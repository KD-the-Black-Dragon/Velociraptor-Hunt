"""Gladiavore match: curated arena + AUT combat + AP/balance/abilities skeleton."""

from __future__ import annotations

import random
from enum import Enum, auto

import attrs
import tcod.console
import tcod.event
from tcod.ecs import Entity, Registry
from tcod.event import KeySym

from src.aut import AutCosts, AutScheduler, load_aut_costs
from src.career import CareerState
from src.components import (
    AI,
    BlocksMovement,
    DisplayName,
    Fighter,
    Player,
    Position,
    Renderable,
)
from src.constants import (
    PLAYER_AC,
    PLAYER_ACCURACY,
    PLAYER_EVADE,
    PLAYER_MAX_DAMAGE,
    PLAYER_MAX_HP,
    PLAYER_MIN_DAMAGE,
)
from src.data.entity_loader import load_entity_registry
from src.downtime_hub import MatchCard
from src.match_cards import (
    compute_loss_payout,
    compute_surrender_payout,
    compute_win_payout,
    enemies_for_card,
    load_match_cards_config,
)
from src.patrons import (
    ActivePatronObjective,
    MatchPatronStats,
    assign_patron_objective,
    evaluate_objective,
)
from src.match_crowd import (
    CrowdConfig,
    CrowdState,
    load_crowd_config,
    settle_crowd_gold,
)
from src.difficulties import DifficultyDef, resolve_difficulty
from src.input_handlers import DIRECTION_KEYS
from src.injuries import (
    format_injury_list,
    injuries_from_dicts,
    injuries_to_dicts,
    try_apply_from_hit,
)
from src.match_combat import (
    CombatantState,
    MatchAbilityDef,
    MatchCombatConfig,
    ability_by_letter,
    actual_fighter,
    apply_ready_balance,
    awareness_openness,
    balance_stat_deltas,
    choose_bump_profile,
    format_ap_meter,
    format_balance_effect_line,
    format_balance_meter,
    format_recovery_meter,
    load_match_combat_config,
    step_aut_multiplier,
)
from src.match_ai_config import MatchAiConfig, load_match_ai_config
from src.match_ai import (
    maybe_start_morale_shock,
    momentum_evade_mult,
    roll_attrs,
    score_ally_intents,
    score_enemy_intents,
    should_forget_order,
)
from src.weapon_measure import (
    all_footwork_offsets,
    attack_delay,
    default_weapon_for_entity,
    effective_band,
    is_footwork_offset,
    measure_mult,
)
from src.match_recovery import RecoveryConfig, load_recovery_config
from src.match_vore import (
    GrappleState,
    VoreConfig,
    VorePhase,
    break_away_chance,
    effective_digest_strikes_to_end,
    grab_chance,
    load_vore_config,
    pick_flaunt,
    swallow_narrative_line,
    swallow_struggle_escape_chance,
)
from src.match_map import (
    SAND_PIT_HEIGHT,
    build_sand_pit_map,
    sand_pit_enemy_spawns,
    sand_pit_player_spawn,
)
from src.match_tactics import (
    PendingReaction,
    ReactionKind,
    chebyshev,
    dodge_fatigue_cost,
    flank_accuracy_multiplier,
    push_direction,
    resolve_pushback,
)
from src.message_log import MessageCategory, MessageLog
from src import messages as msg
from src.roster import AllyRecord, deployed_allies, load_roster_tuning, remove_ally_digest
from src.match_spawn import spawn_match_entity
from src.match_combat_resolve import resolve_attack
from src.match_movement import can_entity_enter_tile
from src.match_naming import entity_log_name
from src.match_hud_layout import MATCH_LOG_MAX_LINES
from src.match_render import (
    apply_grapple_tile_highlights,
    draw_match_entities,
    paint_tile_bg,
    render_map,
)
from src.text import cp437_safe

_WAIT_KEYS = frozenset({KeySym.PERIOD, KeySym.KP_5})  # keep watch (. and numpad 5 same)
_SPACE_WAIT = frozenset({KeySym.SPACE})  # also keep watch
_CONFIRM = frozenset({KeySym.RETURN, KeySym.KP_ENTER})
_ABILITY_MENU_KEYS = frozenset({KeySym.A})
_TALK_KEYS = frozenset({KeySym.T})
_HELP_KEYS = frozenset({KeySym.QUESTION, KeySym.SLASH})  # ? often Shift+/
_ESCAPE = frozenset({KeySym.ESCAPE})
_REACT_DODGE = frozenset({KeySym.N1, KeySym.KP_1})
_REACT_PARRY = frozenset({KeySym.N2, KeySym.KP_2})
_REACT_COUNTER = frozenset({KeySym.N3, KeySym.KP_3})
_REACT_IGNORE = frozenset({KeySym.N4, KeySym.KP_4})
_TALK_ALL = frozenset({KeySym.N0, KeySym.KP_0})
_BRACE_KEYS = frozenset({KeySym.D})
_FOOTWORK_KEYS = frozenset({KeySym.F})
_REACT_HELP = frozenset({KeySym.N3, KeySym.KP_3})  # swallow modal option 3


class MatchPhase(Enum):
    FIGHT = auto()
    RECAP = auto()


class MatchEndKind(Enum):
    WIN = auto()
    LOSS = auto()
    SURRENDER = auto()  # Green mid-match cry-off
    DIGESTED = auto()  # PC permanently removed — career ends


class AbilityUiMode(Enum):
    CLOSED = auto()
    PICK_LETTER = auto()  # after 'a'
    FULL_LIST = auto()  # after a?


class TalkUiMode(Enum):
    CLOSED = auto()
    PICK_ALLY = auto()
    PICK_ORDER = auto()


_SURRENDER_KEYS = frozenset({KeySym.G})


