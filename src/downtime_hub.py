"""Downtime hub between arena matches."""

from __future__ import annotations

import random
from enum import Enum, auto

import attrs
import tcod.console
import tcod.event
from tcod.event import KeySym

from src.career import CareerState
from src.injuries import format_injury_list, heal_one_step, injuries_from_dicts, load_injury_config
from src.patrons import format_patrons_roster_line
from src.roster import (
    AllyRecord,
    count_deployed,
    generate_market,
    load_roster_tuning,
    try_hire,
)
from src.text import cp437_safe
from src.ui.help_overlay import (
    HELP_BODY_FG,
    HELP_FOOTER_FG,
    HELP_SECTION_FG,
    HELP_TITLE_FG,
    HelpTextLine,
)

HUB_INTRO = "You have some downtime before your next match. Here are ways you can spend it."

HUB_ROOT_OPTIONS_COMPANY: tuple[str, ...] = (
    "Shop (buy equipment)",
    "Hire personnel",
    "Manage equipment",
    "Training",
    "Healing (injuries)",
    "Assign team for next match",
    "Select next match",
    "Return to main menu",
)

# Solo Duels: no hire / assign (company systems on ice)
HUB_ROOT_OPTIONS_SOLO: tuple[str, ...] = (
    "Shop (buy equipment)",
    "Manage equipment",
    "Training",
    "Healing (injuries)",
    "Select next match",
    "Return to main menu",
)

# Back-compat alias (company layout)
HUB_ROOT_OPTIONS: tuple[str, ...] = HUB_ROOT_OPTIONS_COMPANY


def hub_root_options(career: CareerState) -> tuple[str, ...]:
    if career.is_solo():
        return HUB_ROOT_OPTIONS_SOLO
    return HUB_ROOT_OPTIONS_COMPANY

_NAV_UP = frozenset({KeySym.UP, KeySym.KP_8})
_NAV_DOWN = frozenset({KeySym.DOWN, KeySym.KP_2})
_CONFIRM = frozenset({KeySym.RETURN, KeySym.KP_ENTER})
_BACK = frozenset({KeySym.ESCAPE})

TITLE_FG = HELP_TITLE_FG
BODY_FG = HELP_BODY_FG
DIM_FG = HELP_FOOTER_FG
SECTION_FG = HELP_SECTION_FG
GREEN_FG = (120, 220, 140)
RED_FG = (240, 120, 100)
HIGHLIGHT_FG = (255, 255, 160)

FOOTER_ROOT = "Up/Down: move  |  Enter: choose  |  Esc/Ctrl+Q: leave to menu"
FOOTER_STUB = "Enter/Esc: back"
FOOTER_MATCH = "Enter: select  |  Esc: back"
FOOTER_HIRE = "Enter: hire  |  R: refresh market  |  Esc: back"
FOOTER_STARTER = "Enter: take free ally  |  need 2 to continue"
FOOTER_ASSIGN = "Enter: toggle deploy  |  Esc: back"
FOOTER_HEAL = "Enter: heal one step  |  Esc: back"


class HubView(Enum):
    ROOT = auto()
    STUB_NOTICE = auto()
    MATCH_SELECT = auto()
    HIRE_MARKET = auto()
    STARTER_PICK = auto()
    ASSIGN_TEAM = auto()
    HEAL = auto()


class HubAction(Enum):
    NONE = auto()
    REQUEST_LEAVE_MENU = auto()
    CAREER_DIRTY = auto()
    START_MATCH = auto()


@attrs.define
class MatchCard:
    card_id: str
    title: str
    kind: str  # "green" | "red"
    payout_mult: float
    max_allies: int = 2  # deploy cap override for this card
    # (entity_id, count) spawns; empty → resolve from match_cards catalog by id
    enemies: tuple[tuple[str, int], ...] = ()

    @property
    def kind_label(self) -> str:
        return "GREEN" if self.kind == "green" else "RED"


def stub_cards_for_round(
    round_index: int = 1,
    *,
    difficulty_id: str = "normal",
    seed: int | None = None,
    solo_only: bool = False,
) -> tuple[MatchCard, ...]:
    """Pick up to 3 cards for this round (compat name; data-driven)."""
    from src.match_cards import pick_match_offers

    rng = random.Random(seed if seed is not None else round_index * 9973)
    return pick_match_offers(
        round_index,
        difficulty_id=difficulty_id,
        rng=rng,
        solo_only=solo_only,
    )


