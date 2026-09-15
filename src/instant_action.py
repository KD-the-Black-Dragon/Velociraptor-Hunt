"""Instant action (Ctrl+B): two-phase kind + match-card pick, then solo practice match."""

from __future__ import annotations

import string
from enum import Enum, auto

import attrs
import tcod.console
import tcod.event
from tcod.event import KeySym, Modifier

from src.career import CareerState, new_career
from src.downtime_hub import MatchCard
from src.input_handlers import MODAL_ADVANCE_KEYS
from src.career import CAMPAIGN_STYLE_SOLO
from src.match_cards import CardDef, is_solo_eligible_card, load_match_cards_config
from src.match_session import MatchSession, start_match
from src import messages as msg
from src.text import cp437_safe

INSTANT_NAME = "Sparrer"
CARD_ID_MAX_LENGTH = 48
# Instant Action follows Solo Duels focus: 1v1 cards only
INSTANT_SOLO_ONLY = True

_PRINTABLE = frozenset(ch for ch in string.printable if ch not in "\t\n\r\x0b\x0c")
_ID_CHARS = frozenset(string.ascii_letters + string.digits + "_")

_EXCLUDED = frozenset({
    KeySym.RETURN,
    KeySym.KP_ENTER,
    KeySym.ESCAPE,
    KeySym.BACKSPACE,
    KeySym.TAB,
    KeySym.DELETE,
})


class InstantStep(Enum):
    KIND = auto()
    CARD = auto()


class InstantActionResult(Enum):
    NONE = auto()
    CANCEL_TO_MENU = auto()
    BACK_TO_KIND = auto()
    START_MATCH = auto()  # selected_card set


@attrs.define
class InstantActionState:
    """Ctrl+B flow: pick green/red, then type a match card id."""

    step: InstantStep = InstantStep.KIND
    kind: str = ""  # green | red once chosen
    buffer: str = ""
    error_message: str = ""
    selected_card: MatchCard | None = None

    def reset(self) -> None:
        self.step = InstantStep.KIND
        self.kind = ""
        self.buffer = ""
        self.error_message = ""
        self.selected_card = None

    def append(self, char: str) -> None:
        if len(self.buffer) >= CARD_ID_MAX_LENGTH:
            return
        self.buffer += char

    def backspace(self) -> None:
        if self.buffer:
            self.buffer = self.buffer[:-1]
        self.error_message = ""


def cards_for_kind(kind: str, *, solo_only: bool = INSTANT_SOLO_ONLY) -> tuple[CardDef, ...]:
    """Match cards of the given kind (round filters ignored). Solo focus: 1v1 only."""
    cfg = load_match_cards_config()
    k = kind if kind in ("green", "red") else "red"
    out: list[CardDef] = []
    for c in cfg.cards:
        if c.kind != k:
            continue
        if solo_only and not is_solo_eligible_card(c):
            continue
        out.append(c)
    return tuple(out)


def filter_cards(
    kind: str,
    buffer: str,
    *,
    solo_only: bool = INSTANT_SOLO_ONLY,
) -> tuple[CardDef, ...]:
    """Dynamic filter: empty buffer → all of kind; else id/title substring match."""
    pool = cards_for_kind(kind, solo_only=solo_only)
    q = buffer.strip().lower()
    if not q:
        return pool
    out: list[CardDef] = []
    for c in pool:
        if q in c.card_id.lower() or q in c.title.lower():
            out.append(c)
    return tuple(out)


def resolve_card_id(
    kind: str,
    raw: str,
    *,
    solo_only: bool = INSTANT_SOLO_ONLY,
) -> tuple[MatchCard | None, str]:
    """Return (MatchCard, error). Card kind forced to Phase A kind."""
    card_id = raw.strip()
    if not card_id:
        return None, msg.instant_enter_card_id()
    cfg = load_match_cards_config()
    d = cfg.by_id.get(card_id)
    if d is None:
        return None, msg.instant_unknown_card_id()
    if d.kind != kind:
        return None, msg.instant_wrong_kind_card(kind)
    if solo_only and not is_solo_eligible_card(d):
        return None, msg.instant_not_solo_card()
    card = MatchCard(
        card_id=d.card_id,
        title=d.title,
        kind=kind,
        payout_mult=0.0,
        max_allies=0,
        enemies=d.enemies,
    )
    return card, ""


def _char_from_keydown(event: tcod.event.KeyDown) -> str | None:
    sym = event.sym
    if sym in _EXCLUDED:
        return None
    if KeySym.A <= sym <= KeySym.Z:
        ch = chr(sym)
        if event.mod & Modifier.SHIFT:
            return ch.upper()
        return ch.lower()
    if KeySym.N0 <= sym <= KeySym.N9:
        return chr(sym)
    if sym == KeySym.UNDERSCORE or (sym == KeySym.MINUS and event.mod & Modifier.SHIFT):
        return "_"
    if 32 <= sym <= 126:
        ch = chr(sym)
        if ch in _ID_CHARS:
            return ch
    return None