@attrs.define
class MatchSession:
    """One arena bout driven by AUT (not the dungeon GameEngine)."""

    career: CareerState
    card: MatchCard
    world: Registry
    game_map: object
    player: Entity
    enemies: list[Entity]
    message_log: MessageLog
    rng: random.Random
    scheduler: AutScheduler
    costs: AutCosts
    combat_cfg: MatchCombatConfig
    recovery_cfg: RecoveryConfig
    vore_cfg: VoreConfig
    combatants: dict[object, CombatantState]
    phase: MatchPhase = MatchPhase.FIGHT
    end_kind: MatchEndKind | None = None
    recap_lines: tuple[str, ...] = ()
    gold_delta: int = 0
    renown_delta: int = 0
    awaiting_player: bool = True
    ability_ui: AbilityUiMode = AbilityUiMode.CLOSED
    pending_reaction: PendingReaction | None = None
    dodge_count: int = 0
    recent_dodges: int = 0  # dodges without a player action between
    # Ally support (PR6)
    ally_entities: list[Entity] = attrs.field(factory=list)
    ally_id_by_entity: dict[object, str] = attrs.field(factory=dict)
    ally_order: dict[str, str] = attrs.field(factory=dict)  # ally_id -> attack|help_me|stay_close
    ally_order_issued_at: dict[str, float] = attrs.field(factory=dict)
    talk_ui: TalkUiMode = TalkUiMode.CLOSED
    talk_target_ids: list[str] = attrs.field(factory=list)  # selected for order
    free_talk_ready_at: float = 0.0
    digest_notes: list[str] = attrs.field(factory=list)
    # PR8 grapple / vore
    grapple: GrappleState | None = None
    # PR10 patrons
    patron_objective: ActivePatronObjective | None = None
    patron_stats: MatchPatronStats = attrs.field(factory=MatchPatronStats)
    # PR11+ stubs
    crowd_cfg: CrowdConfig = attrs.field(factory=load_crowd_config)
    crowd: CrowdState = attrs.field(factory=CrowdState)
    difficulty: DifficultyDef = attrs.field(
        factory=lambda: resolve_difficulty("normal")
    )
    # Battle Sport
    ai_cfg: MatchAiConfig = attrs.field(factory=load_match_ai_config)
    footwork_targeting: bool = False
    footwork_cursor: Position | None = None  # absolute map tile while targeting
    # (world_aut, aggressor entity id) — recent aggressive acts on PC
    pc_aggression_log: list[tuple[float, object]] = attrs.field(factory=list)
    # Instant action (Ctrl+B practice) — no career persistence
    instant_action: bool = False

    def living_enemies(self) -> list[Entity]:
        out: list[Entity] = []
        for e in self.enemies:
            fighter = e.components.get(Fighter)
            if fighter is not None and fighter.hp > 0:
                out.append(e)
        return out

    def living_allies(self) -> list[Entity]:
        out: list[Entity] = []
        for e in self.ally_entities:
            fighter = e.components.get(Fighter)
            if fighter is not None and fighter.hp > 0 and Position in e.components:
                out.append(e)
        return out

    def all_actors(self) -> list[object]:
        actors: list[object] = []
        pf = self.player.components.get(Fighter)
        pc = self.combatants.get(self.player)
        # Downed PC still acts (crawl / recover); not removed by 0 HP alone
        if pf is not None and (pf.hp > 0 or (pc is not None and pc.downed)):
            actors.append(self.player)
        actors.extend(self.living_allies())
        actors.extend(self.living_enemies())
        return actors

    def _player_side_incap(self) -> bool:
        """True when PC is downed and no living allies remain."""
        pc = self.combatants.get(self.player)
        pf = self.player.components.get(Fighter)
        pc_out = pf is not None and pf.hp <= 0 and (pc is None or pc.downed)
        return pc_out and not self.living_allies()

    def is_ally(self, entity: Entity) -> bool:
        return entity in self.ally_id_by_entity

    def _in_grapple(self, entity: Entity) -> bool:
        g = self.grapple
        return g is not None and (entity is g.predator or entity is g.prey)

    def _is_obscured_prey(self, entity: Entity) -> bool:
        """True if entity is currently the prey in an active grapple (cinematic cover)."""
        g = self.grapple
        return g is not None and entity is g.prey

    def _attacker_may_hit(self, attacker: Entity, defender: Entity) -> bool:
        """Grappled prey only takes hits from their current predator (not a free pincushion)."""
        g = self.grapple
        if g is None:
            return True
        if defender is g.prey:
            return attacker is g.predator
        return True

    def _clear_pending_reaction(self) -> None:
        self.pending_reaction = None

    def _note_pc_aggression(self, aggressor: Entity) -> None:
        """Record aggressive act against PC (attacks, feints) for Help me! orders."""
        self.pc_aggression_log.append((self.scheduler.world_aut, aggressor))
        # Cap log size
        if len(self.pc_aggression_log) > 40:
            self.pc_aggression_log = self.pc_aggression_log[-40:]

    def _recent_pc_aggressors(self) -> set[object]:
        win = self.ai_cfg.help_aggression_window_aut
        now = self.scheduler.world_aut
        out: set[object] = set()
        for aut, ent in self.pc_aggression_log:
            if now - aut <= win + 1e-9:
                out.add(ent)
        return out

    def _call_for_help(self, *, from_swallow: bool) -> bool:
        """Tag Help me! for all allies. Returns whether the call was heard."""
        heard = True
        if from_swallow:
            heard = self.rng.random() < self.ai_cfg.help_call_heard_chance_swallow
        if not heard:
            self.message_log.add(
                "You call for help — but no one seems to hear.",
                category=MessageCategory.CAUTION,
            )
            return False
        now = self.scheduler.world_aut
        # Current predator counts as aggressor
        if self.grapple is not None and self.grapple.predator is not None:
            self._note_pc_aggression(self.grapple.predator)  # type: ignore[arg-type]
        for e in self.living_allies():
            aid = self.ally_id_by_entity.get(e)
            if aid:
                self.ally_order[aid] = "help_me"
                self.ally_order_issued_at[aid] = now
        self.message_log.add(
            "You shout for help!",
            category=MessageCategory.SPEECH,
        )
        return True

    def _sync_ap(self) -> None:
        t = self.scheduler.world_aut
        rc = self.recovery_cfg
        for ent, state in list(self.combatants.items()):
            prev = state.last_world_aut
            state.clear_expired_statuses(t)
            if (
                state.morale_shock_until_aut < 0
                and state.hp_at_shock_end is not None
            ):
                pass
            # morale check on live HP
            live = ent.components.get(Fighter) if hasattr(ent, "components") else None
            if live is not None and Player not in getattr(ent, "tags", set()):
                maybe_start_morale_shock(
                    state, int(live.hp), t, self.ai_cfg, self.rng
                )
            elapsed = max(0.0, t - prev)
            if state.downed and elapsed > 0:
                state.recovery_bar = min(
                    rc.recovery_bar_full,
                    state.recovery_bar + elapsed * rc.recovery_bar_fill_per_aut,
                )
            state.tick_ap(t)
            if state.debuff_until_aut >= 0 and t >= state.debuff_until_aut:
                state.debuff_until_aut = -1.0
                state.debuff_accuracy_mult = 1.0
                state.debuff_evade_mult = 1.0

    def process_npc_until_player(self) -> None:
        """Run NPC actions until it is the player's turn or the match ends."""
        # Grapple owns PC input — drop any stale reaction modal so scenes don't stack.
        if (
            self.grapple is not None
            and self.grapple.prey is self.player
            and self.pending_reaction is not None
        ):
            self._clear_pending_reaction()
        if self.pending_reaction is not None:
            self.awaiting_player = True
            return
        guard = 0
        while self.phase is MatchPhase.FIGHT and guard < 500:
            guard += 1
            if (
                self.grapple is not None
                and self.grapple.prey is self.player
                and self.pending_reaction is not None
            ):
                self._clear_pending_reaction()
            if self.pending_reaction is not None:
                self.awaiting_player = True
                return
            actors = self.all_actors()
            if not actors:
                self._finish_loss()
                return
            if self._player_side_incap():
                self._finish_loss()
                return
            if not self.living_enemies():
                self._finish_win()
                return
            nxt = self.scheduler.next_actor(actors, player=self.player)
            self._sync_ap()
            if nxt is None or nxt is self.player:
                self.awaiting_player = True
                return
            if self.grapple is not None and nxt is self.grapple.predator:
                self._predator_grapple_act(nxt)  # type: ignore[arg-type]
            elif self.grapple is not None and nxt is self.grapple.prey:
                if nxt is self.player:
                    self.awaiting_player = True
                    return
                # Ally AI prey: auto break-away attempt
                self._ally_grapple_prey_act(nxt)  # type: ignore[arg-type]
            elif self.is_ally(nxt):  # type: ignore[arg-type]
                self._ally_act(nxt)  # type: ignore[arg-type]
            else:
                self._npc_act(nxt)  # type: ignore[arg-type]
        self.awaiting_player = True

    def handle_event(self, event: tcod.event.Event) -> bool:
        """Return True when recap was dismissed (match fully done)."""
        if self.phase is MatchPhase.RECAP:
            if isinstance(event, tcod.event.KeyDown) and event.sym in _CONFIRM:
                return True
            return False

        if not isinstance(event, tcod.event.KeyDown):
            if not self.awaiting_player and self.pending_reaction is None:
                self.process_npc_until_player()
            return False
        sym = event.sym
        self._sync_ap()

        # Grapple owns PC input while held — never stack with reaction modal.
        if self.grapple is not None and self.grapple.prey is self.player:
            if self.pending_reaction is not None:
                self._clear_pending_reaction()
            # Green: may still cry off mid-hold (mercy bout)
            if sym in _SURRENDER_KEYS:
                self._try_surrender()
                return False
            if self.grapple.phase is VorePhase.ENGULFED:
                if sym in _TALK_KEYS:
                    # Fully swallowed: Talk available; Help me! via free talk path
                    if self.living_allies():
                        self.talk_ui = TalkUiMode.PICK_ALLY
                        self.talk_target_ids = []
                    else:
                        self.message_log.add(
                            "No allies to call.",
                            category=MessageCategory.ROUTINE,
                        )
                    return False
                if sym in _WAIT_KEYS or sym in _SPACE_WAIT or sym in DIRECTION_KEYS:
                    self.scheduler.commit_action(
                        self.player,
                        self.combat_cfg.maneuver("wait").aut_cost,
                    )
                    self.message_log.add(
                        "You thrash uselessly.",
                        category=MessageCategory.CAUTION,
                    )
                    self.awaiting_player = False
                    self.process_npc_until_player()
                return False
            self._handle_grapple_prey_input(sym)
            return False

        if self.pending_reaction is not None:
            return self._handle_reaction_event(event)

        if self.footwork_targeting:
            if sym in _ESCAPE:
                self._cancel_footwork_targeting()
                return False
            if sym in _CONFIRM:
                self._confirm_footwork_targeting()
                return False
            if sym in DIRECTION_KEYS:
                dx, dy = DIRECTION_KEYS[sym]
                self._nudge_footwork_cursor(dx, dy)
                return False
            return False

        if not self.awaiting_player:
            self.process_npc_until_player()
            return False

        if sym in _SURRENDER_KEYS:
            self._try_surrender()
            return False

        # Talk UI
        if self.talk_ui is not TalkUiMode.CLOSED:
            self._handle_talk_event(sym)
            return False

        # Ability UI
        if self.ability_ui is AbilityUiMode.FULL_LIST:
            if sym in _ESCAPE or sym in _CONFIRM:
                self.ability_ui = AbilityUiMode.CLOSED
            return False

        if self.ability_ui is AbilityUiMode.PICK_LETTER:
            if sym in _ESCAPE:
                self.ability_ui = AbilityUiMode.CLOSED
                return False
            if sym in _HELP_KEYS or (sym == KeySym.SLASH):
                self.ability_ui = AbilityUiMode.FULL_LIST
                return False
            letter = _key_to_letter(sym)
            if letter:
                ab = ability_by_letter(self.combat_cfg, letter)
                if ab is None:
                    self.message_log.add(
                        f"No ability bound to '{letter}'.",
                        category=MessageCategory.ROUTINE,
                    )
                    self.ability_ui = AbilityUiMode.CLOSED
                    return False
                self.ability_ui = AbilityUiMode.CLOSED
                self._try_player_ability(ab)
            return False

        if sym in _ABILITY_MENU_KEYS:
            pc = self.combatants[self.player]
            if pc.downed:
                # While downed: a = recover when bar full; s handled below
                self._try_recover_stand()
                return False
            self.ability_ui = AbilityUiMode.PICK_LETTER
            self.message_log.add(
                "Ability: press letter, or ? for list (Esc cancel).",
                category=MessageCategory.CAUTION,
            )
            return False

        # Second Wind (letter S) — also while downed
        if _key_to_letter(sym) == self.recovery_cfg.second_wind.letter:
            self._try_second_wind()
            return False

        if sym in _TALK_KEYS:
            if not self.living_allies():
                self.message_log.add(
                    "No allies to command.",
                    category=MessageCategory.ROUTINE,
                )
                return False
            self.talk_ui = TalkUiMode.PICK_ALLY
            self.talk_target_ids = []
            return False

        # Brace (d) — not while ability menu (handled above)
        if sym in _BRACE_KEYS and self.ability_ui is AbilityUiMode.CLOSED:
            self.recent_dodges = 0
            self._player_brace()
            return False

        if sym in _FOOTWORK_KEYS:
            pc = self.combatants[self.player]
            if pc.downed:
                self.message_log.add(
                    "Too exhausted for footwork.",
                    category=MessageCategory.CAUTION,
                )
                return False
            self._begin_footwork_targeting()
            return False

        if sym in DIRECTION_KEYS:
            dx, dy = DIRECTION_KEYS[sym]
            self.recent_dodges = 0
            mod = int(getattr(event, "mod", 0) or 0)
            from tcod.event import Modifier as _Mod

            ctrl = bool(mod & (int(_Mod.LCTRL) | int(_Mod.RCTRL)))
            shift = bool(mod & (int(_Mod.LSHIFT) | int(_Mod.RSHIFT)))
            if ctrl:
                self._player_directed_attack(dx, dy)
            elif shift:
                # Quick 1-tile footwork shortcut
                self._try_player_footwork(dx, dy)
            else:
                self._player_bump(dx, dy)
            return False
        if sym in _WAIT_KEYS or sym in _SPACE_WAIT:
            self.recent_dodges = 0
            self._player_wait()
            return False
        return False

    def _handle_reaction_event(self, event: tcod.event.KeyDown) -> bool:
        """Process reaction modal input. Never returns True (recap dismiss)."""
        pr = self.pending_reaction
        assert pr is not None
        sym = event.sym

        if pr.awaiting_dodge_dir:
            if sym in _ESCAPE:
                pr.awaiting_dodge_dir = False
                return False
            if sym not in DIRECTION_KEYS:
                return False
            dx, dy = DIRECTION_KEYS[sym]
            self._complete_dodge(dx, dy)
            return False

        if sym in _REACT_DODGE:
            pr.awaiting_dodge_dir = True
            return False
        if sym in _REACT_PARRY:
            self._resolve_incoming(ReactionKind.PARRY)
            return False
        if sym in _REACT_COUNTER:
            self._resolve_incoming(ReactionKind.COUNTER)
            return False
        if sym in _REACT_IGNORE:
            self._resolve_incoming(ReactionKind.IGNORE)
            return False
        return False

    def _complete_dodge(self, dx: int, dy: int) -> None:
        pr = self.pending_reaction
        assert pr is not None
        pos = self.player.components[Position]
        nx, ny = pos.x + dx, pos.y + dy
        blocked = self._blocker_at(nx, ny) is not None
        if blocked or not can_entity_enter_tile(self.game_map, nx, ny, self.player):
            self.message_log.add(
                "No room to dodge that way!",
                category=MessageCategory.CAUTION,
            )
            pr.awaiting_dodge_dir = False
            return
        # Momentum from footwork
        pc_st = self.combatants.get(self.player)
        if pc_st is not None:
            evade_m = momentum_evade_mult(
                pc_st, dx, dy, self.scheduler.world_aut, self.ai_cfg
            )
            if evade_m < 0.5:
                self.message_log.add(
                    "Your momentum works against you!",
                    category=MessageCategory.CAUTION,
                )
            # Soft gate: reverse momentum may fail the dodge
            if evade_m < 0.5 and self.rng.random() > evade_m:
                self.message_log.add(
                    "You fail to reverse course in time!",
                    category=MessageCategory.DANGER,
                )
                pr.awaiting_dodge_dir = False
                self._resolve_incoming(ReactionKind.IGNORE)
                return
        # Fatigue (stamina)
        cost = dodge_fatigue_cost(
            dodges_this_match=self.dodge_count,
            recent_dodges=self.recent_dodges,
        )
        pf = self.player.components[Fighter]
        pf.hp = max(0, pf.hp - int(round(cost)))
        self.player.components[Position] = Position(nx, ny)
        self.dodge_count += 1
        self.recent_dodges += 1
        self.message_log.add(
            f"You dodge aside! (fatigue {cost:.1f})",
            category=MessageCategory.POSITIVE,
        )
        # Incoming attack misses the vacated tile
        aname = entity_log_name(pr.attacker, sentence_start=True)  # type: ignore[arg-type]
        self.message_log.add(
            f"{aname}'s attack cuts empty air.",
            category=MessageCategory.ROUTINE,
        )
        if pr.attacker in self.combatants:
            self.combatants[pr.attacker].shift_balance(
                self.combat_cfg.balance_on_attack,
                self.combat_cfg,
            )
        self.scheduler.commit_action(pr.attacker, pr.attack_aut_cost)
        self.pending_reaction = None
        if self._player_side_incap():
            self._finish_loss()
            return
        self.awaiting_player = False
        self.process_npc_until_player()

    def _resolve_incoming(self, kind: ReactionKind) -> None:
        pr = self.pending_reaction
        assert pr is not None
        attacker = pr.attacker
        assert isinstance(attacker, Entity)
        dmg_mult = pr.damage_mult
        acc_mult = pr.accuracy_mult
        if kind is ReactionKind.PARRY:
            acc_mult *= 0.55
            dmg_mult *= 0.5
            self.message_log.add("You raise a guard!", category=MessageCategory.ROUTINE)
        elif kind is ReactionKind.COUNTER:
            acc_mult *= 0.9
            dmg_mult *= 1.0
        elif kind is ReactionKind.IGNORE:
            pass

        if attacker in self.combatants:
            self.combatants[attacker].shift_balance(
                self.combat_cfg.balance_on_attack,
                self.combat_cfg,
            )
        self._melee(
            attacker,
            self.player,
            cost=pr.attack_aut_cost,
            damage_mult=dmg_mult,
            accuracy_mult=acc_mult,
            style_label=pr.style_label,
            apply_push=True,
        )
        self.pending_reaction = None

        if kind is ReactionKind.COUNTER:
            # Free counter jab if still adjacent and player alive
            pf = self.player.components.get(Fighter)
            if pf is not None and pf.hp > 0 and attacker in self.living_enemies():
                if chebyshev(
                    self.player.components[Position],
                    attacker.components[Position],
                ) <= 1:
                    self.message_log.add(
                        "You snap a counter!",
                        category=MessageCategory.POSITIVE,
                    )
                    self._melee(
                        self.player,
                        attacker,
                        cost=0.0,  # free of AUT for the counter flash
                        damage_mult=0.7,
                        accuracy_mult=1.1,
                        style_label="counter",
                        apply_push=False,
                        commit_attacker=False,
                    )

        if self._player_side_incap():
            self._finish_loss()
            return
        if not self.living_enemies():
            self._finish_win()
            return
        self.awaiting_player = False
        self.process_npc_until_player()

    def _player_wait(self) -> None:
        """Keep watch (. / numpad 5 / space) — near-neutral, not turtle dump."""
        cst = self.combatants[self.player]
        man = self.combat_cfg.maneuver("keep_watch")
        if cst.downed:
            self.scheduler.commit_action(self.player, man.aut_cost)
            self.message_log.add(
                "You catch your breath in the sand.",
                category=MessageCategory.ROUTINE,
            )
            self.awaiting_player = False
            self.process_npc_until_player()
            return
        apply_ready_balance(cst, self.combat_cfg, "keep_watch")
        self.scheduler.commit_action(self.player, man.aut_cost)
        self.message_log.add(
            "You keep watch.",
            category=MessageCategory.ROUTINE,
        )
        self.awaiting_player = False
        self.process_npc_until_player()

    def _player_brace(self) -> None:
        cst = self.combatants[self.player]
        if cst.downed:
            self.message_log.add(
                "You cannot brace while downed.",
                category=MessageCategory.CAUTION,
            )
            return
        man = self.combat_cfg.maneuver("brace")
        apply_ready_balance(cst, self.combat_cfg, "brace")
        self.scheduler.commit_action(self.player, man.aut_cost)
        self.message_log.add(
            "You raise your guard.",
            category=MessageCategory.ROUTINE,
        )
        self.awaiting_player = False
        self.process_npc_until_player()

    def _footwork_max_chebyshev(self) -> int:
        return int(self.ai_cfg.footwork.max_chebyshev)

    def _footwork_legal_tiles(self) -> list[Position]:
        """Legal footwork destinations: any open tile within max_chebyshev (1 and 2)."""
        pos = self.player.components[Position]
        legal: list[Position] = []
        r = self._footwork_max_chebyshev()
        for dx, dy in all_footwork_offsets(max_chebyshev=r):
            tx, ty = pos.x + dx, pos.y + dy
            if self._blocker_at(tx, ty) is not None:
                continue
            if not can_entity_enter_tile(self.game_map, tx, ty, self.player):
                continue
            legal.append(Position(tx, ty))
        return legal

    def _begin_footwork_targeting(self) -> None:
        legal = self._footwork_legal_tiles()
        if not legal:
            self.message_log.add(
                "No legal footwork landing.",
                category=MessageCategory.ROUTINE,
            )
            return
        self.footwork_targeting = True
        # Prefer a forward-ish legal tile; else first legal
        self.footwork_cursor = legal[0]
        for cand in legal:
            if cand.x >= self.player.components[Position].x:
                self.footwork_cursor = cand
                break
        self.message_log.add(
            "Footwork: move cursor 1–2 tiles away (incl. knight range), Enter confirm, Esc cancel. "
            "Shift+direction = quick 1-tile footwork.",
            category=MessageCategory.CAUTION,
        )

    def _cancel_footwork_targeting(self) -> None:
        self.footwork_targeting = False
        self.footwork_cursor = None
        self.message_log.add(
            "Footwork cancelled.",
            category=MessageCategory.ROUTINE,
        )

    def _nudge_footwork_cursor(self, dx: int, dy: int) -> None:
        """Move targeting cursor one tile; snap to nearest legal if leaving legal set is OK.

        Free movement on the map within a short radius, but only legal landings confirm.
        """
        if self.footwork_cursor is None:
            legal = self._footwork_legal_tiles()
            if not legal:
                return
            self.footwork_cursor = legal[0]
        cx = self.footwork_cursor.x + dx
        cy = self.footwork_cursor.y + dy
        # Clamp to map
        cx = max(0, min(self.game_map.width - 1, cx))
        cy = max(0, min(self.game_map.height - 1, cy))
        pos = self.player.components[Position]
        # Keep cursor within Chebyshev 3 of player (footwork range + 1 for aiming)
        if max(abs(cx - pos.x), abs(cy - pos.y)) > 3:
            return
        self.footwork_cursor = Position(cx, cy)

    def _confirm_footwork_targeting(self) -> None:
        if self.footwork_cursor is None:
            self._cancel_footwork_targeting()
            return
        pos = self.player.components[Position]
        dx = self.footwork_cursor.x - pos.x
        dy = self.footwork_cursor.y - pos.y
        r = self._footwork_max_chebyshev()
        if not is_footwork_offset(dx, dy, max_chebyshev=r):
            self.message_log.add(
                "Not a legal footwork landing (need 1–2 tiles away).",
                category=MessageCategory.CAUTION,
            )
            return
        # Keep targeting state until success/fail of resolve
        ok = self._try_player_footwork(dx, dy)
        if ok:
            self.footwork_targeting = False
            self.footwork_cursor = None

    def _try_player_footwork(self, dx: int, dy: int) -> bool:
        """Execute footwork to offset (dx, dy). Returns True if the action committed."""
        cst = self.combatants[self.player]
        r = self._footwork_max_chebyshev()
        if not is_footwork_offset(dx, dy, max_chebyshev=r):
            self.message_log.add(
                "You must footwork to at least 1 tile away.",
                category=MessageCategory.ROUTINE,
            )
            return False
        pos = self.player.components[Position]
        tx, ty = pos.x + dx, pos.y + dy
        if self._blocker_at(tx, ty) is not None or not can_entity_enter_tile(
            self.game_map, tx, ty, self.player
        ):
            self.message_log.add(
                "No room for footwork.",
                category=MessageCategory.ROUTINE,
            )
            return False
        fw = self.ai_cfg.footwork
        world = self.scheduler.world_aut
        chain = 0
        if world - cst.last_footwork_aut <= fw.compound_window_aut:
            chain = cst.footwork_chain + 1
        else:
            chain = 0
        ap_cost = fw.ap_cost_base + chain * fw.ap_cost_compound
        if not cst.spend_ap(ap_cost):
            self.message_log.add(
                f"Not enough AP for footwork (need {ap_cost:.1f}).",
                category=MessageCategory.CAUTION,
            )
            return False
        self.player.components[Position] = Position(tx, ty)
        bal_delta = fw.balance_delta_for(cst.balance)
        if bal_delta:
            cst.shift_balance(bal_delta, self.combat_cfg)
        cst.footwork_chain = chain
        cst.last_footwork_aut = world
        mo = self.ai_cfg.momentum
        cst.momentum_dx = dx
        cst.momentum_dy = dy
        cst.momentum_until_aut = world + mo.duration_aut
        self.scheduler.commit_action(self.player, fw.aut_cost)
        self.message_log.add(
            "You burst into a new position.",
            category=MessageCategory.POSITIVE,
        )
        self.awaiting_player = False
        self.process_npc_until_player()
        return True

    def _player_directed_attack(self, dx: int, dy: int) -> None:
        """ctrl+dir: cone/homing basic attack or feint; R5+ no-op."""
        cst = self.combatants[self.player]
        if cst.downed:
            return
        pos = self.player.components[Position]
        # Candidates in cone: same general direction
        best: Entity | None = None
        best_score = -1.0
        for e in self.living_enemies():
            ep = e.components.get(Position)
            if ep is None:
                continue
            ex, ey = ep.x - pos.x, ep.y - pos.y
            if dx != 0 and (ex == 0 or (ex > 0) != (dx > 0)):
                continue
            if dy != 0 and (ey == 0 or (ey > 0) != (dy > 0)):
                continue
            if dx == 0 and dy == 0:
                continue
            band = effective_band(pos, ep)
            if band >= 5:
                continue
            # prefer closer, aligned
            score = 10.0 - band
            if score > best_score:
                best_score = score
                best = e
        if best is None:
            # No-op — never shame-swing
            self.message_log.add(
                "No foe in reach that way.",
                category=MessageCategory.ROUTINE,
            )
            return
        ep = best.components[Position]
        band = effective_band(pos, ep)
        mm = measure_mult(cst.weapon_id, band)
        if band >= 3 and mm < 0.45:
            # Feint
            fe = self.ai_cfg.feint
            cst.shift_balance(fe.balance_delta, self.combat_cfg)
            self.scheduler.commit_action(self.player, fe.aut_cost)
            self.message_log.add(
                f"You feint toward {entity_log_name(best, sentence_start=False)}.",
                category=MessageCategory.ROUTINE,
            )
            self.awaiting_player = False
            self.process_npc_until_player()
            return
        man = self.combat_cfg.maneuver("standard_attack")
        cst.shift_balance(man.balance_delta, self.combat_cfg)
        delay = attack_delay(cst.weapon_id)
        self._melee(
            self.player,
            best,
            cost=delay,
            damage_mult=man.damage_mult,
            accuracy_mult=man.accuracy_mult,
            style_label="thrust" if band >= 2 else "attack",
            apply_push=band <= 1,
        )
        if self.phase is MatchPhase.RECAP:
            return
        if not self.living_enemies():
            self._finish_win()
            return
        self.awaiting_player = False
        self.process_npc_until_player()

    def _try_recover_stand(self) -> None:
        """Optional Recover when recovery bar is full."""
        cst = self.combatants[self.player]
        rc = self.recovery_cfg
        if not cst.downed:
            return
        if cst.recovery_bar + 1e-9 < rc.recovery_bar_full:
            self.message_log.add(
                "Not ready to stand yet.",
                category=MessageCategory.CAUTION,
            )
            return
        pf = self.player.components[Fighter]
        pf.hp = min(pf.max_hp, rc.recover_to_hp)
        cst.downed = False
        cst.recovery_bar = 0.0
        man = self.combat_cfg.maneuver("wait")
        self.scheduler.commit_action(self.player, man.aut_cost)
        self.message_log.add(
            f"You force yourself up ({pf.hp} HP).",
            category=MessageCategory.POSITIVE,
        )
        self.awaiting_player = False
        self.process_npc_until_player()

    def _try_second_wind(self) -> None:
        rc = self.recovery_cfg.second_wind
        if not rc.enabled:
            return
        cst = self.combatants[self.player]
        if cst.second_wind_uses_left <= 0:
            self.message_log.add(
                "Second Wind already spent this match.",
                category=MessageCategory.CAUTION,
            )
            return
        if not cst.spend_ap(rc.ap_cost):
            self.message_log.add("Not enough AP.", category=MessageCategory.CAUTION)
            return
        cst.second_wind_uses_left -= 1
        pf = self.player.components[Fighter]
        pf.hp = min(pf.max_hp, pf.hp + rc.hp_restore)
        cst.downed = False
        cst.recovery_bar = 0.0
        cst.shift_balance(rc.balance_delta, self.combat_cfg)
        cst.debuff_until_aut = self.scheduler.world_aut + rc.debuff_aut
        cst.debuff_accuracy_mult = rc.debuff_accuracy_mult
        cst.debuff_evade_mult = rc.debuff_evade_mult
        self.scheduler.commit_action(self.player, rc.aut_cost)
        self.message_log.add(
            f"Second Wind! You push to {pf.hp} HP (shaken).",
            category=MessageCategory.POSITIVE,
        )
        self.awaiting_player = False
        self.process_npc_until_player()

    def _handle_talk_event(self, sym: KeySym) -> None:
        living = self.living_allies()
        if self.talk_ui is TalkUiMode.PICK_ALLY:
            if sym in _ESCAPE:
                self.talk_ui = TalkUiMode.CLOSED
                return
            if sym in _TALK_ALL:
                self.talk_target_ids = [
                    self.ally_id_by_entity[e] for e in living if e in self.ally_id_by_entity
                ]
                self.talk_ui = TalkUiMode.PICK_ORDER
                return
            # 1..n for each ally
            letter = _key_to_letter(sym)
            idx = None
            if sym in (KeySym.N1, KeySym.KP_1):
                idx = 0
            elif sym in (KeySym.N2, KeySym.KP_2):
                idx = 1
            elif sym in (KeySym.N3, KeySym.KP_3):
                idx = 2
            if idx is not None and idx < len(living):
                aid = self.ally_id_by_entity.get(living[idx])
                if aid:
                    self.talk_target_ids = [aid]
                    self.talk_ui = TalkUiMode.PICK_ORDER
            return

        if self.talk_ui is TalkUiMode.PICK_ORDER:
            if sym in _ESCAPE:
                self.talk_ui = TalkUiMode.PICK_ALLY
                return
            order = None
            if sym in (KeySym.N1, KeySym.KP_1, KeySym.A):
                order = "attack"
            elif sym in (KeySym.N2, KeySym.KP_2, KeySym.H):
                order = "help_me"
            elif sym in (KeySym.N3, KeySym.KP_3, KeySym.C):
                order = "stay_close"
            # Legacy defend → stay_close
            elif sym in (KeySym.D,):
                order = "stay_close"
            if order is None:
                return
            self._issue_orders(order)
            self.talk_ui = TalkUiMode.CLOSED

    def _issue_orders(self, order: str) -> None:
        """Apply Attack!/Help me!/Stay close!; Free Talk 0 AUT once per refresh, else AP+turn."""
        # Fully swallowed Help me: 50% hear
        from_swallow = (
            self.grapple is not None
            and self.grapple.prey is self.player
            and self.grapple.phase is VorePhase.ENGULFED
            and order == "help_me"
        )
        if from_swallow and self.rng.random() >= self.ai_cfg.help_call_heard_chance_swallow:
            self.message_log.add(
                "You call for help — but no one seems to hear.",
                category=MessageCategory.CAUTION,
            )
            free = self.scheduler.world_aut + 1e-9 >= self.free_talk_ready_at
            if free:
                self.free_talk_ready_at = (
                    self.scheduler.world_aut + self.combat_cfg.free_talk_refresh_aut
                )
            return

        names: list[str] = []
        now = self.scheduler.world_aut
        for aid in self.talk_target_ids:
            self.ally_order[aid] = order
            self.ally_order_issued_at[aid] = now
            # Sync order onto career roster copy
            allies = self.career.allies()
            for a in allies:
                if a.ally_id == aid:
                    a.order = order
                    names.append(a.name)
            self.career.set_allies(allies)
        if order == "help_me":
            label = "Help me!"
            if self.grapple is not None and self.grapple.predator is not None:
                self._note_pc_aggression(self.grapple.predator)  # type: ignore[arg-type]
        elif order == "stay_close":
            label = "Stay close!"
        else:
            label = "Attack!"
        who = ", ".join(names) if names else "allies"
        free = self.scheduler.world_aut + 1e-9 >= self.free_talk_ready_at
        cst = self.combatants[self.player]
        refresh = self.combat_cfg.free_talk_refresh_aut
        man = self.combat_cfg.maneuver("talk_paid")
        if free:
            self.free_talk_ready_at = self.scheduler.world_aut + refresh
            self.patron_stats.talk_used = True
            self.message_log.add(
                f'You shout to {who}: "{label}" (free talk)',
                category=MessageCategory.SPEECH,
            )
            return
        if not cst.spend_ap(man.ap_cost):
            self.message_log.add(
                "Not enough AP to shout again (Free Talk not ready).",
                category=MessageCategory.CAUTION,
            )
            return
        self.message_log.add(
            f'You shout to {who}: "{label}"',
            category=MessageCategory.SPEECH,
        )
        self.patron_stats.talk_used = True
        self.scheduler.commit_action(self.player, man.aut_cost)
        self.awaiting_player = False
        self.process_npc_until_player()

    def _ally_act(self, entity: Entity) -> None:
        if not self.living_enemies():
            cst = self.combatants.get(entity)
            if cst:
                man = self.combat_cfg.maneuver("keep_watch")
                cst.shift_balance(man.balance_delta, self.combat_cfg)
                self.scheduler.commit_action(entity, man.aut_cost)
            else:
                self.scheduler.commit_action(entity, self.costs.wait)
            return
        self._execute_ai_intent(entity, is_ally=True)

    def _on_ally_down(self, entity: Entity) -> None:
        aid = self.ally_id_by_entity.get(entity)
        if not aid:
            return
        self.patron_stats.ally_was_lost = True
        name = "Ally"
        if DisplayName in entity.components:
            name = entity.components[DisplayName].name
        self.scheduler.unregister(entity)
        self.combatants.pop(entity, None)
        if Position in entity.components:
            del entity.components[Position]
        entity.tags.discard(BlocksMovement)
        if self.card.kind == "red":
            allies = self.career.allies()
            new_roster, new_gold, refund = remove_ally_digest(
                allies,
                aid,
                gold=self.career.gold,
            )
            self.career.set_allies(new_roster)
            self.career.gold = new_gold
            note = (
                f"{name} is lost to the sand (digested). "
                f"Compensation: +{refund} gold."
            )
            self.digest_notes.append(note)
            self.message_log.add(note, category=MessageCategory.DANGER)
        else:
            self.message_log.add(
                f"{name} is down (green match — they survive the bout).",
                category=MessageCategory.CAUTION,
            )

    def _player_bump(self, dx: int, dy: int) -> None:
        cst = self.combatants[self.player]
        pos = self.player.components[Position]
        tx, ty = pos.x + dx, pos.y + dy
        target = self._blocker_at(tx, ty)
        # Ally bump: no-op (no AUT) — never smart-melee friendlies
        if target is not None and target is not self.player and self.is_ally(target):
            name = entity_log_name(target, sentence_start=True)
            self.message_log.add(
                msg.ally_standing_there(name),
                category=MessageCategory.ROUTINE,
            )
            return
        if cst.downed:
            # Crawl only — no attacks while down
            if target is not None:
                self.message_log.add(
                    "You are too exhausted to strike.",
                    category=MessageCategory.CAUTION,
                )
                return
            if can_entity_enter_tile(self.game_map, tx, ty, self.player) and target is None:
                self.player.components[Position] = Position(tx, ty)
                man = self.combat_cfg.maneuver("step")
                aut = man.aut_cost * self.recovery_cfg.crawl_step_aut_mult
                aut *= step_aut_multiplier(cst)
                self.scheduler.commit_action(self.player, aut)
                self.message_log.add("You crawl.", category=MessageCategory.ROUTINE)
                self.awaiting_player = False
                self.process_npc_until_player()
                return
            self.message_log.add("You can't go that way.", category=MessageCategory.ROUTINE)
            return
        if target is not None and target is not self.player:
            self._player_melee_smart(target)
            if self.phase is MatchPhase.RECAP:
                return
            if not self.living_enemies():
                self._finish_win()
                return
            self.awaiting_player = False
            self.process_npc_until_player()
            return
        if can_entity_enter_tile(self.game_map, tx, ty, self.player) and target is None:
            self.player.components[Position] = Position(tx, ty)
            man = self.combat_cfg.maneuver("step")
            apply_ready_balance(cst, self.combat_cfg, "step")
            aut = man.aut_cost * step_aut_multiplier(cst)
            self.scheduler.commit_action(self.player, aut)
            self.awaiting_player = False
            self.process_npc_until_player()
            return
        self.message_log.add("You can't go that way.", category=MessageCategory.ROUTINE)

    def _player_melee_smart(self, target: Entity) -> None:
        dfn = target.components[Fighter]
        d_state = self.combatants.get(target)
        d_bal = d_state.balance if d_state else 0
        openness = awareness_openness(d_bal, dfn.hp, dfn.max_hp)
        profile = choose_bump_profile(openness)
        if profile == "jab":
            man = self.combat_cfg.maneuver("jab")
            label = "jab"
        elif profile == "all_out":
            man = self.combat_cfg.maneuver("all_out")
            label = "all-out strike"
        else:
            man = self.combat_cfg.maneuver("standard_attack")
            label = "attack"

        cst = self.combatants[self.player]
        cst.shift_balance(man.balance_delta, self.combat_cfg)
        delay = attack_delay(cst.weapon_id)
        self._melee(
            self.player,
            target,
            cost=delay,
            damage_mult=man.damage_mult,
            accuracy_mult=man.accuracy_mult,
            style_label=label,
            apply_push=True,
        )

    def _try_player_ability(self, ab: MatchAbilityDef) -> None:
        cst = self.combatants[self.player]
        if not cst.spend_ap(ab.ap_cost):
            self.message_log.add(
                f"Not enough AP for {ab.name} (need {ab.ap_cost}).",
                category=MessageCategory.CAUTION,
            )
            return
        # Target: nearest adjacent enemy, else fail soft
        target = self._adjacent_enemy(self.player)
        if target is None and ab.id != "haymaker":
            # refund AP if no target for directed abilities — still "used" thematically?
            # Designer: spend only when resolving; refund here.
            cst.ap = min(cst.ap_max, cst.ap + ab.ap_cost)
            self.message_log.add(
                f"No adjacent foe for {ab.name}.",
                category=MessageCategory.ROUTINE,
            )
            return
        if target is None:
            cst.ap = min(cst.ap_max, cst.ap + ab.ap_cost)
            self.message_log.add(
                f"No adjacent foe for {ab.name}.",
                category=MessageCategory.ROUTINE,
            )
            return

        cst.shift_balance(ab.balance_delta, self.combat_cfg)
        d_state = self.combatants.get(target)
        d_bal = d_state.balance if d_state else 0
        dfn = target.components[Fighter]
        openness = awareness_openness(d_bal, dfn.hp, dfn.max_hp)

        if ab.id == "haymaker":
            if openness >= ab.openness_threshold:
                dmg_mult = ab.damage_mult_open if ab.damage_mult_open is not None else 1.8
                acc_mult = (
                    ab.accuracy_mult_open if ab.accuracy_mult_open is not None else 1.2
                )
                note = "Haymaker crashes through!"
            else:
                dmg_mult = (
                    ab.damage_mult_guarded if ab.damage_mult_guarded is not None else 0.9
                )
                acc_mult = (
                    ab.accuracy_mult_guarded
                    if ab.accuracy_mult_guarded is not None
                    else 0.55
                )
                note = "Haymaker is wild and poorly aimed!"
            self.message_log.add(note, category=MessageCategory.CAUTION)
            self._melee(
                self.player,
                target,
                cost=ab.aut_cost,
                damage_mult=dmg_mult,
                accuracy_mult=acc_mult,
                style_label="haymaker",
                apply_push=True,
                push_tiles=ab.push_tiles,
            )
        elif ab.id == "shield_push":
            turtle = d_bal <= -2 or openness < 0.4
            dmg_mult = ab.damage_mult * (ab.turtle_damage_bonus if turtle else 1.0)
            acc_mult = ab.accuracy_mult * (ab.turtle_accuracy_bonus if turtle else 1.0)
            self.message_log.add(
                "You drive your shield forward!",
                category=MessageCategory.POSITIVE,
            )
            self._melee(
                self.player,
                target,
                cost=ab.aut_cost,
                damage_mult=dmg_mult,
                accuracy_mult=acc_mult,
                style_label="shield push",
                apply_push=True,
                push_tiles=ab.push_tiles,
            )
        elif ab.id == "hook_shield":
            turtle = d_bal <= -2 or openness < 0.4
            dmg_mult = ab.damage_mult * (ab.turtle_damage_bonus if turtle else 1.0)
            acc_mult = ab.accuracy_mult * (ab.turtle_accuracy_bonus if turtle else 1.0)
            self.message_log.add(
                "You hook past their guard!",
                category=MessageCategory.POSITIVE,
            )
            self._melee(
                self.player,
                target,
                cost=ab.aut_cost,
                damage_mult=dmg_mult,
                accuracy_mult=acc_mult,
                style_label="hook",
                apply_push=True,
                push_tiles=ab.push_tiles,
            )
        else:
            self._melee(
                self.player,
                target,
                cost=ab.aut_cost,
                damage_mult=ab.damage_mult,
                accuracy_mult=ab.accuracy_mult,
                style_label=ab.name,
                apply_push=True,
                push_tiles=ab.push_tiles,
            )

        if self.phase is MatchPhase.RECAP:
            return
        if not self.living_enemies():
            self._finish_win()
            return
        self.awaiting_player = False
        self.process_npc_until_player()

    def _adjacent_enemy(self, entity: Entity) -> Entity | None:
        pos = entity.components[Position]
        for e in self.living_enemies():
            ep = e.components[Position]
            if max(abs(ep.x - pos.x), abs(ep.y - pos.y)) == 1:
                return e
        return None

    def _handle_grapple_prey_input(self, sym: KeySym) -> None:
        """PC options while grappled/swallowing (stub wrestling; swallow is modal)."""
        g = self.grapple
        assert g is not None and g.prey is self.player
        if g.phase is VorePhase.SWALLOW:
            # Interactive swallow modal: 1 struggle | 2 conserve | 3 call for help
            if sym in _REACT_DODGE or sym == KeySym.N1 or sym == KeySym.KP_1:
                self._prey_swallow_struggle()
            elif sym in _REACT_PARRY or sym == KeySym.N2 or sym == KeySym.KP_2:
                self._prey_swallow_conserve()
            elif sym in _REACT_COUNTER or sym == KeySym.N3 or sym == KeySym.KP_3:
                self._prey_swallow_call_help()
            return
        if sym in _REACT_DODGE or sym == KeySym.N1 or sym == KeySym.KP_1:
            self._prey_break_away(spend_aut=True)
            return
        if sym in _REACT_PARRY or sym == KeySym.N2 or sym == KeySym.KP_2:
            self._prey_counter_grapple()
            return
        if sym in _WAIT_KEYS:
            self.scheduler.commit_action(
                self.player,
                self.combat_cfg.maneuver("wait").aut_cost,
            )
            self.message_log.add(
                msg.you_brace_in_grip(),
                category=MessageCategory.ROUTINE,
            )
            self.awaiting_player = False
            self.process_npc_until_player()

    def _prey_break_away(self, *, spend_aut: bool) -> None:
        """Grapple-phase wrestling escape (stub odds). Not used for swallow."""
        g = self.grapple
        assert g is not None
        cfg = self.vore_cfg
        if g.phase is VorePhase.SWALLOW:
            self._prey_swallow_struggle()
            return
        chance = break_away_chance(
            grapple_hp=g.grapple_hp,
            grapple_hp_max=g.grapple_hp_max,
            cfg=cfg,
        )
        if spend_aut:
            self.scheduler.commit_action(g.prey, cfg.break_away_aut)
        if self.rng.random() < chance:
            self.message_log.add(
                msg.you_wrench_free(),
                category=MessageCategory.POSITIVE,
            )
            self._end_grapple(released=True)
        else:
            self.message_log.add(
                msg.struggle_grip_holds(),
                category=MessageCategory.CAUTION,
            )
        if self.phase is MatchPhase.FIGHT:
            self.awaiting_player = False
            self.process_npc_until_player()

    def _prey_swallow_struggle(self) -> None:
        """Coup de grâce thrash: ~1% miracle escape (JSON)."""
        g = self.grapple
        assert g is not None and g.phase is VorePhase.SWALLOW
        cfg = self.vore_cfg
        chance = swallow_struggle_escape_chance(cfg)
        self.scheduler.commit_action(g.prey, cfg.swallow_struggle_aut)
        if self.rng.random() < chance:
            self.message_log.add(
                msg.swallow_struggle_miracle(),
                category=MessageCategory.POSITIVE,
            )
            self._end_grapple(released=True)
        else:
            self.message_log.add(
                msg.swallow_struggle_fails(),
                category=MessageCategory.CAUTION,
            )
        if self.phase is MatchPhase.FIGHT:
            self.awaiting_player = False
            self.process_npc_until_player()

    def _prey_swallow_conserve(self) -> None:
        """Focus on breathing: no escape roll; each conserve extends later endurance (no cap)."""
        g = self.grapple
        assert g is not None and g.phase is VorePhase.SWALLOW
        cfg = self.vore_cfg
        g.conserved_strength += 1
        self.scheduler.commit_action(g.prey, cfg.swallow_conserve_aut)
        self.message_log.add(
            msg.swallow_conserve_strength(),
            category=MessageCategory.ROUTINE,
        )
        if self.phase is MatchPhase.FIGHT:
            self.awaiting_player = False
            self.process_npc_until_player()

    def _prey_swallow_call_help(self) -> None:
        """Option 3: call help (50% heard) and advance swallow with no escape/conserve."""
        g = self.grapple
        assert g is not None and g.phase is VorePhase.SWALLOW
        cfg = self.vore_cfg
        self._call_for_help(from_swallow=True)
        # Advance phase without escape or conserve bonus
        g.swallow_phase_index += 1
        self.scheduler.commit_action(g.prey, cfg.swallow_struggle_aut)
        self.message_log.add(
            "The swallow continues as you cry out.",
            category=MessageCategory.DANGER,
        )
        if self.phase is MatchPhase.FIGHT:
            self.awaiting_player = False
            self.process_npc_until_player()

    def _prey_counter_grapple(self) -> None:
        g = self.grapple
        assert g is not None
        cfg = self.vore_cfg
        pred = g.predator
        assert isinstance(pred, Entity)
        pf = pred.components.get(Fighter)
        dmg = self.rng.randint(cfg.counter_grapple_damage_min, cfg.counter_grapple_damage_max)
        if pf is not None:
            pf.hp = max(0, pf.hp - dmg)
            self.message_log.add(
                f"You strike them in the hold for {dmg}!",
                category=MessageCategory.POSITIVE,
            )
            self._note_assist_damage(pred, float(dmg))
        self.scheduler.commit_action(g.prey, cfg.counter_grapple_aut)
        if pf is not None and pf.hp <= 0:
            self._end_grapple(released=True)
            self.message_log.add(
                f"{entity_log_name(pred, sentence_start=True)} is defeated.",
                category=MessageCategory.POSITIVE,
            )
            self.scheduler.unregister(pred)
            self.combatants.pop(pred, None)
            if Position in pred.components:
                del pred.components[Position]
            pred.tags.discard(BlocksMovement)
            if not self.living_enemies():
                self._finish_win()
                return
        elif self.rng.random() < cfg.counter_also_break_chance:
            self.message_log.add(
                "The blow loosens their hold — you slip free!",
                category=MessageCategory.POSITIVE,
            )
            self._end_grapple(released=True)
        if self.phase is MatchPhase.FIGHT:
            self.awaiting_player = False
            self.process_npc_until_player()

    def _ally_grapple_prey_act(self, entity: Entity) -> None:
        """Ally held: auto attempt break-away (grapple) or rare thrash (swallow)."""
        g = self.grapple
        assert g is not None
        cfg = self.vore_cfg
        name = (
            entity.components[DisplayName].name
            if DisplayName in entity.components
            else "Ally"
        )
        if g.phase is VorePhase.SWALLOW:
            chance = swallow_struggle_escape_chance(cfg)
            self.scheduler.commit_action(entity, cfg.swallow_struggle_aut)
        elif g.phase is VorePhase.ENGULFED:
            self.scheduler.commit_action(entity, cfg.break_away_aut)
            self.message_log.add(
                f"{name} thrashes inside!",
                category=MessageCategory.CAUTION,
            )
            return
        else:
            chance = break_away_chance(
                grapple_hp=g.grapple_hp,
                grapple_hp_max=max(1, g.grapple_hp_max),
                cfg=cfg,
            )
            self.scheduler.commit_action(entity, cfg.break_away_aut)
        if self.rng.random() < chance:
            self.message_log.add(
                f"{name} breaks free!",
                category=MessageCategory.POSITIVE,
            )
            self._end_grapple(released=True)
        else:
            self.message_log.add(
                f"{name} struggles in the grip.",
                category=MessageCategory.ROUTINE,
            )

    def _start_grapple(self, predator: Entity, prey: Entity) -> None:
        pf = prey.components[Fighter]
        ghp = max(1, pf.hp) if pf.hp > 0 else 1
        # Red + 0 HP: skip war — grapple_hp 0 so swallow can start immediately
        pc = self.combatants.get(prey)
        downed = pc is not None and pc.downed
        if self.card.kind == "red" and (pf.hp <= 0 or downed):
            ghp = 0
        ally_id = self.ally_id_by_entity.get(prey)
        # Scene ownership: cancel reaction modal so grab doesn't stack with incoming swings
        if Player in prey.tags or (
            self.pending_reaction is not None
            and self.pending_reaction.attacker is not predator
        ):
            self._clear_pending_reaction()
        self.grapple = GrappleState(
            predator=predator,
            prey=prey,
            grapple_hp=ghp,
            grapple_hp_max=max(1, pf.max_hp),
            phase=VorePhase.GRAPPLE,
            prey_is_player=Player in prey.tags,
            prey_ally_id=ally_id,
        )
        # Wrestling clinch: separate tiles (adjacent). Swallow is when they share a tile.
        self._ensure_grapple_adjacent_positions(predator, prey)
        pname = entity_log_name(predator, sentence_start=True)
        if Player in prey.tags:
            self.message_log.add(
                f"{pname} seizes you!",
                category=MessageCategory.DANGER,
            )
        else:
            prey_name = (
                prey.components[DisplayName].name
                if DisplayName in prey.components
                else "ally"
            )
            self.message_log.add(
                f"{pname} seizes {prey_name}!",
                category=MessageCategory.DANGER,
            )
        if ghp <= 0:
            self._begin_swallow()

    def _end_grapple(self, *, released: bool) -> None:
        g = self.grapple
        if g is not None and released:
            self._separate_grapple_participants(
                g.predator,  # type: ignore[arg-type]
                g.prey,  # type: ignore[arg-type]
            )
        self.grapple = None

    def _ensure_grapple_adjacent_positions(
        self, predator: Entity, prey: Entity
    ) -> None:
        """Keep wrestling participants on different adjacent tiles."""
        if Position not in predator.components or Position not in prey.components:
            return
        pp = predator.components[Position]
        pr = prey.components[Position]
        if (pp.x, pp.y) != (pr.x, pr.y):
            return
        # Same tile (e.g. legacy): nudge prey to a free adjacent cell
        for dx, dy in (
            (1, 0),
            (-1, 0),
            (0, 1),
            (0, -1),
            (1, 1),
            (1, -1),
            (-1, 1),
            (-1, -1),
        ):
            nx, ny = pp.x + dx, pp.y + dy
            if not can_entity_enter_tile(self.game_map, nx, ny, prey):
                continue
            if self._blocker_at(nx, ny) is not None:
                continue
            prey.components[Position] = Position(nx, ny)
            return

    def _co_locate_prey_on_predator(self, predator: Entity, prey: Entity) -> None:
        """Swallow finisher: prey vanishes onto predator's tile."""
        if Position not in predator.components:
            return
        if Position not in prey.components:
            return
        pp = predator.components[Position]
        prey.components[Position] = Position(pp.x, pp.y)

    def _separate_grapple_participants(
        self, predator: Entity, prey: Entity
    ) -> None:
        """After release from same tile, place prey on a free adjacent tile."""
        if Position not in predator.components or Position not in prey.components:
            return
        pp = predator.components[Position]
        pr = prey.components[Position]
        if (pp.x, pp.y) != (pr.x, pr.y):
            return
        self._ensure_grapple_adjacent_positions(predator, prey)

    def _sync_grapple_hp_from_stamina(self, prey: Entity, *, damage: int) -> None:
        """Stamina damage while grappled also reduces grapple HP; cap to remaining HP."""
        g = self.grapple
        if g is None or prey is not g.prey:
            return
        g.grapple_hp = max(0, g.grapple_hp - max(0, damage))
        pf = prey.components.get(Fighter)
        if pf is not None and pf.hp > 0:
            g.grapple_hp = min(g.grapple_hp, pf.hp)

    def _begin_swallow(self) -> None:
        g = self.grapple
        assert g is not None
        g.phase = VorePhase.SWALLOW
        g.swallow_phase_index = 0
        # Finisher: prey lifted / vanishing — share the predator's tile
        self._co_locate_prey_on_predator(
            g.predator,  # type: ignore[arg-type]
            g.prey,  # type: ignore[arg-type]
        )
        self.message_log.add(
            "They start to force you down!",
            category=MessageCategory.DANGER,
        ) if g.prey_is_player else self.message_log.add(
            "Swallowing begins!",
            category=MessageCategory.DANGER,
        )

    def _predator_grapple_act(self, predator: Entity) -> None:
        g = self.grapple
        assert g is not None and predator is g.predator
        cfg = self.vore_cfg
        prey = g.prey
        assert isinstance(prey, Entity)

        # Miracle regurg if predator critically hurt
        pred_f = predator.components.get(Fighter)
        if pred_f is not None and pred_f.max_hp > 0:
            if pred_f.hp / pred_f.max_hp <= cfg.regurgitate_predator_hp_fraction:
                self.message_log.add(
                    f"{entity_log_name(predator, sentence_start=True)} heaves — "
                    "forced to release their catch!",
                    category=MessageCategory.POSITIVE,
                )
                self._end_grapple(released=True)
                self.scheduler.commit_action(predator, cfg.predator_secure_aut)
                return

        if g.phase is VorePhase.GRAPPLE:
            if g.grapple_hp <= 0:
                self._begin_swallow()
                self.scheduler.commit_action(predator, cfg.swallow_phase_aut)
                return
            # Crush stamina or secure (ghp)
            if self.rng.random() < 0.5:
                dmg = self.rng.randint(
                    cfg.predator_crush_damage_min,
                    cfg.predator_crush_damage_max,
                )
                pf = prey.components[Fighter]
                pf.hp = max(0, pf.hp - dmg)
                # Grapple HP tracks stamina damage (pools move together)
                self._sync_grapple_hp_from_stamina(prey, damage=dmg)
                self.message_log.add(
                    f"The crushing hold deals {dmg}.",
                    category=MessageCategory.DANGER,
                )
                self.scheduler.commit_action(predator, cfg.predator_crush_aut)
                if Player in prey.tags and pf.hp <= 0:
                    st = self.combatants.get(prey)
                    if st:
                        st.downed = True
                        self.patron_stats.pc_was_downed = True
            else:
                g.grapple_hp = max(0, g.grapple_hp - cfg.predator_secure_grapple_damage)
                self.message_log.add(
                    "They tighten their grip!",
                    category=MessageCategory.DANGER,
                )
                self.scheduler.commit_action(predator, cfg.predator_secure_aut)
            if g.grapple_hp <= 0:
                self._begin_swallow()
            return

        if g.phase is VorePhase.SWALLOW:
            g.swallow_phase_index += 1
            self.scheduler.commit_action(predator, cfg.swallow_phase_aut)
            self.message_log.add(
                f"Swallowing… ({g.swallow_phase_index}/{cfg.swallow_phases})",
                category=MessageCategory.DANGER,
            )
            if g.swallow_phase_index >= cfg.swallow_phases:
                # Green: must release before digest
                if self.card.kind == "green" and cfg.green_abort_before_digest:
                    self.message_log.add(
                        cfg.green_release_message,
                        category=MessageCategory.CAUTION,
                    )
                    self._end_grapple(released=True)
                    return
                g.phase = VorePhase.ENGULFED
                g.digest_strikes = 0
                self.message_log.add(
                    "Fully engulfed!",
                    category=MessageCategory.DANGER,
                )
            return

        if g.phase is VorePhase.ENGULFED:
            # Green safety net
            if self.card.kind == "green" and cfg.green_abort_before_digest:
                self.message_log.add(
                    cfg.green_release_message,
                    category=MessageCategory.CAUTION,
                )
                self._end_grapple(released=True)
                self.scheduler.commit_action(predator, cfg.digest_strike_aut)
                return
            g.digest_strikes += 1
            self.scheduler.commit_action(predator, cfg.digest_strike_aut)
            need = effective_digest_strikes_to_end(
                cfg, conserved_strength=g.conserved_strength
            )
            self.message_log.add(
                f"Digestion presses in… ({g.digest_strikes}/{need})",
                category=MessageCategory.DANGER,
            )
            prey_f = prey.components.get(Fighter)
            if prey_f is not None and prey_f.hp > 0:
                prey_f.hp = max(0, prey_f.hp - 2)
            if g.digest_strikes >= need:
                self._complete_digestion()

    def _complete_digestion(self) -> None:
        g = self.grapple
        assert g is not None
        pred = g.predator
        assert isinstance(pred, Entity)
        flaunt = pick_flaunt(self.rng, self.vore_cfg)
        if g.prey_is_player:
            self.grapple = None
            self._finish_digested(flaunt)
            return
        # Ally digested
        prey = g.prey
        assert isinstance(prey, Entity)
        self.message_log.add(flaunt, category=MessageCategory.DANGER)
        self._end_grapple(released=False)
        self._on_ally_down(prey)
        if self._player_side_incap():
            self._finish_loss()

    def _finish_digested(self, flaunt: str) -> None:
        self.phase = MatchPhase.RECAP
        self.end_kind = MatchEndKind.DIGESTED
        self.ability_ui = AbilityUiMode.CLOSED
        self.pending_reaction = None
        self.talk_ui = TalkUiMode.CLOSED
        self.grapple = None
        if self.instant_action:
            self.recap_lines = (
                "Digested",
                flaunt,
                "Instant action — practice bout ends here.",
                f"{self.card.title}  [{self.card.kind_label}]",
                "",
                self._recap_continue_line(),
            )
        else:
            patron_lines = self._apply_patron_settlement(end_kind="digested")
            crowd_lines = self._apply_crowd_settlement(end_kind="digested")
            self.recap_lines = (
                "Digested",
                flaunt,
                "Your career ends in the pit.",
                f"Final renown: {self.career.renown}",
                f"Gold at end: {self.career.gold}",
                *patron_lines,
                *crowd_lines,
                "",
                self._recap_continue_line(),
            )
        self.awaiting_player = False

    def _note_assist_damage(self, predator: Entity, damage: float) -> None:
        g = self.grapple
        if g is None or predator is not g.predator:
            return
        g.assist_damage_accumulated += damage
        pred_f = predator.components.get(Fighter)
        if pred_f is None or pred_f.max_hp <= 0:
            return
        need = pred_f.max_hp * self.vore_cfg.ally_assist_release_damage_fraction
        if g.assist_damage_accumulated >= need:
            self.message_log.add(
                "The combined assault forces them to let go!",
                category=MessageCategory.POSITIVE,
            )
            self._end_grapple(released=True)

    def _try_enemy_grab(self, entity: Entity, target: Entity) -> bool:
        """Maybe start grapple instead of normal attack. Returns True if grab resolved."""
        if self.grapple is not None:
            return False
        # Green still allows grab-for-control
        tf = target.components.get(Fighter)
        if tf is None:
            return False
        st = self.combatants.get(target)
        downed = st is not None and st.downed
        chance = grab_chance(
            prey_hp=tf.hp,
            prey_max_hp=tf.max_hp,
            prey_downed=downed or tf.hp <= 0,
            cfg=self.vore_cfg,
        )
        chance = min(0.95, chance * float(self.difficulty.grab_chance_mult))
        if self.rng.random() > chance:
            return False
        cst = self.combatants.get(entity)
        if cst:
            cst.shift_balance(self.vore_cfg.grab_balance_delta_predator, self.combat_cfg)
        self.scheduler.commit_action(entity, self.vore_cfg.grab_aut_cost)
        self._start_grapple(entity, target)
        return True

    def _execute_ai_intent(self, entity: Entity, *, is_ally: bool) -> None:
        """Run one fuzzy AI turn for enemy or ally."""
        cst = self.combatants.get(entity)
        if cst is None or Position not in entity.components:
            self.scheduler.commit_action(entity, self.costs.wait)
            return
        pos = entity.components[Position]
        world = self.scheduler.world_aut
        live = entity.components.get(Fighter)
        if live is not None:
            maybe_start_morale_shock(cst, int(live.hp), world, self.ai_cfg, self.rng)
        cst.clear_expired_statuses(world)

        def can_enter(x: int, y: int) -> bool:
            if self._blocker_at(x, y) is not None:
                return False
            return can_entity_enter_tile(self.game_map, x, y, entity)

        if is_ally:
            enemies = self.living_enemies()
            targets = [
                (e, e.components[Position], e.components[Fighter])
                for e in enemies
                if Position in e.components and Fighter in e.components
            ]
            aid = self.ally_id_by_entity.get(entity, "")
            order = self.ally_order.get(aid, "attack")
            issued = self.ally_order_issued_at.get(aid, -999.0)
            if order != "attack" and issued >= 0:
                if should_forget_order(issued, world, self.ai_cfg, self.rng):
                    order = "attack"
                    self.ally_order[aid] = "attack"
            help_set = self._recent_pc_aggressors()
            # During grapple, predator is help target
            g = self.grapple
            if g is not None and isinstance(g.predator, Entity):
                help_set = set(help_set)
                help_set.add(g.predator)
            intent = score_ally_intents(
                rng=self.rng,
                ai_cfg=self.ai_cfg,
                state=cst,
                pos=pos,
                player_pos=self.player.components[Position],
                order=order,
                enemies=targets,
                help_targets=help_set,
                world_aut=world,
                can_enter=can_enter,
                can_clinch=True,
            )
        else:
            targets_list: list[tuple[object, Position, Fighter]] = []
            pf = self.player.components.get(Fighter)
            if pf is not None and not self._is_obscured_prey(self.player):
                targets_list.append(
                    (self.player, self.player.components[Position], pf)
                )
            for ally in self.living_allies():
                if self._is_obscured_prey(ally):
                    continue
                af = ally.components.get(Fighter)
                if af is not None and Position in ally.components:
                    targets_list.append((ally, ally.components[Position], af))
            intent = score_enemy_intents(
                rng=self.rng,
                ai_cfg=self.ai_cfg,
                state=cst,
                pos=pos,
                targets=targets_list,
                world_aut=world,
                can_enter=can_enter,
                can_clinch=True,
            )

        if intent.kind == "keep_watch":
            man = self.combat_cfg.maneuver("keep_watch")
            apply_ready_balance(cst, self.combat_cfg, "keep_watch")
            self.scheduler.commit_action(entity, man.aut_cost)
            return
        if intent.kind == "brace":
            man = self.combat_cfg.maneuver("brace")
            apply_ready_balance(cst, self.combat_cfg, "brace")
            self.scheduler.commit_action(entity, man.aut_cost)
            return
        if intent.kind == "step":
            tx, ty = pos.x + intent.dx, pos.y + intent.dy
            if can_enter(tx, ty):
                entity.components[Position] = Position(tx, ty)
                man = self.combat_cfg.maneuver("step")
                apply_ready_balance(cst, self.combat_cfg, "step")
                self.scheduler.commit_action(entity, man.aut_cost)
                return
            man = self.combat_cfg.maneuver("keep_watch")
            apply_ready_balance(cst, self.combat_cfg, "keep_watch")
            self.scheduler.commit_action(entity, man.aut_cost)
            return
        if intent.kind == "footwork":
            fw = self.ai_cfg.footwork
            tx, ty = pos.x + intent.dx, pos.y + intent.dy
            if not can_enter(tx, ty) or not is_footwork_offset(
                intent.dx, intent.dy, max_chebyshev=fw.max_chebyshev
            ):
                man = self.combat_cfg.maneuver("keep_watch")
                apply_ready_balance(cst, self.combat_cfg, "keep_watch")
                self.scheduler.commit_action(entity, man.aut_cost)
                return
            ap_cost = fw.ap_cost_base
            if not cst.spend_ap(ap_cost):
                # fall back to step
                sdx = (intent.dx > 0) - (intent.dx < 0)
                sdy = (intent.dy > 0) - (intent.dy < 0)
                if can_enter(pos.x + sdx, pos.y + sdy):
                    entity.components[Position] = Position(pos.x + sdx, pos.y + sdy)
                    man = self.combat_cfg.maneuver("step")
                    apply_ready_balance(cst, self.combat_cfg, "step")
                    self.scheduler.commit_action(entity, man.aut_cost)
                    return
                self.scheduler.commit_action(entity, self.costs.wait)
                return
            entity.components[Position] = Position(tx, ty)
            bal_d = fw.balance_delta_for(cst.balance)
            if bal_d:
                cst.shift_balance(bal_d, self.combat_cfg)
            cst.momentum_dx = intent.dx
            cst.momentum_dy = intent.dy
            cst.momentum_until_aut = world + self.ai_cfg.momentum.duration_aut
            self.scheduler.commit_action(entity, fw.aut_cost)
            return
        if intent.kind == "clinch":
            target = intent.target_key
            if isinstance(target, Entity) and self._try_enemy_grab(entity, target):
                return
            # fall through to attack on same target
            if isinstance(target, Entity):
                man = self.combat_cfg.maneuver("standard_attack")
                delay = attack_delay(cst.weapon_id)
                cst.shift_balance(man.balance_delta, self.combat_cfg)
                if target is self.player:
                    self._note_pc_aggression(entity)
                    self._npc_open_player_attack(entity)
                    return
                self._melee(
                    entity,
                    target,
                    cost=delay,
                    damage_mult=man.damage_mult,
                    accuracy_mult=man.accuracy_mult,
                    apply_push=True,
                )
                return
        if intent.kind == "ability" and intent.ability_id:
            ab = None
            for a in self.combat_cfg.abilities:
                if a.id == intent.ability_id:
                    ab = a
                    break
            target = intent.target_key
            if ab is not None and isinstance(target, Entity) and cst.spend_ap(ab.ap_cost):
                cst.shift_balance(ab.balance_delta, self.combat_cfg)
                if target is self.player:
                    self._note_pc_aggression(entity)
                    self._npc_open_player_attack(entity)
                    return
                self._melee(
                    entity,
                    target,
                    cost=ab.aut_cost,
                    damage_mult=ab.damage_mult,
                    accuracy_mult=ab.accuracy_mult,
                    apply_push=True,
                )
                return
        if intent.kind == "attack":
            target = intent.target_key
            if not isinstance(target, Entity):
                man = self.combat_cfg.maneuver("keep_watch")
                self.scheduler.commit_action(entity, man.aut_cost)
                return
            man = self.combat_cfg.maneuver(intent.profile or "standard_attack")
            delay = attack_delay(cst.weapon_id)
            if target is self.player:
                self._note_pc_aggression(entity)
                # Use reaction modal path
                aname = entity_log_name(entity, sentence_start=True)
                cst.shift_balance(man.balance_delta, self.combat_cfg)
                self._npc_open_player_attack(entity)
                return
            cst.shift_balance(man.balance_delta, self.combat_cfg)
            self._melee(
                entity,
                target,
                cost=delay,
                damage_mult=man.damage_mult,
                accuracy_mult=man.accuracy_mult,
                apply_push=True,
            )
            return
        man = self.combat_cfg.maneuver("keep_watch")
        cst.shift_balance(man.balance_delta, self.combat_cfg)
        self.scheduler.commit_action(entity, man.aut_cost)

    def _npc_open_player_attack(self, entity: Entity) -> None:
        """Telegraph a swing at the PC (reaction modal). Never while PC is grappled prey."""
        if self._is_obscured_prey(self.player):
            return
        aname = entity_log_name(entity, sentence_start=True)
        self.pending_reaction = PendingReaction(
            attacker=entity,
            attack_aut_cost=self.combat_cfg.maneuver("standard_attack").aut_cost,
            style_label="attack",
            announce=f"{aname} swings at you!",
        )
        self.awaiting_player = True

    def _npc_act(self, entity: Entity) -> None:
        if self.grapple is not None:
            # Only predator/prey use special acts; other NPCs fight normally
            if entity is self.grapple.predator or entity is self.grapple.prey:
                return
        self._execute_ai_intent(entity, is_ally=False)

    def _other_adjacent_positions(
        self,
        defender: Entity,
        attacker: Entity,
    ) -> list[Position]:
        """Other living combatants adjacent to defender (flank partners)."""
        dpos = defender.components[Position]
        others: list[Position] = []
        candidates: list[Entity] = list(self.living_enemies())
        candidates.extend(self.living_allies())
        pf = self.player.components.get(Fighter)
        if pf is not None and pf.hp > 0:
            candidates.append(self.player)
        for e in candidates:
            if e is attacker or e is defender:
                continue
            ep = e.components.get(Position)
            if ep is None:
                continue
            if chebyshev(ep, dpos) == 1:
                others.append(ep)
        return others

    def _melee(
        self,
        attacker: Entity,
        defender: Entity,
        *,
        cost: float,
        damage_mult: float = 1.0,
        accuracy_mult: float = 1.0,
        style_label: str = "attack",
        apply_push: bool = False,
        push_tiles: int | None = None,
        commit_attacker: bool = True,
    ) -> None:
        # Hard gate: obscured grapple prey only takes damage from their predator.
        if not self._attacker_may_hit(attacker, defender):
            return
        a_state = self.combatants.get(attacker)
        d_state = self.combatants.get(defender)
        atk_live = attacker.components[Fighter]
        dfn_live = defender.components[Fighter]

        # Flanking accuracy from angular separation
        flank_mult, flank_note = flank_accuracy_multiplier(
            attacker.components[Position],
            defender.components[Position],
            self._other_adjacent_positions(defender, attacker),
        )
        accuracy_mult *= flank_mult

        # Weapon measure bands
        if (
            Position in attacker.components
            and Position in defender.components
            and a_state is not None
        ):
            band = effective_band(
                attacker.components[Position], defender.components[Position]
            )
            mm = measure_mult(a_state.weapon_id, band)
            accuracy_mult *= mm
            damage_mult *= mm

        if a_state is not None:
            atk_stats = actual_fighter(a_state, self.combat_cfg, live_hp=atk_live.hp)
            atk_stats = Fighter(
                hp=atk_live.hp,
                max_hp=atk_stats.max_hp,
                accuracy=atk_stats.accuracy * accuracy_mult,
                evade=atk_stats.evade,
                ac=atk_stats.ac,
                min_damage=max(0, int(round(atk_stats.min_damage * damage_mult))),
                max_damage=max(0, int(round(atk_stats.max_damage * damage_mult))),
            )
        else:
            atk_stats = Fighter(
                hp=atk_live.hp,
                max_hp=atk_live.max_hp,
                accuracy=atk_live.accuracy * accuracy_mult,
                evade=atk_live.evade,
                ac=atk_live.ac,
                min_damage=max(0, int(round(atk_live.min_damage * damage_mult))),
                max_damage=max(0, int(round(atk_live.max_damage * damage_mult))),
            )

        if d_state is not None:
            dfn_stats = actual_fighter(d_state, self.combat_cfg, live_hp=dfn_live.hp)
            dfn_stats = Fighter(
                hp=dfn_live.hp,
                max_hp=dfn_stats.max_hp,
                accuracy=dfn_stats.accuracy,
                evade=dfn_stats.evade,
                ac=dfn_stats.ac,
                min_damage=dfn_stats.min_damage,
                max_damage=dfn_stats.max_damage,
            )
        else:
            dfn_stats = dfn_live

        hit, dmg = resolve_attack(atk_stats, dfn_stats, self.rng)
        if Player in attacker.tags:
            aname = "You"
        elif self.is_ally(attacker):
            aname = (
                attacker.components[DisplayName].name
                if DisplayName in attacker.components
                else "Ally"
            )
        else:
            aname = entity_log_name(attacker, sentence_start=True)
        if Player in defender.tags:
            dname = "you"
        elif self.is_ally(defender):
            dname = (
                defender.components[DisplayName].name
                if DisplayName in defender.components
                else "ally"
            )
        else:
            dname = entity_log_name(defender, sentence_start=False)
        if flank_note and hit:
            style_label = f"{style_label} ({flank_note})"

        if not hit:
            if Player in attacker.tags:
                self.crowd.shift(self.crowd_cfg.on_player_miss, self.crowd_cfg)
                self.message_log.add(
                    f"Your {style_label} misses {dname}.",
                    category=MessageCategory.ROUTINE,
                )
            else:
                self.message_log.add(
                    f"{aname} misses {dname}.",
                    category=MessageCategory.ROUTINE,
                )
        else:
            dfn_live.hp = max(0, dfn_live.hp - dmg)
            if Player in attacker.tags:
                self.crowd.shift(self.crowd_cfg.on_player_hit, self.crowd_cfg)
                self.message_log.add(
                    f"Your {style_label} hits {dname} for {dmg}.",
                    category=MessageCategory.POSITIVE,
                )
            else:
                if Player in defender.tags:
                    self.crowd.shift(
                        self.crowd_cfg.on_enemy_hit_player, self.crowd_cfg
                    )
                self.message_log.add(
                    f"{aname} hits {dname} for {dmg}.",
                    category=MessageCategory.DANGER
                    if Player in defender.tags
                    else MessageCategory.POSITIVE,
                )
            # Grapple: stamina damage on prey; assist damage on predator
            if self.grapple is not None and dmg > 0:
                if defender is self.grapple.prey:
                    self._sync_grapple_hp_from_stamina(defender, damage=dmg)
                    if (
                        self.grapple is not None
                        and self.grapple.grapple_hp <= 0
                        and self.grapple.phase is VorePhase.GRAPPLE
                    ):
                        self._begin_swallow()
                elif defender is self.grapple.predator:
                    self._note_assist_damage(defender, float(dmg))
            # Injury roll (PC and allies only — vague labels)
            if d_state is not None and (
                Player in defender.tags or self.is_ally(defender)
            ):
                new_inj, label = try_apply_from_hit(
                    d_state.injuries,
                    damage=dmg,
                    defender_max_hp=max(1, dfn_live.max_hp),
                    rng=self.rng,
                )
                if label:
                    d_state.injuries = new_inj
                    self.message_log.add(label, category=MessageCategory.CAUTION)
                    self._persist_injuries(defender, d_state)
            if apply_push and dmg > 0 and dfn_live.hp > 0:
                tiles = push_tiles if push_tiles is not None else (2 if dmg >= 4 else 1)
                self._apply_push(attacker, defender, tiles=tiles)
            if dfn_live.hp <= 0:
                if (
                    self.grapple is not None
                    and (
                        defender is self.grapple.predator
                        or defender is self.grapple.prey
                    )
                ):
                    self._end_grapple(released=True)
                if Player in defender.tags:
                    # Stunned / downed — not match end by itself
                    if d_state is not None:
                        d_state.downed = True
                        d_state.recovery_bar = 0.0
                    self.patron_stats.pc_was_downed = True
                    self.message_log.add(
                        "You collapse, exhausted. (Recover when ready; or Second Wind.)",
                        category=MessageCategory.DANGER,
                    )
                elif self.is_ally(defender):
                    self._on_ally_down(defender)
                else:
                    self.message_log.add(
                        f"{entity_log_name(defender, sentence_start=True)} is defeated.",
                        category=MessageCategory.POSITIVE,
                    )
                    self.scheduler.unregister(defender)
                    self.combatants.pop(defender, None)
                    if Position in defender.components:
                        del defender.components[Position]
                    defender.tags.discard(BlocksMovement)
        if commit_attacker and cost > 0:
            self.scheduler.commit_action(attacker, cost)
        elif commit_attacker and cost <= 0:
            pass

    def _persist_injuries(self, entity: Entity, state: CombatantState) -> None:
        """Write injuries back to career roster / PC sheet."""
        if Player in entity.tags:
            self.career.set_player_injuries(state.injuries)
            return
        aid = self.ally_id_by_entity.get(entity)
        if not aid:
            return
        allies = self.career.allies()
        for a in allies:
            if a.ally_id == aid:
                a.injuries = injuries_to_dicts(state.injuries)
        self.career.set_allies(allies)

    def _apply_push(self, attacker: Entity, defender: Entity, *, tiles: int) -> None:
        ap = attacker.components[Position]
        dp = defender.components[Position]
        dx, dy = push_direction(ap, dp)
        if dx == 0 and dy == 0:
            return

        def blocked(x: int, y: int) -> bool:
            return self._blocker_at(x, y) is not None

        new_pos, wall_dmg, moved = resolve_pushback(
            self.game_map,
            defender,
            dp,
            dx,
            dy,
            tiles=tiles,
            is_blocked=blocked,
        )
        if moved:
            defender.components[Position] = new_pos
            who = (
                "You are"
                if Player in defender.tags
                else f"{entity_log_name(defender, sentence_start=True)} is"
            )
            self.message_log.add(
                f"{who} shoved back.",
                category=MessageCategory.ROUTINE,
            )
        if wall_dmg > 0:
            dfn = defender.components[Fighter]
            dfn.hp = max(0, dfn.hp - wall_dmg)
            self.message_log.add(
                f"Impact against the wall deals {wall_dmg}!",
                category=MessageCategory.DANGER,
            )

    def _blocker_at(self, x: int, y: int) -> Entity | None:
        for entity in self.world.Q.all_of(components=[Position], tags=[BlocksMovement]):
            p = entity.components[Position]
            if p.x == x and p.y == y:
                fighter = entity.components.get(Fighter)
                if fighter is not None and fighter.hp <= 0:
                    continue
                return entity
        return None

    def _try_surrender(self) -> None:
        """Green mid-match cry-off only; denied if too early or red."""
        if self.phase is not MatchPhase.FIGHT:
            return
        if self.card.kind != "green":
            self.message_log.add(
                "You cannot surrender a red match.",
                category=MessageCategory.CAUTION,
            )
            return
        econ = load_match_cards_config().economy
        if self.scheduler.world_aut < econ.surrender_min_world_aut:
            self.message_log.add(
                "Too early to cry off — the crowd expects a fight first.",
                category=MessageCategory.CAUTION,
            )
            return
        self._finish_surrender()

    def _apply_patron_settlement(self, *, end_kind: str) -> list[str]:
        """Evaluate patron objective; grant gold bonus on hit only. Returns recap lines."""
        self.patron_stats.end_kind = end_kind
        self.patron_stats.world_aut = self.scheduler.world_aut
        hit, bonus, line = evaluate_objective(self.patron_objective, self.patron_stats)
        if line:
            self.career.last_patron_result = line
        out: list[str] = []
        if hit and bonus > 0:
            self.career.gold += bonus
            self.gold_delta += bonus
            self.crowd.shift(self.crowd_cfg.on_patron_hit, self.crowd_cfg)
            out.append(line)
        elif line:
            out.append(line)
        return out

    def _apply_crowd_settlement(self, *, end_kind: str) -> list[str]:
        """End-of-match crowd mood + optional gold crumb."""
        cfg = self.crowd_cfg
        if end_kind == "win":
            self.crowd.shift(cfg.on_win, cfg)
        elif end_kind == "surrender":
            self.crowd.shift(cfg.on_surrender, cfg)
        elif end_kind == "digested":
            self.crowd.shift(cfg.on_digest, cfg)
        else:
            self.crowd.shift(cfg.on_loss, cfg)
        bonus, mood = settle_crowd_gold(self.crowd.favor, cfg)
        lines = [f"Crowd favor {self.crowd.favor}: {mood}"]
        if bonus > 0:
            self.career.gold += bonus
            self.gold_delta += bonus
            lines.append(f"Crowd bonus: +{bonus} gold")
        return lines

    def _payout_diff_mult(self) -> float:
        return float(self.difficulty.payout_mult)

    def _recap_continue_line(self) -> str:
        if self.instant_action:
            return "Press Enter to return to the main menu."
        return "Press Enter to return to downtime."

    def _finish_surrender(self) -> None:
        self.phase = MatchPhase.RECAP
        self.end_kind = MatchEndKind.SURRENDER
        self.ability_ui = AbilityUiMode.CLOSED
        self.pending_reaction = None
        self.talk_ui = TalkUiMode.CLOSED
        self.grapple = None
        econ = load_match_cards_config().economy
        gold, renown, frac = compute_surrender_payout(
            self.card,
            world_aut=self.scheduler.world_aut,
            economy=econ,
            difficulty_payout_mult=self._payout_diff_mult(),
        )
        self.gold_delta = 0 if self.instant_action else gold
        self.renown_delta = 0 if self.instant_action else renown
        if not self.instant_action:
            self.career.gold += gold
            self.career.renown += renown
            self.career.round_index += 1
        patron_lines = (
            () if self.instant_action else self._apply_patron_settlement(end_kind="surrender")
        )
        crowd_lines = (
            () if self.instant_action else self._apply_crowd_settlement(end_kind="surrender")
        )
        notes = tuple(self.digest_notes) if self.digest_notes else ()
        pct = int(round(frac * 100))
        if self.instant_action:
            self.recap_lines = (
                "Surrender",
                "Instant action — practice bout ended under mercy rules.",
                f"{self.card.title}  [{self.card.kind_label}]",
                *notes,
                "",
                self._recap_continue_line(),
            )
        else:
            self.recap_lines = (
                "Surrender",
                "You cry off mid-match. The bout ends under mercy rules.",
                f"Show length scaled payout ({pct}% of appearance fee).",
                f"+{gold} gold  |  +{renown} renown",
                f"Purse: {self.career.gold} gold  |  Renown: {self.career.renown}",
                f"Next round: {self.career.round_index}",
                *patron_lines,
                *crowd_lines,
                *notes,
                "",
                self._recap_continue_line(),
            )
        self.awaiting_player = False

    def _finish_win(self) -> None:
        self.phase = MatchPhase.RECAP
        self.end_kind = MatchEndKind.WIN
        self.ability_ui = AbilityUiMode.CLOSED
        self.pending_reaction = None
        self.talk_ui = TalkUiMode.CLOSED
        self.grapple = None
        econ = load_match_cards_config().economy
        gold, renown = compute_win_payout(
            self.card, econ, difficulty_payout_mult=self._payout_diff_mult()
        )
        self.gold_delta = 0 if self.instant_action else gold
        self.renown_delta = 0 if self.instant_action else renown
        if not self.instant_action:
            self.career.gold += gold
            self.career.renown += renown
            self.career.round_index += 1
        patron_lines = (
            () if self.instant_action else self._apply_patron_settlement(end_kind="win")
        )
        crowd_lines = (
            () if self.instant_action else self._apply_crowd_settlement(end_kind="win")
        )
        notes = tuple(self.digest_notes) if self.digest_notes else ()
        if self.instant_action:
            self.recap_lines = (
                "Victory!",
                f"Instant action — defeated: {self.card.title}",
                f"Risk: {self.card.kind_label}",
                *notes,
                "",
                self._recap_continue_line(),
            )
        else:
            self.recap_lines = (
                "Victory!",
                f"You defeated the opposition in: {self.card.title}",
                f"Risk: {self.card.kind_label}",
                f"+{gold} gold  |  +{renown} renown",
                f"Purse: {self.career.gold} gold  |  Renown: {self.career.renown}",
                f"Next round: {self.career.round_index}",
                *patron_lines,
                *crowd_lines,
                *notes,
                "",
                self._recap_continue_line(),
            )
        self.awaiting_player = False

    def _finish_loss(self) -> None:
        self.phase = MatchPhase.RECAP
        self.end_kind = MatchEndKind.LOSS
        self.ability_ui = AbilityUiMode.CLOSED
        self.pending_reaction = None
        self.talk_ui = TalkUiMode.CLOSED
        self.grapple = None
        econ = load_match_cards_config().economy
        gold, renown = compute_loss_payout(
            self.card, econ, difficulty_payout_mult=self._payout_diff_mult()
        )
        if self.card.kind == "green":
            note = "Green match loss — appearance fee only. (No digestion.)"
        else:
            note = (
                "Red match loss — you are hauled out of the sand alive. "
                "(Permanent end only if digested.)"
            )
        self.gold_delta = 0 if self.instant_action else gold
        self.renown_delta = 0 if self.instant_action else renown
        if not self.instant_action:
            self.career.gold += gold
            self.career.renown += renown
            self.career.round_index += 1
        patron_lines = (
            () if self.instant_action else self._apply_patron_settlement(end_kind="loss")
        )
        crowd_lines = (
            () if self.instant_action else self._apply_crowd_settlement(end_kind="loss")
        )
        notes = tuple(self.digest_notes) if self.digest_notes else ()
        if self.instant_action:
            self.recap_lines = (
                "Defeat",
                f"Instant action — {note}",
                f"{self.card.title}  [{self.card.kind_label}]",
                *notes,
                "",
                self._recap_continue_line(),
            )
        else:
            self.recap_lines = (
                "Defeat",
                note,
                f"+{gold} gold",
                f"Purse: {self.career.gold} gold  |  Renown: {self.career.renown}",
                f"Next round: {self.career.round_index}",
                *patron_lines,
                *crowd_lines,
                *notes,
                "",
                self._recap_continue_line(),
            )
        self.awaiting_player = False


