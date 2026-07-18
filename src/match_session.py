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
    awareness_openness,
    choose_bump_profile,
    format_ap_meter,
    format_balance_meter,
    format_recovery_meter,
    load_match_combat_config,
    step_aut_multiplier,
)
from src.match_recovery import RecoveryConfig, load_recovery_config
from src.match_vore import (
    GrappleState,
    VoreConfig,
    VorePhase,
    break_away_chance,
    grab_chance,
    load_vore_config,
    pick_flaunt,
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
from src.roster import AllyRecord, deployed_allies, load_roster_tuning, remove_ally_digest
from src.match_spawn import spawn_match_entity
from src.match_combat_resolve import resolve_attack
from src.match_movement import can_entity_enter_tile
from src.match_naming import entity_log_name
from src.match_render import render_map
from src.text import cp437_safe

_WAIT_KEYS = frozenset({KeySym.PERIOD, KeySym.KP_5, KeySym.SPACE})
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
    ally_order: dict[str, str] = attrs.field(factory=dict)  # ally_id -> attack|defend
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

    def _sync_ap(self) -> None:
        t = self.scheduler.world_aut
        rc = self.recovery_cfg
        for ent, state in list(self.combatants.items()):
            prev = state.last_world_aut
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
                if sym in _WAIT_KEYS or sym in DIRECTION_KEYS:
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

        if sym in DIRECTION_KEYS:
            dx, dy = DIRECTION_KEYS[sym]
            self.recent_dodges = 0
            self._player_bump(dx, dy)
            return False
        if sym in _WAIT_KEYS:
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
        cst = self.combatants[self.player]
        man = self.combat_cfg.maneuver("wait")
        if cst.downed:
            # Holding while down still fills recovery (via AUT commit)
            self.scheduler.commit_action(self.player, man.aut_cost)
            self.message_log.add(
                "You catch your breath in the sand.",
                category=MessageCategory.ROUTINE,
            )
            self.awaiting_player = False
            self.process_npc_until_player()
            return
        cst.shift_balance(man.balance_delta, self.combat_cfg)
        self.scheduler.commit_action(self.player, man.aut_cost)
        self.message_log.add(
            "You brace and wait.",
            category=MessageCategory.ROUTINE,
        )
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
            elif sym in (KeySym.N2, KeySym.KP_2, KeySym.D):
                order = "defend"
            if order is None:
                return
            self._issue_orders(order)
            self.talk_ui = TalkUiMode.CLOSED

    def _issue_orders(self, order: str) -> None:
        """Apply Attack/Defend; Free Talk 0 AUT once per 1.0 AUT, else AP+turn."""
        names: list[str] = []
        for aid in self.talk_target_ids:
            self.ally_order[aid] = order
            # Sync order onto career roster copy
            allies = self.career.allies()
            for a in allies:
                if a.ally_id == aid:
                    a.order = order
                    names.append(a.name)
            self.career.set_allies(allies)
        label = "Attack!" if order == "attack" else "Defend me!"
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
        aid = self.ally_id_by_entity.get(entity, "")
        order = self.ally_order.get(aid, "attack")
        cst = self.combatants.get(entity)
        enemies = self.living_enemies()
        if not enemies:
            if cst:
                cst.shift_balance(self.combat_cfg.balance_on_wait, self.combat_cfg)
            self.scheduler.commit_action(entity, self.costs.wait)
            return
        pos = entity.components[Position]
        player_pos = self.player.components[Position]

        # During a grapple, rescuers prefer the big target (the predator)
        g = self.grapple
        pred = g.predator if g is not None else None
        if isinstance(pred, Entity) and pred in enemies:
            if chebyshev(pos, pred.components[Position]) == 1:
                if cst:
                    cst.shift_balance(self.combat_cfg.balance_on_attack, self.combat_cfg)
                self._melee(
                    entity,
                    pred,
                    cost=self.costs.standard_attack,
                    apply_push=True,
                )
                return

        # Prefer adjacent enemy always
        adjacent = [
            e
            for e in enemies
            if chebyshev(pos, e.components[Position]) == 1
        ]
        if adjacent:
            # Prefer predator among adjacent when grappling an ally/PC
            if isinstance(pred, Entity) and pred in adjacent:
                target = pred
            else:
                target = min(
                    adjacent,
                    key=lambda e: e.components[Fighter].hp,
                )
            if cst:
                cst.shift_balance(self.combat_cfg.balance_on_attack, self.combat_cfg)
            self._melee(
                entity,
                target,
                cost=self.costs.standard_attack,
                apply_push=True,
            )
            return

        if order == "defend":
            # Stay near player; step closer if far
            dist = chebyshev(pos, player_pos)
            if dist <= 1:
                if cst:
                    cst.shift_balance(self.combat_cfg.balance_on_wait, self.combat_cfg)
                self.scheduler.commit_action(entity, self.costs.wait)
                return
            dx = _sign(player_pos.x - pos.x)
            dy = _sign(player_pos.y - pos.y)
        else:
            # Attack: move toward predator if grappling, else nearest enemy
            if isinstance(pred, Entity) and pred in enemies:
                target = pred
            else:
                target = min(
                    enemies,
                    key=lambda e: chebyshev(pos, e.components[Position]),
                )
            tp = target.components[Position]
            dx = _sign(tp.x - pos.x)
            dy = _sign(tp.y - pos.y)

        tx, ty = pos.x + dx, pos.y + dy
        if self._blocker_at(tx, ty) is None and can_entity_enter_tile(
            self.game_map, tx, ty, entity
        ):
            entity.components[Position] = Position(tx, ty)
            if cst:
                cst.shift_balance(self.combat_cfg.balance_on_step, self.combat_cfg)
            self.scheduler.commit_action(entity, self.costs.step)
        else:
            if cst:
                cst.shift_balance(self.combat_cfg.balance_on_wait, self.combat_cfg)
            self.scheduler.commit_action(entity, self.costs.wait)

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
            cst.shift_balance(man.balance_delta, self.combat_cfg)
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
        self._melee(
            self.player,
            target,
            cost=man.aut_cost,
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
        """PC options while grappled (not yet engulfed): 1 break away, 2 counter."""
        g = self.grapple
        assert g is not None and g.prey is self.player
        if g.phase is VorePhase.SWALLOW:
            # During swallow, thrash is low-value; still may break rarely
            if sym in _WAIT_KEYS or sym in DIRECTION_KEYS or sym in _REACT_DODGE:
                self._prey_break_away(spend_aut=True)
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
                "You brace in their grip.",
                category=MessageCategory.ROUTINE,
            )
            self.awaiting_player = False
            self.process_npc_until_player()

    def _prey_break_away(self, *, spend_aut: bool) -> None:
        g = self.grapple
        assert g is not None
        cfg = self.vore_cfg
        chance = break_away_chance(
            grapple_hp=g.grapple_hp,
            grapple_hp_max=g.grapple_hp_max,
            cfg=cfg,
        )
        if g.phase is VorePhase.SWALLOW:
            chance *= 0.35
        if spend_aut:
            self.scheduler.commit_action(g.prey, cfg.break_away_aut)
        if self.rng.random() < chance:
            self.message_log.add(
                "You wrench free!",
                category=MessageCategory.POSITIVE,
            )
            self._end_grapple(released=True)
        else:
            self.message_log.add(
                "You struggle, but the grip holds.",
                category=MessageCategory.CAUTION,
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
        """Ally held: auto attempt break-away."""
        g = self.grapple
        assert g is not None
        cfg = self.vore_cfg
        chance = break_away_chance(
            grapple_hp=g.grapple_hp,
            grapple_hp_max=max(1, g.grapple_hp_max),
            cfg=cfg,
        )
        self.scheduler.commit_action(entity, cfg.break_away_aut)
        name = (
            entity.components[DisplayName].name
            if DisplayName in entity.components
            else "Ally"
        )
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
        # Co-locate prey on predator for display
        if Position in predator.components and Position in prey.components:
            pp = predator.components[Position]
            prey.components[Position] = Position(pp.x, pp.y)
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
        self.grapple = None

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
            self.message_log.add(
                f"Digestion presses in… ({g.digest_strikes}/{cfg.digest_strikes_to_end})",
                category=MessageCategory.DANGER,
            )
            prey_f = prey.components.get(Fighter)
            if prey_f is not None and prey_f.hp > 0:
                prey_f.hp = max(0, prey_f.hp - 2)
            if g.digest_strikes >= cfg.digest_strikes_to_end:
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
        # Miss only — no bonus; still record the attempt
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
            "Press Enter to return to the main menu.",
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
        # Prefer soft targets: downed PC, then PC, then nearest ally —
        # but never poke an obscured grapple prey (other predator's catch).
        targets: list[Entity] = []
        pf = self.player.components.get(Fighter)
        if pf is not None and not self._is_obscured_prey(self.player):
            targets.append(self.player)
        for ally in self.living_allies():
            if not self._is_obscured_prey(ally):
                targets.append(ally)
        if not targets:
            # Hesitate: won't risk jabbing into another predator's grapple
            cst = self.combatants.get(entity)
            if cst:
                cst.shift_balance(self.combat_cfg.balance_on_wait, self.combat_cfg)
            self.scheduler.commit_action(entity, self.costs.wait)
            return

        pos = entity.components[Position]
        # Score: prefer adjacent, then downed
        def score(t: Entity) -> tuple[int, int, int]:
            tp = t.components[Position]
            dist = chebyshev(pos, tp)
            st = self.combatants.get(t)
            down = 0 if (st and st.downed) or (
                t.components.get(Fighter) and t.components[Fighter].hp <= 0
            ) else 1
            is_pc = 0 if Player in t.tags else 1
            return (dist, down, is_pc)

        target = min(targets, key=score)
        player_pos = target.components[Position]
        dx = _sign(player_pos.x - pos.x)
        dy = _sign(player_pos.y - pos.y)
        cst = self.combatants.get(entity)
        if dx == 0 and dy == 0:
            # Same tile or already on them — grab/attack
            if self._try_enemy_grab(entity, target):
                return
            if target is self.player:
                self._npc_open_player_attack(entity)
            else:
                if cst:
                    cst.shift_balance(self.combat_cfg.balance_on_attack, self.combat_cfg)
                self._melee(
                    entity,
                    target,
                    cost=self.combat_cfg.maneuver("standard_attack").aut_cost,
                    apply_push=True,
                )
            return
        tx, ty = pos.x + dx, pos.y + dy
        if not can_entity_enter_tile(self.game_map, tx, ty, entity) and (
            self._blocker_at(tx, ty) is None
            or self._blocker_at(tx, ty) is target
        ):
            if abs(player_pos.x - pos.x) >= abs(player_pos.y - pos.y):
                tx, ty = pos.x + dx, pos.y
            else:
                tx, ty = pos.x, pos.y + dy

        blocker = self._blocker_at(tx, ty)
        if blocker is target or (
            blocker is not None and chebyshev(pos, target.components[Position]) == 1
        ):
            if chebyshev(pos, target.components[Position]) > 1 and blocker is None:
                pass
            else:
                # Adjacent: grab or attack
                if chebyshev(pos, target.components[Position]) <= 1:
                    if self._try_enemy_grab(entity, target):
                        return
                    if target is self.player:
                        self._npc_open_player_attack(entity)
                        return
                    if cst:
                        cst.shift_balance(
                            self.combat_cfg.balance_on_attack,
                            self.combat_cfg,
                        )
                    self._melee(
                        entity,
                        target,
                        cost=self.combat_cfg.maneuver("standard_attack").aut_cost,
                        apply_push=True,
                    )
                    return
        if blocker is None and can_entity_enter_tile(self.game_map, tx, ty, entity):
            entity.components[Position] = Position(tx, ty)
            if cst:
                cst.shift_balance(self.combat_cfg.balance_on_step, self.combat_cfg)
            self.scheduler.commit_action(entity, self.costs.step)
            return
        # Adjacent fallback
        if chebyshev(pos, target.components[Position]) <= 1:
            if self._try_enemy_grab(entity, target):
                return
            if target is self.player:
                self._npc_open_player_attack(entity)
                return
        if cst:
            cst.shift_balance(self.combat_cfg.balance_on_wait, self.combat_cfg)
        self.scheduler.commit_action(entity, self.costs.wait)

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
        self.gold_delta = gold
        self.renown_delta = renown
        self.career.gold += gold
        self.career.renown += renown
        self.career.round_index += 1
        patron_lines = self._apply_patron_settlement(end_kind="surrender")
        crowd_lines = self._apply_crowd_settlement(end_kind="surrender")
        notes = tuple(self.digest_notes) if self.digest_notes else ()
        pct = int(round(frac * 100))
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
            "Press Enter to return to downtime.",
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
        self.gold_delta = gold
        self.renown_delta = renown
        self.career.gold += gold
        self.career.renown += renown
        self.career.round_index += 1
        patron_lines = self._apply_patron_settlement(end_kind="win")
        crowd_lines = self._apply_crowd_settlement(end_kind="win")
        notes = tuple(self.digest_notes) if self.digest_notes else ()
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
            "Press Enter to return to downtime.",
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
        self.gold_delta = gold
        self.renown_delta = renown
        self.career.gold += gold
        self.career.renown += renown
        self.career.round_index += 1
        patron_lines = self._apply_patron_settlement(end_kind="loss")
        crowd_lines = self._apply_crowd_settlement(end_kind="loss")
        notes = tuple(self.digest_notes) if self.digest_notes else ()
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
            "Press Enter to return to downtime.",
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

    # Deployed allies (PC + up to card max / career max)
    tuning = load_roster_tuning()
    max_dep = min(career.max_deployed_allies, card.max_allies, tuning.max_deployed_allies)
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
    combatants: dict[object, CombatantState] = {
        player: CombatantState.from_fighter(
            player.components[Fighter],
            combat_cfg,
            world_aut=0.0,
            injuries=player_injuries,
            second_wind_uses=recovery_cfg.second_wind.uses_per_match,
        ),
    }
    for e in enemies:
        scheduler.register(e)
        combatants[e] = CombatantState.from_fighter(
            e.components[Fighter],
            combat_cfg,
            world_aut=0.0,
        )
    for e, rec in zip(ally_entities, to_deploy):
        scheduler.register(e)
        combatants[e] = CombatantState.from_fighter(
            e.components[Fighter],
            combat_cfg,
            world_aut=0.0,
            injuries=injuries_from_dicts(rec.injuries),
            second_wind_uses=0,
        )

    log = MessageLog()
    log.add(
        f"Match: {card.title} [{card.kind_label}]",
        category=MessageCategory.CAUTION,
    )
    log.add(
        "Move/bump, . wait, a abilities, T talk, s Second Wind. AP over AUT.",
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
    for entity in session.world.Q.all_of(components=[Position, Renderable]):
        pos = entity.components[Position]
        ren = entity.components[Renderable]
        if 0 <= pos.x < console.width and 0 <= pos.y < console.height:
            console.print(pos.x, pos.y, chr(ren.ch), fg=ren.fg)


def match_footer_text(session: MatchSession) -> str:
    if session.phase is MatchPhase.RECAP:
        return "Enter: continue"
    if session.ability_ui is AbilityUiMode.FULL_LIST:
        return "Enter/Esc: close"
    if session.talk_ui is TalkUiMode.PICK_ALLY:
        return "1/2… ally  |  0 all  |  Esc: cancel"
    if session.talk_ui is TalkUiMode.PICK_ORDER:
        return "1 Attack  |  2 Defend  |  Esc: back"
    # Grapple owns the footer while PC is held (no reaction stack)
    g = session.grapple
    if g is not None and g.prey is session.player:
        surr = "  |  G: surrender" if session.card.kind == "green" else ""
        if g.phase is VorePhase.ENGULFED:
            return f"Engulfed: . or move thrash (low odds){surr}  |  Ctrl+Q"
        if g.phase is VorePhase.SWALLOW:
            return f"Swallowing: 1 struggle  |  . brace{surr}  |  Ctrl+Q"
        return f"Grappled: 1 Break away  |  2 Counter  |  . brace{surr}  |  Ctrl+Q"
    if session.pending_reaction is not None:
        if session.pending_reaction.awaiting_dodge_dir:
            return "Dodge: press direction into an open tile  |  Esc: cancel"
        return "1 Dodge  |  2 Parry/Block  |  3 Counter  |  4 Ignore"
    if session.ability_ui is AbilityUiMode.PICK_LETTER:
        return "Letter: use ability  |  ? list  |  Esc: cancel"
    if session.combatants.get(session.player) and session.combatants[session.player].downed:
        base = (
            "Crawl: move  |  . rest  |  a: Recover when bar full  |  "
            f"{session.recovery_cfg.second_wind.letter}: Second Wind"
        )
        if session.card.kind == "green":
            base += "  |  G: surrender"
        return base + "  |  Ctrl+Q"
    base = "Move/bump  |  . wait  |  a abilities  |  T talk  |  s Second Wind"
    if session.card.kind == "green":
        base += "  |  G: surrender"
    return base + "  |  Ctrl+Q"


def match_text_lines(session: MatchSession) -> tuple:
    """Proportional log-font content (everything except map/glyphs)."""
    from src.ui.help_overlay import (
        HELP_BODY_FG,
        HELP_SECTION_FG,
        HELP_TITLE_FG,
        HelpTextLine,
    )

    body = HELP_BODY_FG
    title = HELP_TITLE_FG
    section = HELP_SECTION_FG
    dim = (160, 160, 170)
    meter_fg = (180, 220, 255)
    green = (120, 220, 140)
    red = (240, 120, 100)

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

    # Fight HUD + recent log
    session._sync_ap()
    pf = session.player.components[Fighter]
    pc = session.combatants[session.player]
    kind_fg = green if session.card.kind == "green" else red
    lines = [
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
                (220, 200, 120),
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
    if pc.injuries:
        lines.append(
            HelpTextLine("; ".join(format_injury_list(pc.injuries)), (255, 200, 120))
        )
    lines.append(HelpTextLine("", body))
    g = session.grapple
    pc_held = g is not None and g.prey is session.player
    if session.pending_reaction is not None and not pc_held:
        pr = session.pending_reaction
        lines.append(HelpTextLine("INCOMING!", title))
        lines.append(HelpTextLine(pr.announce, red))
        lines.append(HelpTextLine("", body))
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
        lines.append(HelpTextLine("", body))
    if g is not None:
        phase_label = {
            VorePhase.GRAPPLE: "GRAPPLE",
            VorePhase.SWALLOW: "SWALLOWING",
            VorePhase.ENGULFED: "ENGULFED",
        }.get(g.phase, "GRAPPLE")
        if g.prey is session.player:
            lines.append(HelpTextLine(f"{phase_label} — you are held!", title))
            if g.phase is VorePhase.GRAPPLE:
                lines.append(
                    HelpTextLine(
                        f"Grapple HP {g.grapple_hp}/{g.grapple_hp_max}",
                        red,
                    )
                )
                lines.append(HelpTextLine("1  Break away", body))
                lines.append(HelpTextLine("2  Counter-strike", body))
            elif g.phase is VorePhase.SWALLOW:
                lines.append(
                    HelpTextLine(
                        f"Phase {g.swallow_phase_index}/{session.vore_cfg.swallow_phases}"
                        " — struggle (1) for a slim chance",
                        red,
                    )
                )
            else:
                lines.append(
                    HelpTextLine(
                        f"Digest strikes {g.digest_strikes}/{session.vore_cfg.digest_strikes_to_end}"
                        " — thrash (. or move)",
                        red,
                    )
                )
        else:
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
        lines.append(HelpTextLine("", body))
    if session.talk_ui is TalkUiMode.PICK_ALLY:
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
        lines.append(HelpTextLine("", body))
    elif session.talk_ui is TalkUiMode.PICK_ORDER:
        lines.append(HelpTextLine("TALK — Order?", title))
        lines.append(HelpTextLine("1) Attack (aggressive)", body))
        lines.append(HelpTextLine("2) Defend (stay near you)", body))
        lines.append(HelpTextLine("", body))
    if session.ability_ui is AbilityUiMode.PICK_LETTER:
        lines.append(
            HelpTextLine(
                "Ability: press letter (a/b/c), or ? for list — Esc cancel",
                title,
            )
        )
        lines.append(HelpTextLine("", body))
    lines.append(HelpTextLine("Log", section))
    for entry in session.message_log.entries()[-8:]:
        lines.append(HelpTextLine(entry.text, body))
    return tuple(lines)


def render_match_cp437_fallback(
    console: tcod.console.Console,
    session: MatchSession,
) -> None:
    """Full CP437 draw when log font is unavailable (map + text)."""
    from src.ui.help_overlay import HelpTextLine

    render_match(console, session)
    if session.phase is MatchPhase.RECAP or session.ability_ui is AbilityUiMode.FULL_LIST:
        console.clear()
    y = 0 if session.phase is not MatchPhase.FIGHT else session.game_map.height + 1
    if session.phase is MatchPhase.FIGHT and session.ability_ui is not AbilityUiMode.FULL_LIST:
        pass
    else:
        y = 1
    for entry in match_text_lines(session):
        if not isinstance(entry, HelpTextLine):
            continue
        if y >= console.height - 2:
            break
        if entry.text:
            console.print(
                0 if session.phase is MatchPhase.FIGHT else 2,
                y,
                cp437_safe(entry.text[: console.width - 2]),
                fg=entry.fg,
            )
        y += 1
    console.print(
        0,
        console.height - 1,
        cp437_safe(match_footer_text(session)[: console.width]),
        fg=(140, 140, 140),
    )