def handle_instant_action_event(
    state: InstantActionState,
    event: tcod.event.Event,
) -> InstantActionResult:
    if not isinstance(event, tcod.event.KeyDown):
        return InstantActionResult.NONE
    sym = event.sym

    if state.step is InstantStep.KIND:
        if sym == KeySym.ESCAPE:
            return InstantActionResult.CANCEL_TO_MENU
        if sym in (KeySym.N1, KeySym.KP_1):
            state.kind = "green"
            state.step = InstantStep.CARD
            state.buffer = ""
            state.error_message = ""
            return InstantActionResult.NONE
        if sym in (KeySym.N2, KeySym.KP_2):
            state.kind = "red"
            state.step = InstantStep.CARD
            state.buffer = ""
            state.error_message = ""
            return InstantActionResult.NONE
        return InstantActionResult.NONE

    # CARD step
    if sym == KeySym.ESCAPE:
        state.step = InstantStep.KIND
        state.kind = ""
        state.buffer = ""
        state.error_message = ""
        state.selected_card = None
        return InstantActionResult.BACK_TO_KIND
    if sym == KeySym.BACKSPACE:
        state.backspace()
        return InstantActionResult.NONE
    if sym in MODAL_ADVANCE_KEYS:
        card, err = resolve_card_id(state.kind, state.buffer)
        if err:
            state.error_message = err
            return InstantActionResult.NONE
        state.selected_card = card
        state.error_message = ""
        return InstantActionResult.START_MATCH
    ch = _char_from_keydown(event)
    if ch is not None:
        state.append(ch)
        state.error_message = ""
    return InstantActionResult.NONE


def render_instant_action(console: tcod.console.Console, state: InstantActionState) -> None:
    """Fixed-width fallback render for instant action screens."""
    console.clear()
    if state.step is InstantStep.KIND:
        console.print(2, 1, "Instant Action", fg=(220, 220, 240))
        console.print(2, 3, "Choose match rules:", fg=(200, 200, 200))
        console.print(2, 5, "1 - Green  (mercy / no permanent digest)", fg=(120, 220, 140))
        console.print(2, 6, "2 - Red    (full stakes)", fg=(240, 120, 100))
        console.print(
            2,
            console.height - 1,
            "1/2: choose  |  Esc: main menu",
            fg=(140, 140, 140),
        )
        return

    kind_label = "GREEN" if state.kind == "green" else "RED"
    kind_fg = (120, 220, 140) if state.kind == "green" else (240, 120, 100)
    console.print(2, 1, f"Instant Action — {kind_label}", fg=kind_fg)
    console.print(2, 3, "Enter match card id:", fg=(200, 200, 200))
    console.print(2, 4, f"> {cp437_safe(state.buffer)}_", fg=(255, 255, 200))
    if state.error_message:
        console.print(2, 5, cp437_safe(state.error_message)[: console.width - 4], fg=(240, 100, 100))

    filtered = filter_cards(state.kind, state.buffer)
    y0 = 7
    console.print(2, y0 - 1, "Valid sets (filtered):", fg=(160, 160, 180))
    max_y = console.height - 2
    col_w = max(20, console.width // 2)
    for i, card in enumerate(filtered):
        col = i // max(1, max_y - y0)
        row = i % max(1, max_y - y0)
        if col > 1:
            break
        x = 2 + col * col_w
        y = y0 + row
        if y >= max_y:
            break
        line = f"{card.card_id} — {card.title}"
        console.print(x, y, cp437_safe(line)[: col_w - 2], fg=(120, 120, 130))

    console.print(
        2,
        console.height - 1,
        "Type id  |  Enter: start  |  Esc: back to Green/Red",
        fg=(140, 140, 140),
    )


def make_instant_career(*, difficulty_id: str = "normal") -> CareerState:
    """Ephemeral solo career: no allies, starter gate done, static defaults."""
    career = new_career(
        player_name=INSTANT_NAME,
        difficulty_id=difficulty_id,
        campaign_style=CAMPAIGN_STYLE_SOLO,
    )
    career.gold = 0
    career.renown = 0
    return career


def start_instant_match(
    card: MatchCard,
    *,
    difficulty_id: str = "normal",
    seed: int | None = None,
) -> MatchSession:
    """Solo sand-pit match; no allies; instant_action flag set."""
    career = make_instant_career(difficulty_id=difficulty_id)
    # Force solo even if card JSON allows allies
    solo = MatchCard(
        card_id=card.card_id,
        title=card.title,
        kind=card.kind,
        payout_mult=0.0,
        max_allies=0,
        enemies=card.enemies,
    )
    session = start_match(career, solo, seed=seed)
    session.instant_action = True
    # Soften recap footers after finish methods run — patched in finish via flag
    return session