def start_match(
    career: CareerState,
    card: MatchCard,
    *,
    seed: int | None = None,
) -> MatchSession:
    rng = random.Random(seed)
    costs = load_aut_costs()
    combat_cfg = load_match_combat_config()
    recovery_cfg = load_recovery_config()
    game_map = build_sand_pit_map()
    world = Registry()

    px, py = sand_pit_player_spawn()
    player = world[object()]
    player.components[Position] = Position(px, py)
    player.components[Renderable] = Renderable(ch=ord("@"), fg=(255, 255, 255))
    # Stamina full each match; injuries persist as stat debuffs
    player.components[Fighter] = Fighter(
        hp=PLAYER_MAX_HP,
        max_hp=PLAYER_MAX_HP,
        accuracy=float(PLAYER_ACCURACY),
        evade=float(PLAYER_EVADE),
        ac=PLAYER_AC,
        min_damage=PLAYER_MIN_DAMAGE,
        max_damage=PLAYER_MAX_DAMAGE,
    )
    player.tags.add(Player)
    player.tags.add(BlocksMovement)
    player_injuries = career.get_player_injuries()

    registry = load_entity_registry()
    spawn_plan: list[str] = []
    for entity_id, count in enemies_for_card(card):
        spawn_plan.extend([entity_id] * max(1, int(count)))
    if not spawn_plan:
        spawn_plan = ["rat"]
    # Solo Duels career: force exactly one opponent
    if career.is_solo():
        spawn_plan = [spawn_plan[0]]
    spawns = sand_pit_enemy_spawns(len(spawn_plan))
    enemies: list[Entity] = []
    for (sx, sy), entity_id in zip(spawns, spawn_plan):
        try:
            definition = registry.get(entity_id)
        except KeyError:
            definition = registry.get("rat")
        ent = spawn_match_entity(world, definition, sx, sy, rng=rng)
        enemies.append(ent)

    # Difficulty: scale enemy stamina and damage (stub)
    diff = resolve_difficulty(career.difficulty_id)
    for ent in enemies:
        ef = ent.components.get(Fighter)
        if ef is None:
            continue
        new_max = max(1, int(round(ef.max_hp * diff.enemy_hp_mult)))
        ef.max_hp = new_max
        ef.hp = new_max
        ef.min_damage = max(0, int(round(ef.min_damage * diff.enemy_damage_mult)))
        ef.max_damage = max(
            ef.min_damage,
            int(round(ef.max_damage * diff.enemy_damage_mult)),
        )

    # Deployed allies (PC + up to card max / career max) — never for solo careers
    tuning = load_roster_tuning()
    if career.is_solo():
        max_dep = 0
        to_deploy = []
    else:
        max_dep = min(
            career.max_deployed_allies, card.max_allies, tuning.max_deployed_allies
        )
        to_deploy = deployed_allies(career.allies(), max_deploy=max_dep)
    ally_entities: list[Entity] = []
    ally_id_by_entity: dict[object, str] = {}
    ally_order: dict[str, str] = {}
    ally_offsets = ((1, 0), (0, 1), (0, -1), (1, 1), (1, -1))
    for i, rec in enumerate(to_deploy):
        ox, oy = ally_offsets[i % len(ally_offsets)]
        ax, ay = px + ox, py + oy
        # Keep inside sand
        ax = max(1, min(game_map.width - 2, ax))
        ay = max(1, min(game_map.height - 2, ay))
        ally = world[object()]
        ally.components[Position] = Position(ax, ay)
        glyph = "A"
        try:
            glyph = registry.get(rec.species_id).glyph
        except Exception:
            pass
        ally.components[Renderable] = Renderable(
            ch=ord(glyph[0]) if glyph else ord("A"),
            fg=(120, 200, 255),
        )
        ally.components[Fighter] = Fighter(
            hp=rec.max_hp,
            max_hp=rec.max_hp,
            accuracy=float(rec.accuracy),
            evade=float(rec.evade),
            ac=int(rec.ac),
            min_damage=int(rec.min_damage),
            max_damage=int(rec.max_damage),
        )
        ally.components[DisplayName] = DisplayName(name=rec.name)
        ally.components[AI] = AI()
        ally.tags.add(BlocksMovement)
        ally_entities.append(ally)
        ally_id_by_entity[ally] = rec.ally_id
        ally_order[rec.ally_id] = rec.order or "attack"

    scheduler = AutScheduler()
    scheduler.register(player)
    ai_cfg = load_match_ai_config()
    combatants: dict[object, CombatantState] = {
        player: CombatantState.from_fighter(
            player.components[Fighter],
            combat_cfg,
            world_aut=0.0,
            injuries=player_injuries,
            second_wind_uses=recovery_cfg.second_wind.uses_per_match,
            weapon_id=ai_cfg.player_default_weapon,
            ferocity=5,
            cunning=5,
            tenacity=5,
            appetite=0,
            vore_capable=False,
        ),
    }
    for e, entity_id in zip(enemies, spawn_plan):
        scheduler.register(e)
        ov = ai_cfg.entity_attr_overrides.get(entity_id, {})
        fer, cun, ten, app, wep, abs_ = roll_attrs(
            rng, overrides=ov, defaults=ai_cfg.default_entity_attrs
        )
        if not wep:
            wep = default_weapon_for_entity(entity_id)
        # Seed abilities for AI with any cunning
        seed_abs = abs_ or ("haymaker", "shield_push", "hook_shield")
        combatants[e] = CombatantState.from_fighter(
            e.components[Fighter],
            combat_cfg,
            world_aut=0.0,
            weapon_id=wep,
            ferocity=fer,
            cunning=cun,
            tenacity=ten,
            appetite=app,
            ability_ids=tuple(seed_abs) if cun > 0 else (),
            vore_capable=True,
        )
    for e, rec in zip(ally_entities, to_deploy):
        scheduler.register(e)
        ov = ai_cfg.entity_attr_overrides.get(rec.species_id, {})
        fer, cun, ten, app, wep, abs_ = roll_attrs(
            rng, overrides=ov, defaults=ai_cfg.default_entity_attrs
        )
        if not wep:
            wep = default_weapon_for_entity(rec.species_id)
        combatants[e] = CombatantState.from_fighter(
            e.components[Fighter],
            combat_cfg,
            world_aut=0.0,
            injuries=injuries_from_dicts(rec.injuries),
            second_wind_uses=0,
            weapon_id=wep,
            ferocity=fer,
            cunning=cun,
            tenacity=ten,
            appetite=app,
            ability_ids=tuple(abs_) if abs_ else (),
            vore_capable=False,  # beast flag later; default steel allies
        )

    log = MessageLog()
    log.add(
        f"Match: {card.title} [{card.kind_label}]",
        category=MessageCategory.CAUTION,
    )
    log.add(
        "Move/bump, ctrl+dir attack, f footwork, . keep watch, d brace, a abilities, T talk.",
        category=MessageCategory.ROUTINE,
    )
    if player_injuries:
        log.add(
            "Carrying: " + "; ".join(format_injury_list(player_injuries)),
            category=MessageCategory.CAUTION,
        )
    if ally_entities:
        names = ", ".join(
            e.components[DisplayName].name for e in ally_entities if DisplayName in e.components
        )
        log.add(f"Allies: {names}", category=MessageCategory.POSITIVE)

    patron_obj = assign_patron_objective(
        card_kind=card.kind,
        has_deployed_allies=bool(ally_entities),
        rng=rng,
    )
    if patron_obj is not None:
        log.add(
            f"Patron: {patron_obj.short_line()}",
            category=MessageCategory.CAUTION,
        )

    vore_cfg = load_vore_config()
    crowd_cfg = load_crowd_config()
    session = MatchSession(
        career=career,
        card=card,
        world=world,
        game_map=game_map,
        player=player,
        enemies=enemies,
        message_log=log,
        rng=rng,
        scheduler=scheduler,
        costs=costs,
        combat_cfg=combat_cfg,
        recovery_cfg=recovery_cfg,
        vore_cfg=vore_cfg,
        combatants=combatants,
        ai_cfg=ai_cfg,
        ally_entities=ally_entities,
        ally_id_by_entity=ally_id_by_entity,
        ally_order=ally_order,
        patron_objective=patron_obj,
        crowd_cfg=crowd_cfg,
        crowd=CrowdState(favor=crowd_cfg.start_favor),
        difficulty=diff,
    )
    session.process_npc_until_player()
    return session