@attrs.define
class DowntimeHubState:
    view: HubView = HubView.ROOT
    highlight: int = 0
    match_highlight: int = 0
    list_highlight: int = 0
    notice_lines: tuple[str, ...] = ()
    cards: tuple[MatchCard, ...] = attrs.field(factory=lambda: stub_cards_for_round(1))
    pending_match_card: MatchCard | None = None
    market_offers: list[AllyRecord] = attrs.field(factory=list)
    market_seed: int = 0
    free_market: bool = False  # starter picks cost 0
    # HEAL view: list of (owner_key, region, label, cost)
    # owner_key = "pc" or ally_id
    heal_entries: list[tuple[str, str, str, int]] = attrs.field(factory=list)

    def reset_to_root(self) -> None:
        self.view = HubView.ROOT
        self.notice_lines = ()
        self.pending_match_card = None
        self.list_highlight = 0

    def open_stub(self, *lines: str) -> None:
        self.view = HubView.STUB_NOTICE
        self.notice_lines = lines

    def open_match_select(self, career: CareerState) -> None:
        self.view = HubView.MATCH_SELECT
        self.match_highlight = 0
        # Seed from career state so reopening mid-round is stable until round advances
        seed = (
            career.round_index * 10007
            + career.renown * 13
            + career.gold
            + len(career.roster)
        )
        self.cards = stub_cards_for_round(
            career.round_index,
            difficulty_id=career.difficulty_id,
            seed=seed,
            solo_only=career.is_solo(),
        )

    def open_hire(
        self,
        career: CareerState,
        *,
        free: bool = False,
        starter: bool = False,
    ) -> None:
        rng = random.Random(self.market_seed + career.round_index + len(career.roster))
        self.free_market = free
        self.market_offers = generate_market(rng, free=free)
        self.list_highlight = 0
        self.view = HubView.STARTER_PICK if starter else HubView.HIRE_MARKET

    def open_assign(self) -> None:
        self.view = HubView.ASSIGN_TEAM
        self.list_highlight = 0

    def open_heal(self, career: CareerState) -> None:
        cfg = load_injury_config()
        entries: list[tuple[str, str, str, int]] = []
        for inj in career.get_player_injuries():
            cost = int(cfg.heal_gold_per_step.get(inj.severity, 50))
            entries.append(("pc", inj.region, f"You — {inj.label()}", cost))
        for ally in career.allies():
            for inj in injuries_from_dicts(ally.injuries):
                cost = int(cfg.heal_gold_per_step.get(inj.severity, 50))
                entries.append(
                    (ally.ally_id, inj.region, f"{ally.name} — {inj.label()}", cost)
                )
        self.heal_entries = entries
        self.list_highlight = 0
        self.view = HubView.HEAL

    def ensure_starter_gate(self, career: CareerState) -> None:
        """If starter picks incomplete, force STARTER_PICK view (company only)."""
        if career.is_solo():
            career.starter_picks_done = True
            career.max_deployed_allies = 0
            return
        if career.starter_picks_done:
            return
        tuning = load_roster_tuning()
        if len(career.roster) >= tuning.free_starter_picks:
            career.starter_picks_done = True
            return
        if self.view not in (HubView.STARTER_PICK, HubView.STUB_NOTICE):
            self.open_hire(career, free=True, starter=True)


def hub_footer_text(hub: DowntimeHubState) -> str:
    if hub.view is HubView.STUB_NOTICE:
        return FOOTER_STUB
    if hub.view is HubView.MATCH_SELECT:
        return FOOTER_MATCH
    if hub.view is HubView.HIRE_MARKET:
        return FOOTER_HIRE
    if hub.view is HubView.STARTER_PICK:
        return FOOTER_STARTER
    if hub.view is HubView.ASSIGN_TEAM:
        return FOOTER_ASSIGN
    if hub.view is HubView.HEAL:
        return FOOTER_HEAL
    return FOOTER_ROOT


def downtime_display_lines(
    career: CareerState,
    hub: DowntimeHubState,
) -> tuple[HelpTextLine, ...]:
    tuning = load_roster_tuning()
    lines: list[HelpTextLine] = [
        HelpTextLine("DOWNTIME", TITLE_FG),
        HelpTextLine(
            f"{career.player_name}  |  Round {career.round_index}  |  "
            f"Gold: {career.gold}  |  Renown: {career.renown}"
            + (
                f"  |  BG: {career.background_id}"
                if career.background_id
                else ""
            )
            + f"  |  Diff: {career.difficulty_id}",
            BODY_FG,
        ),
    ]
    if career.is_solo():
        lines.append(
            HelpTextLine("Campaign: Solo Duels  |  1-on-1 only", SECTION_FG)
        )
    else:
        lines.append(
            HelpTextLine(
                f"Roster: {len(career.roster)}/{tuning.max_allies}  |  "
                f"Deployed: {count_deployed(career.allies())}/{career.max_deployed_allies}",
                DIM_FG,
            )
        )
    patrons_line = format_patrons_roster_line()
    if patrons_line:
        lines.append(HelpTextLine(patrons_line, DIM_FG))
    if career.last_patron_result:
        lines.append(HelpTextLine(career.last_patron_result, SECTION_FG))
    lines.append(HelpTextLine("", BODY_FG))

    if hub.view is HubView.STUB_NOTICE:
        for line in hub.notice_lines:
            lines.append(HelpTextLine(line, BODY_FG))
        return tuple(lines)

    if hub.view is HubView.MATCH_SELECT:
        lines.append(HelpTextLine("Select next match", SECTION_FG))
        lines.append(
            HelpTextLine(
                "RED = digestion risk, better pay.  GREEN = safer, lower pay.",
                DIM_FG,
            )
        )
        lines.append(
            HelpTextLine(
                "A patron will offer a gold bonus objective when the match starts.",
                DIM_FG,
            )
        )
        lines.append(HelpTextLine("", BODY_FG))
        for i, card in enumerate(hub.cards):
            marker = ">" if i == hub.match_highlight else " "
            kind_fg = GREEN_FG if card.kind == "green" else RED_FG
            row_fg = HIGHLIGHT_FG if i == hub.match_highlight else BODY_FG
            lines.append(
                HelpTextLine(
                    f"{marker} [{card.kind_label}] {card.title}  (x{card.payout_mult:.2f})",
                    kind_fg if i != hub.match_highlight else row_fg,
                )
            )
        return tuple(lines)

    if hub.view in (HubView.HIRE_MARKET, HubView.STARTER_PICK):
        title = "FREE STARTER ALLIES" if hub.view is HubView.STARTER_PICK else "HIRE MARKET"
        lines.append(HelpTextLine(title, SECTION_FG))
        if hub.view is HubView.STARTER_PICK:
            need = tuning.free_starter_picks - len(career.roster)
            lines.append(
                HelpTextLine(
                    f"Pick {need} more free fighter(s) to begin your career.",
                    DIM_FG,
                )
            )
        lines.append(HelpTextLine("", BODY_FG))
        if not hub.market_offers:
            lines.append(HelpTextLine("(No offers — press R to refresh.)", DIM_FG))
        for i, offer in enumerate(hub.market_offers):
            marker = ">" if i == hub.list_highlight else " "
            fg = HIGHLIGHT_FG if i == hub.list_highlight else BODY_FG
            price = "FREE" if hub.free_market else f"{offer.hire_cost}g"
            lines.append(
                HelpTextLine(
                    f"{marker} {offer.name} [{offer.tier}] {offer.species_id}  {price}",
                    fg,
                )
            )
            if i == hub.list_highlight:
                lines.append(
                    HelpTextLine(
                        f"    HP {offer.max_hp}  Acc {offer.accuracy:.1f}  "
                        f"Dmg {offer.min_damage}-{offer.max_damage}",
                        DIM_FG,
                    )
                )
                lines.append(HelpTextLine(f"    {offer.backstory}", DIM_FG))
        return tuple(lines)

    if hub.view is HubView.ASSIGN_TEAM:
        lines.append(HelpTextLine("ASSIGN TEAM", SECTION_FG))
        lines.append(
            HelpTextLine(
                f"PC always enters. Deploy up to {career.max_deployed_allies} allies "
                f"(Enter toggles).",
                DIM_FG,
            )
        )
        lines.append(HelpTextLine("", BODY_FG))
        allies = career.allies()
        if not allies:
            lines.append(HelpTextLine("(No allies hired yet.)", DIM_FG))
        for i, ally in enumerate(allies):
            marker = ">" if i == hub.list_highlight else " "
            flag = "[IN]" if ally.deployed else "[--]"
            fg = HIGHLIGHT_FG if i == hub.list_highlight else BODY_FG
            lines.append(
                HelpTextLine(
                    f"{marker} {flag} {ally.name} [{ally.tier}] HP {ally.max_hp}",
                    fg,
                )
            )
            if ally.injuries:
                lines.append(
                    HelpTextLine(
                        "    " + "; ".join(
                            format_injury_list(injuries_from_dicts(ally.injuries))
                        ),
                        DIM_FG,
                    )
                )
        return tuple(lines)

    if hub.view is HubView.HEAL:
        lines.append(HelpTextLine("HEALING", SECTION_FG))
        lines.append(
            HelpTextLine(
                "Pay gold to reduce one severity step (Major→Moderate→Minor→clear).",
                DIM_FG,
            )
        )
        lines.append(
            HelpTextLine("Expensive — often better to play around injuries.", DIM_FG)
        )
        lines.append(HelpTextLine("", BODY_FG))
        if not hub.heal_entries:
            lines.append(HelpTextLine("(No injuries.)", DIM_FG))
        for i, (_owner, _region, label, cost) in enumerate(hub.heal_entries):
            marker = ">" if i == hub.list_highlight else " "
            fg = HIGHLIGHT_FG if i == hub.list_highlight else BODY_FG
            lines.append(HelpTextLine(f"{marker} {label}  —  {cost}g", fg))
        return tuple(lines)

    # ROOT
    pc_inj = career.get_player_injuries()
    if pc_inj:
        lines.append(
            HelpTextLine(
                "You: " + "; ".join(format_injury_list(pc_inj)),
                (255, 200, 120),
            )
        )
        lines.append(HelpTextLine("", BODY_FG))
    if not career.is_solo() and not career.starter_picks_done:
        lines.append(
            HelpTextLine(
                "Complete free starter ally picks before other hub actions.",
                RED_FG,
            )
        )
        lines.append(HelpTextLine("", BODY_FG))
    lines.append(HelpTextLine(HUB_INTRO, DIM_FG))
    lines.append(HelpTextLine("", BODY_FG))
    options = hub_root_options(career)
    # Clamp highlight if switching styles mid-session (shouldn't happen often)
    if hub.highlight >= len(options):
        hub.highlight = 0
    for i, option in enumerate(options):
        marker = ">" if i == hub.highlight else " "
        fg = HIGHLIGHT_FG if i == hub.highlight else BODY_FG
        lines.append(HelpTextLine(f"{marker} {option}", fg))
    return tuple(lines)