def _sign(v: int) -> int:
    if v > 0:
        return 1
    if v < 0:
        return -1
    return 0


def _key_to_letter(sym: KeySym) -> str | None:
    # tcod KeySym letter values align with ord for a-z in many builds; use name.
    name = getattr(sym, "name", "") or str(sym)
    if name.startswith("KeySym."):
        name = name.split(".", 1)[-1]
    if len(name) == 1 and name.isalpha():
        return name.lower()
    # FALLBACK: numeric value
    try:
        code = int(sym)
        if ord("a") <= code <= ord("z"):
            return chr(code)
        if ord("A") <= code <= ord("Z"):
            return chr(code).lower()
    except (TypeError, ValueError):
        pass
    return None


def render_match(
    console: tcod.console.Console,
    session: MatchSession,
) -> None:
    """Draw **only** map tiles + entity glyphs (fixed-width). All other UI is log-font via present."""
    console.clear()
    if session.phase is MatchPhase.RECAP:
        return
    if session.ability_ui is AbilityUiMode.FULL_LIST:
        return
    render_map(console, session.game_map)
    apply_grapple_tile_highlights(
        console,
        grapple=session.grapple,
        is_ally=session.is_ally,
    )
    # Footwork targeting: legal landings cyan, cursor bright white
    if session.footwork_targeting:
        pos = session.player.components.get(Position)
        legal = session._footwork_legal_tiles()
        legal_set = {(p.x, p.y) for p in legal}
        for lx, ly in legal_set:
            paint_tile_bg(console, lx, ly, (40, 90, 120))
        cur = session.footwork_cursor
        if cur is not None:
            if (cur.x, cur.y) in legal_set:
                paint_tile_bg(console, cur.x, cur.y, (220, 240, 255))
            else:
                paint_tile_bg(console, cur.x, cur.y, (180, 100, 60))
        if pos is not None:
            # faint mark on player origin
            paint_tile_bg(console, pos.x, pos.y, (60, 60, 90))
    draw_match_entities(console, session)


def match_footer_text(session: MatchSession) -> str:
    if session.phase is MatchPhase.RECAP:
        return "Enter: continue"
    if session.ability_ui is AbilityUiMode.FULL_LIST:
        return "Enter/Esc: close"
    if session.talk_ui is TalkUiMode.PICK_ALLY:
        return "1/2… ally  |  0 all  |  Esc: cancel"
    if session.talk_ui is TalkUiMode.PICK_ORDER:
        return "1 Attack!  |  2 Help me!  |  3 Stay close!  |  Esc: back"
    # Grapple owns the footer while PC is held (no reaction stack)
    g = session.grapple
    if g is not None and g.prey is session.player:
        surr = "  |  G: surrender" if session.card.kind == "green" else ""
        if g.phase is VorePhase.ENGULFED:
            return f"Engulfed: . or move thrash (low odds){surr}  |  Ctrl+Q"
        if g.phase is VorePhase.SWALLOW:
            # Swallow modal owns chrome — keep footer to choices only (no Ctrl+Q noise)
            return match_swallow_options_line()
        return f"Grappled: 1 Break away  |  2 Counter  |  . brace{surr}  |  Ctrl+Q"
    if session.pending_reaction is not None:
        if session.pending_reaction.awaiting_dodge_dir:
            return "Dodge: press direction into an open tile  |  Esc: cancel"
        return "1 Dodge  |  2 Parry/Block  |  3 Counter  |  4 Ignore"
    if session.ability_ui is AbilityUiMode.PICK_LETTER:
        return "Letter: use ability  |  ? list  |  Esc: cancel"
    if session.footwork_targeting:
        return (
            "Footwork: arrows move cursor (1–2 tiles)  |  Enter: confirm  |  Esc: cancel"
        )
    if session.combatants.get(session.player) and session.combatants[session.player].downed:
        base = (
            "Crawl: move  |  . rest  |  a: Recover when bar full  |  "
            f"{session.recovery_cfg.second_wind.letter}: Second Wind"
        )
        if session.card.kind == "green":
            base += "  |  G: surrender"
        return base + "  |  Ctrl+Q"
    base = (
        "Move/bump  |  ctrl+dir attack  |  f footwork  |  . watch  |  d brace  |  "
        "a abilities  |  T talk  |  s Second Wind"
    )
    if session.card.kind == "green":
        base += "  |  G: surrender"
    return base + "  |  Ctrl+Q"