def handle_downtime_event(
    hub: DowntimeHubState,
    career: CareerState,
    event: tcod.event.Event,
) -> HubAction:
    if not isinstance(event, tcod.event.KeyDown):
        return HubAction.NONE
    sym = event.sym

    hub.ensure_starter_gate(career)

    if hub.view is HubView.STUB_NOTICE:
        if sym in _CONFIRM or sym in _BACK:
            if not career.starter_picks_done:
                hub.open_hire(career, free=True, starter=True)
            else:
                hub.reset_to_root()
        return HubAction.NONE

    if hub.view is HubView.MATCH_SELECT:
        n = len(hub.cards)
        if n <= 0:
            hub.reset_to_root()
            return HubAction.NONE
        if sym in _NAV_UP:
            hub.match_highlight = (hub.match_highlight - 1) % n
        elif sym in _NAV_DOWN:
            hub.match_highlight = (hub.match_highlight + 1) % n
        elif sym in _BACK:
            hub.reset_to_root()
        elif sym in _CONFIRM:
            hub.pending_match_card = hub.cards[hub.match_highlight]
            return HubAction.START_MATCH
        return HubAction.NONE

    if hub.view in (HubView.HIRE_MARKET, HubView.STARTER_PICK):
        return _handle_hire(hub, career, sym)

    if hub.view is HubView.ASSIGN_TEAM:
        return _handle_assign(hub, career, sym)

    if hub.view is HubView.HEAL:
        return _handle_heal(hub, career, sym)

    # ROOT — company: block most actions until starter picks done
    if not career.is_solo() and not career.starter_picks_done:
        if sym in _CONFIRM or sym in _NAV_UP or sym in _NAV_DOWN:
            hub.open_hire(career, free=True, starter=True)
            return HubAction.NONE
        if sym in _BACK:
            return HubAction.REQUEST_LEAVE_MENU
        return HubAction.NONE

    options = hub_root_options(career)
    count = len(options)
    if hub.highlight >= count:
        hub.highlight = 0
    if sym in _NAV_UP:
        hub.highlight = (hub.highlight - 1) % count
    elif sym in _NAV_DOWN:
        hub.highlight = (hub.highlight + 1) % count
    elif sym in _BACK:
        return HubAction.REQUEST_LEAVE_MENU
    elif sym in _CONFIRM:
        return _activate_root_option(hub, career)
    return HubAction.NONE