def _match_palette() -> dict[str, tuple[int, int, int]]:
    from src.ui.help_overlay import HELP_BODY_FG, HELP_SECTION_FG, HELP_TITLE_FG

    return {
        "body": HELP_BODY_FG,
        "title": HELP_TITLE_FG,
        "section": HELP_SECTION_FG,
        "dim": (160, 160, 170),
        "meter": (180, 220, 255),
        "green": (120, 220, 140),
        "red": (240, 120, 100),
        "gold": (220, 200, 120),
        "injury": (255, 200, 120),
    }


def match_fullscreen_text_lines(session: MatchSession) -> tuple:
    """Recap or full ability list (full-screen log-font panels)."""
    from src.ui.help_overlay import HelpTextLine

    pal = _match_palette()
    body, title, section = pal["body"], pal["title"], pal["section"]

    if session.phase is MatchPhase.RECAP:
        lines: list = []
        for i, line in enumerate(session.recap_lines):
            lines.append(HelpTextLine(line, title if i == 0 else body))
        return tuple(lines)

    if session.ability_ui is AbilityUiMode.FULL_LIST:
        lines = [HelpTextLine("ABILITIES", title), HelpTextLine("", body)]
        for ab in session.combat_cfg.abilities:
            lines.append(
                HelpTextLine(
                    f"{ab.letter}) {ab.name}  —  AP {ab.ap_cost}  AUT {ab.aut_cost:.1f}",
                    section,
                )
            )
            lines.append(HelpTextLine(ab.description, body))
            lines.append(HelpTextLine("", body))
        return tuple(lines)

    return ()


def match_status_lines(session: MatchSession) -> tuple:
    """Right-of-map status: meters, card meta, grapple/talk/ability prompts (no log, no reaction)."""
    from src.ui.help_overlay import HelpTextLine

    if session.phase is not MatchPhase.FIGHT:
        return ()
    if session.ability_ui is AbilityUiMode.FULL_LIST:
        return ()

    pal = _match_palette()
    body = pal["body"]
    title = pal["title"]
    dim = pal["dim"]
    meter_fg = pal["meter"]
    green = pal["green"]
    red = pal["red"]
    orange = (240, 160, 70)

    session._sync_ap()
    pf = session.player.components[Fighter]
    pc = session.combatants[session.player]
    kind_fg = green if session.card.kind == "green" else red
    lines: list = [
        HelpTextLine(
            f"HP {pf.hp}/{pf.max_hp}    AUT {session.scheduler.world_aut:.1f}",
            body,
        ),
        HelpTextLine(
            f"[{session.card.kind_label}] {session.card.title}",
            kind_fg,
        ),
    ]
    if session.patron_objective is not None:
        lines.append(
            HelpTextLine(
                session.patron_objective.short_line(),
                pal["gold"],
            )
        )
    lines.append(
        HelpTextLine(
            f"Crowd {session.crowd.favor}  |  Diff: {session.difficulty.label}",
            dim,
        )
    )
    if pc.downed:
        lines.append(
            HelpTextLine(
                f"DOWN  Recovery {format_recovery_meter(pc.recovery_bar, session.recovery_cfg.recovery_bar_full)}  "
                f"(a: stand when full  |  {session.recovery_cfg.second_wind.letter}: Second Wind)",
                red,
            )
        )
    else:
        lines.append(
            HelpTextLine(
                f"AP {pc.ap:.0f}/{pc.ap_max:.0f}  {format_ap_meter(pc.ap, pc.ap_max)}",
                meter_fg,
            )
        )
    lines.append(
        HelpTextLine(
            f"Bal {format_balance_meter(pc.balance, lo=session.combat_cfg.balance_min, hi=session.combat_cfg.balance_max)}",
            meter_fg,
        )
    )
    # Balance-driven actual-stat deltas (buffs green, debuffs orange)
    for label, val, is_buff in balance_stat_deltas(pc, session.combat_cfg):
        is_ac = label == "AC"
        text = format_balance_effect_line(label, val, is_ac=is_ac)
        lines.append(HelpTextLine(text, green if is_buff else orange))
    if pc.injuries:
        lines.append(
            HelpTextLine("; ".join(format_injury_list(pc.injuries)), pal["injury"])
        )
    if session.footwork_targeting and session.footwork_cursor is not None:
        cur = session.footwork_cursor
        pos = session.player.components[Position]
        dx, dy = cur.x - pos.x, cur.y - pos.y
        legal = is_footwork_offset(
            dx, dy, max_chebyshev=session._footwork_max_chebyshev()
        ) and any(p.x == cur.x and p.y == cur.y for p in session._footwork_legal_tiles())
        tip = "legal — Enter" if legal else "not a legal landing"
        lines.append(
            HelpTextLine(f"Footwork cursor ({cur.x},{cur.y}) — {tip}", title)
        )

    g = session.grapple
    if g is not None:
        # PC-held grapple/swallow owned by dedicated modals (not status chrome).
        # Engulfed stays a short status note; ally-as-prey stays here for rescuer awareness.
        if g.prey is session.player:
            if g.phase is VorePhase.ENGULFED:
                lines.append(HelpTextLine("", body))
                need = effective_digest_strikes_to_end(
                    session.vore_cfg, conserved_strength=g.conserved_strength
                )
                lines.append(
                    HelpTextLine(
                        f"ENGULFED  Digest {g.digest_strikes}/{need}  — thrash (. or move)",
                        red,
                    )
                )
        else:
            lines.append(HelpTextLine("", body))
            phase_label = {
                VorePhase.GRAPPLE: "GRAPPLE",
                VorePhase.SWALLOW: "SWALLOWING",
                VorePhase.ENGULFED: "ENGULFED",
            }.get(g.phase, "GRAPPLE")
            prey_nm = (
                g.prey.components[DisplayName].name
                if isinstance(g.prey, Entity) and DisplayName in g.prey.components
                else "ally"
            )
            lines.append(
                HelpTextLine(f"{phase_label} — {prey_nm} is held!", title)
            )
            if g.phase is VorePhase.GRAPPLE:
                lines.append(
                    HelpTextLine(
                        f"Grapple HP {g.grapple_hp}/{g.grapple_hp_max}  "
                        "(hit the predator to force release)",
                        red,
                    )
                )

    if session.talk_ui is TalkUiMode.PICK_ALLY:
        lines.append(HelpTextLine("", body))
        lines.append(HelpTextLine("TALK — Who?", title))
        for i, e in enumerate(session.living_allies()):
            nm = (
                e.components[DisplayName].name
                if DisplayName in e.components
                else f"Ally {i + 1}"
            )
            aid = session.ally_id_by_entity.get(e, "")
            order = session.ally_order.get(aid, "attack")
            lines.append(HelpTextLine(f"{i + 1}) {nm}  (now: {order})", body))
        lines.append(HelpTextLine("0) All allies", body))
    elif session.talk_ui is TalkUiMode.PICK_ORDER:
        lines.append(HelpTextLine("", body))
        lines.append(HelpTextLine("TALK — Order?", title))
        lines.append(HelpTextLine("1) Attack (aggressive)", body))
        lines.append(HelpTextLine("2) Defend (stay near you)", body))
    if session.ability_ui is AbilityUiMode.PICK_LETTER:
        lines.append(HelpTextLine("", body))
        lines.append(
            HelpTextLine(
                "Ability: press letter (a/b/c), or ? for list — Esc cancel",
                title,
            )
        )
    return tuple(lines)