def _handle_hire(
    hub: DowntimeHubState,
    career: CareerState,
    sym: KeySym,
) -> HubAction:
    offers = hub.market_offers
    n = len(offers)
    if sym == KeySym.R and hub.view is HubView.HIRE_MARKET:
        hub.market_seed += 1
        hub.open_hire(career, free=False, starter=False)
        return HubAction.NONE
    if n > 0 and sym in _NAV_UP:
        hub.list_highlight = (hub.list_highlight - 1) % n
        return HubAction.NONE
    if n > 0 and sym in _NAV_DOWN:
        hub.list_highlight = (hub.list_highlight + 1) % n
        return HubAction.NONE
    if sym in _BACK:
        if hub.view is HubView.STARTER_PICK and not career.starter_picks_done:
            return HubAction.REQUEST_LEAVE_MENU
        hub.reset_to_root()
        return HubAction.NONE
    if sym in _CONFIRM and n > 0:
        offer = offers[hub.list_highlight]
        free = hub.free_market or hub.view is HubView.STARTER_PICK
        allies = career.allies()
        new_roster, new_gold, err = try_hire(
            allies,
            offer,
            gold=career.gold,
            free=free,
        )
        if err:
            hub.open_stub(err, "", "Enter/Esc: back")
            # After stub, re-open hire — handled by stub return path for starter
            return HubAction.NONE
        career.set_allies(new_roster)
        career.gold = new_gold
        # Remove hired offer from market list
        del hub.market_offers[hub.list_highlight]
        if hub.list_highlight >= len(hub.market_offers) and hub.market_offers:
            hub.list_highlight = len(hub.market_offers) - 1
        tuning = load_roster_tuning()
        if hub.view is HubView.STARTER_PICK:
            if len(career.roster) >= tuning.free_starter_picks:
                career.starter_picks_done = True
                # Auto-deploy first two
                allies2 = career.allies()
                for i, a in enumerate(allies2):
                    a.deployed = i < career.max_deployed_allies
                career.set_allies(allies2)
                hub.open_stub(
                    "Starter team ready!",
                    "",
                    *[f"- {a.name} [{a.tier}]" for a in career.allies()],
                    "",
                    "Enter: continue to downtime hub.",
                )
                return HubAction.CAREER_DIRTY
            hub.open_hire(career, free=True, starter=True)
            return HubAction.CAREER_DIRTY
        hub.open_stub(
            f"Hired {offer.name} for {0 if free else offer.hire_cost} gold.",
            offer.backstory,
            "",
            "Enter/Esc: back",
        )
        return HubAction.CAREER_DIRTY
    return HubAction.NONE


def _handle_assign(
    hub: DowntimeHubState,
    career: CareerState,
    sym: KeySym,
) -> HubAction:
    allies = career.allies()
    n = len(allies)
    if sym in _BACK:
        hub.reset_to_root()
        return HubAction.NONE
    if n <= 0:
        if sym in _CONFIRM:
            hub.reset_to_root()
        return HubAction.NONE
    if sym in _NAV_UP:
        hub.list_highlight = (hub.list_highlight - 1) % n
        return HubAction.NONE
    if sym in _NAV_DOWN:
        hub.list_highlight = (hub.list_highlight + 1) % n
        return HubAction.NONE
    if sym in _CONFIRM:
        ally = allies[hub.list_highlight]
        if ally.deployed:
            ally.deployed = False
        else:
            if count_deployed(allies) >= career.max_deployed_allies:
                hub.open_stub(
                    f"Already deploying {career.max_deployed_allies} allies.",
                    "Bench someone first.",
                    "",
                    "Enter/Esc: back",
                )
                return HubAction.NONE
            ally.deployed = True
        career.set_allies(allies)
        return HubAction.CAREER_DIRTY
    return HubAction.NONE