def match_log_lines(session: MatchSession, *, max_lines: int = MATCH_LOG_MAX_LINES) -> tuple:
    """Bottom action log only (recent message_log entries)."""
    from src.ui.help_overlay import HelpTextLine

    if session.phase is not MatchPhase.FIGHT:
        return ()
    if session.ability_ui is AbilityUiMode.FULL_LIST:
        return ()
    body = _match_palette()["body"]
    entries = session.message_log.entries()[-max_lines:]
    return tuple(HelpTextLine(e.text, body) for e in entries)


def match_reaction_modal_lines(session: MatchSession) -> tuple | None:
    """Incoming-attack modal content, or None when inactive / PC grappled."""
    from src.ui.help_overlay import HelpTextLine

    if session.phase is not MatchPhase.FIGHT:
        return None
    g = session.grapple
    pc_held = g is not None and g.prey is session.player
    if session.pending_reaction is None or pc_held:
        return None

    pal = _match_palette()
    body = pal["body"]
    title = pal["title"]
    section = pal["section"]
    red = pal["red"]
    pr = session.pending_reaction
    lines: list = [
        HelpTextLine("INCOMING!", title),
        HelpTextLine(pr.announce, red),
        HelpTextLine("", body),
    ]
    if pr.awaiting_dodge_dir:
        lines.append(
            HelpTextLine(
                "Dodge which way? (8 directions — must be open)",
                section,
            )
        )
    else:
        lines.append(HelpTextLine("1  Dodge (then direction)", body))
        lines.append(HelpTextLine("2  Parry / Block", body))
        lines.append(HelpTextLine("3  Counterattack", body))
        lines.append(HelpTextLine("4  Ignore", body))
    return tuple(lines)


def match_grapple_modal_lines(session: MatchSession) -> tuple | None:
    """Red low-right grapple crisis modal (PC prey, GRAPPLE phase only; stub)."""
    from src.ui.help_overlay import HelpTextLine

    if session.phase is not MatchPhase.FIGHT:
        return None
    g = session.grapple
    if g is None or g.prey is not session.player or g.phase is not VorePhase.GRAPPLE:
        return None

    pal = _match_palette()
    body = pal["body"]
    title = pal["title"]
    red = pal["red"]
    pred = g.predator
    pname = (
        entity_log_name(pred, sentence_start=True)  # type: ignore[arg-type]
        if isinstance(pred, Entity)
        else "The predator"
    )
    return (
        HelpTextLine(msg.predator_grapples_you(pname), title),
        HelpTextLine(f"Grapple HP {g.grapple_hp}/{g.grapple_hp_max}", red),
        HelpTextLine("", body),
        HelpTextLine("1  Break away", body),
        HelpTextLine("2  Counter-strike", body),
        HelpTextLine(".  Brace", body),
    )


def match_swallow_narrative_text(session: MatchSession) -> str | None:
    """Phase narrative only — progress is implied by which snippet shows."""
    if session.phase is not MatchPhase.FIGHT:
        return None
    g = session.grapple
    if g is None or g.prey is not session.player or g.phase is not VorePhase.SWALLOW:
        return None
    return swallow_narrative_line(
        session.vore_cfg, phase_index=g.swallow_phase_index
    )


def match_swallow_options_line() -> str:
    """Single-line choices; no explanations."""
    return "1 - struggle | 2 - conserve strength | 3 - call for help"


def match_swallow_modal_lines(session: MatchSession) -> tuple | None:
    """Minimal swallow modal payload: narrative + one options line (for tests/CP437)."""
    from src.ui.help_overlay import HelpTextLine

    narrative = match_swallow_narrative_text(session)
    if narrative is None:
        return None
    pal = _match_palette()
    return (
        HelpTextLine(narrative, pal["body"]),
        HelpTextLine("", pal["body"]),
        HelpTextLine(match_swallow_options_line(), pal["section"]),
    )


def match_low_right_crisis_lines(session: MatchSession) -> tuple | None:
    """Low-right red panel: reaction or grapple (not swallow)."""
    reaction = match_reaction_modal_lines(session)
    if reaction is not None:
        return reaction
    return match_grapple_modal_lines(session)


def match_text_lines(session: MatchSession) -> tuple:
    """Compatibility aggregate: fullscreen text, or status+reaction+log for fight."""
    from src.ui.help_overlay import HelpTextLine

    full = match_fullscreen_text_lines(session)
    if full:
        return full
    body = _match_palette()["body"]
    parts: list = list(match_status_lines(session))
    crisis = match_low_right_crisis_lines(session)
    if crisis:
        parts.append(HelpTextLine("", body))
        parts.extend(crisis)
    swallow = match_swallow_modal_lines(session)
    if swallow:
        parts.append(HelpTextLine("", body))
        parts.extend(swallow)
    parts.append(HelpTextLine("", body))
    parts.extend(match_log_lines(session))
    return tuple(parts)


def render_match_cp437_fallback(
    console: tcod.console.Console,
    session: MatchSession,
) -> None:
    """Full CP437 draw when log font is unavailable (map + regional text)."""
    from src.match_hud_layout import match_hud_bands
    from src.ui.help_overlay import HelpTextLine

    render_match(console, session)
    if session.phase is MatchPhase.RECAP or session.ability_ui is AbilityUiMode.FULL_LIST:
        console.clear()
        y = 1
        for entry in match_fullscreen_text_lines(session):
            if not isinstance(entry, HelpTextLine):
                continue
            if y >= console.height - 2:
                break
            if entry.text:
                console.print(
                    2,
                    y,
                    cp437_safe(entry.text[: console.width - 4]),
                    fg=entry.fg,
                )
            y += 1
    elif session.phase is MatchPhase.FIGHT:
        swallow_narrative = match_swallow_narrative_text(session)
        if swallow_narrative is not None:
            # CP437: keep map; overlay a compact centered panel
            max_w = min(50, console.width - 4)
            words = swallow_narrative.split()
            narr_lines: list[str] = []
            cur = ""
            for w in words:
                trial = f"{cur} {w}".strip()
                if len(trial) <= max_w - 2:
                    cur = trial
                else:
                    if cur:
                        narr_lines.append(cur)
                    cur = w
            if cur:
                narr_lines.append(cur)
            panel_h = min(8, 2 + len(narr_lines[:3]) + 3)
            panel_w = max_w
            px = max(0, (console.width - panel_w) // 2)
            py = max(1, (console.height - panel_h) // 2)
            for row in range(panel_h):
                console.print(
                    px,
                    py + row,
                    " " * panel_w,
                    bg=(48, 28, 32),
                )
            y = py + 1  # top padding inside panel
            for line in narr_lines[:3]:
                x = px + max(1, (panel_w - len(line)) // 2)
                console.print(x, y, cp437_safe(line[: panel_w - 2]), fg=(235, 210, 205))
                y += 1
            opt = match_swallow_options_line()
            ox = px + max(1, (panel_w - len(opt)) // 2)
            console.print(
                ox,
                py + panel_h - 2,
                cp437_safe(opt[: panel_w - 2]),
                fg=(180, 180, 190),
            )
        else:
            crisis_lines = match_low_right_crisis_lines(session)
            bands = match_hud_bands(
                map_w=session.game_map.width,
                map_h=session.game_map.height,
                root_w=console.width,
                root_h=console.height,
                reaction_active=crisis_lines is not None,
            )
            # Status — right of map
            y = bands.status.y
            for entry in match_status_lines(session):
                if y >= bands.status.y + bands.status.h:
                    break
                if entry.text:
                    console.print(
                        bands.status.x,
                        y,
                        cp437_safe(entry.text[: bands.status.w]),
                        fg=entry.fg,
                    )
                y += 1
            # Action log — bottom
            y = bands.log.y
            for entry in match_log_lines(session):
                if y >= bands.log.y + bands.log.h:
                    break
                if entry.text:
                    console.print(
                        bands.log.x,
                        y,
                        cp437_safe(entry.text[: bands.log.w]),
                        fg=entry.fg,
                    )
                y += 1
            # Reaction / grapple modal — low-right
            if crisis_lines is not None and bands.reaction is not None:
                y = bands.reaction.y
                for entry in crisis_lines:
                    if y >= bands.reaction.y + bands.reaction.h:
                        break
                    if entry.text:
                        console.print(
                            bands.reaction.x,
                            y,
                            cp437_safe(entry.text[: bands.reaction.w]),
                            fg=entry.fg,
                        )
                    y += 1
    console.print(
        0,
        console.height - 1,
        cp437_safe(match_footer_text(session)[: console.width]),
        fg=(140, 140, 140),
    )