def _activate_root_option(hub: DowntimeHubState, career: CareerState) -> HubAction:
    options = hub_root_options(career)
    if hub.highlight < 0 or hub.highlight >= len(options):
        return HubAction.NONE
    label = options[hub.highlight]
    if label.startswith("Shop"):
        hub.open_stub(
            "Shop",
            "",
            "Buy weapons, shields, and armor between matches.",
            "(Stub — stock and prices arrive later.)",
            f"You have {career.gold} gold.",
        )
    elif label.startswith("Hire"):
        if career.is_solo():
            return HubAction.NONE
        hub.open_hire(career, free=False, starter=False)
    elif label.startswith("Manage"):
        manage_blurb = (
            "Outfit yourself for the next duel."
            if career.is_solo()
            else "Outfit yourself and your employees from the shared armory."
        )
        hub.open_stub(
            "Manage equipment",
            "",
            manage_blurb,
            "(Stub — loadout UI arrives later.)",
        )
    elif label.startswith("Training"):
        hub.open_stub(
            "Training",
            "",
            "Buy skill +1s and learn abilities.",
            "(Stub — trainers arrive later.)",
        )
    elif label.startswith("Healing"):
        hub.open_heal(career)
    elif label.startswith("Assign"):
        if career.is_solo():
            return HubAction.NONE
        hub.open_assign()
    elif label.startswith("Select"):
        hub.open_match_select(career)
    elif label.startswith("Return"):
        return HubAction.REQUEST_LEAVE_MENU
    return HubAction.NONE


def _handle_heal(
    hub: DowntimeHubState,
    career: CareerState,
    sym: KeySym,
) -> HubAction:
    if sym in _BACK:
        hub.reset_to_root()
        return HubAction.NONE
    n = len(hub.heal_entries)
    if n <= 0:
        if sym in _CONFIRM:
            hub.reset_to_root()
        return HubAction.NONE
    if sym in _NAV_UP:
        hub.list_highlight = (hub.list_highlight - 1) % n
        return HubAction.NONE
    if sym in _NAV_DOWN:
        hub.list_highlight = (hub.list_highlight + 1) % n
        return HubAction.NONE
    if sym not in _CONFIRM:
        return HubAction.NONE
    owner, region, label, cost = hub.heal_entries[hub.list_highlight]
    if career.gold < cost:
        hub.open_stub(
            f"Need {cost} gold (have {career.gold}).",
            "",
            "Enter/Esc: back",
        )
        return HubAction.NONE
    if owner == "pc":
        new_list, paid, msg = heal_one_step(career.get_player_injuries(), region)
        career.set_player_injuries(new_list)
    else:
        allies = career.allies()
        msg = None
        paid = cost
        for a in allies:
            if a.ally_id == owner:
                new_list, paid, msg = heal_one_step(
                    injuries_from_dicts(a.injuries),
                    region,
                )
                from src.injuries import injuries_to_dicts

                a.injuries = injuries_to_dicts(new_list)
                break
        career.set_allies(allies)
    career.gold -= paid
    hub.open_heal(career)
    if msg:
        # Brief feedback via reopening list; also stub optional
        pass
    return HubAction.CAREER_DIRTY


def render_downtime_hub(
    console: tcod.console.Console,
    career: CareerState,
    hub: DowntimeHubState,
) -> None:
    console.clear(bg=(16, 16, 24))
    y = 1
    for entry in downtime_display_lines(career, hub):
        if y >= console.height - 2:
            break
        if entry.text:
            console.print(
                2,
                y,
                cp437_safe(entry.text[: max(1, console.width - 4)]),
                fg=entry.fg,
            )
        y += 1
    footer = hub_footer_text(hub)
    console.print(2, console.height - 2, cp437_safe(footer[: console.width - 4]), fg=DIM_FG)
