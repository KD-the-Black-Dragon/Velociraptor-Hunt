from __future__ import annotations

import random
from dataclasses import dataclass

from src.debug.session_log import session_log

import attrs
from tcod.ecs import Entity

from src.components import (
    Alignment,
    BlocksMovement,
    DigestionStats,
    DigestionStrikes,
    Engulfed,
    EquipState,
    Fighter,
    Inventory,
    ItemCategory,
    NPCAlignment,
    Player,
    Predator,
)
from src.game_over_ending import GameOverEnding
from src.digestion_content import (
    DIGESTION_COMPLETE_POOL,
    GOOD_PLEA_POOL,
    PLAYER_DIGESTION_MODAL,
)
from src.systems.vore_fallback import (
    GENERIC_DIGESTION_COMPLETE,
    GENERIC_OFFSCREEN_DIGEST,
    GENERIC_PLAYER_DIGESTION_MODAL,
    is_generic_vore_type,
)
from src.map_gen import GameMap
from src.message_log import MessageCategory, MessageLog
from src.systems.inventory import destroy_item_in_slot, item_registry
from src.systems.combat import sync_stunned_state
from src.systems.fov import entity_visible_to_player
from src.data.depth_scaling_config import DifficultyProfile
from src.data.narrative_index import get_narrative_index
from src.systems.naming import entity_display_name, entity_log_name, entity_type_id
from src.text import enforce_sentence_capitalization


@attrs.define
class DigestionModalState:
    phases: list[str] = attrs.field(factory=list)
    phase_index: int = 0
    predator: Entity | None = None

    @property
    def active(self) -> bool:
        return bool(self.phases)

    @property
    def line(self) -> str:
        if not self.phases:
            return ""
        return self.phases[self.phase_index]

    def open(self, predator: Entity, phases: list[str]) -> None:
        self.predator = predator
        self.phases = list(phases)
        self.phase_index = 0

    def advance(self) -> bool:
        """Advance to the next phase. Returns True when the modal is finished."""
        if self.phase_index < len(self.phases) - 1:
            self.phase_index += 1
            return False
        return True

    def reset(self) -> None:
        self.phases = []
        self.phase_index = 0
        self.predator = None


@attrs.define
class GameOverState:
    player_name: str = "Player"
    ending: GameOverEnding | None = None
    monsters_defeated: int = 0
    runes_collected: int = 0
    depth: int = 0

    @property
    def active(self) -> bool:
        return self.ending is not None

    def open(
        self,
        *,
        player_name: str,
        ending: GameOverEnding,
        monsters_defeated: int,
        runes_collected: int,
        depth: int,
        save_store: object | None = None,
        past_runs_store: object | None = None,
        macguffin_score: int | None = None,
        difficulty_id: str | None = None,
        difficulty_display: str | None = None,
        level_warped: bool = False,
    ) -> None:
        from src.past_runs.schema import PastRunRecord
        from src.past_runs.store import today_display_date

        session_log.log("Game over")
        self.player_name = player_name
        self.ending = ending
        self.monsters_defeated = monsters_defeated
        self.runes_collected = runes_collected
        self.depth = depth
        if past_runs_store is not None and not level_warped:
            past_runs_store.append(
                PastRunRecord(
                    character_name=player_name,
                    ending_kind=ending.kind,
                    ending_detail=ending.detail,
                    monsters_defeated=monsters_defeated,
                    runes_collected=runes_collected,
                    depth=depth,
                    date=today_display_date(),
                    macguffin_score=macguffin_score,
                    difficulty_id=difficulty_id,
                    difficulty_display=difficulty_display,
                )
            )
        if save_store is not None:
            save_store.delete_all()

    def reset(self) -> None:
        self.player_name = "Player"
        self.ending = None
        self.monsters_defeated = 0
        self.runes_collected = 0
        self.depth = 0


@dataclass(frozen=True)
class PlayerDigestionResult:
    open_modal: bool = False
    strike_added: bool = False


def _prey_alignment(prey: Entity) -> Alignment | None:
    alignment = prey.components.get(NPCAlignment)
    if alignment is None:
        return None
    return alignment.alignment


def _format_digestion_line(template: str, predator: Entity, prey: Entity) -> str:
    from src.text import format_narrative_template

    predator_name = entity_log_name(predator)
    prey_name = entity_log_name(prey)
    return enforce_sentence_capitalization(
        format_narrative_template(template, predator=predator_name, prey=prey_name)
    )


def _maybe_good_plea_message(
    prey: Entity,
    predator: Entity,
    game_map: GameMap,
    message_log: MessageLog,
    rng: random.Random,
) -> None:
    if _prey_alignment(prey) != Alignment.GOOD:
        return
    if not (
        entity_visible_to_player(game_map, predator)
        or entity_visible_to_player(game_map, prey)
    ):
        return
    if rng.random() >= 0.10:
        return
    template = rng.choice(GOOD_PLEA_POOL)
    message_log.add(_format_digestion_line(template, predator, prey))


def _format_player_digestion_phase(template: str, predator: Entity) -> str:
    from src.text import format_narrative_template

    predator_name = entity_log_name(predator)
    return enforce_sentence_capitalization(
        format_narrative_template(template, predator=predator_name)
    )


def player_digestion_modal_phases(
    predator: Entity,
    narrative_type: str,
    rng: random.Random,
) -> list[str]:
    """Return formatted modal phases; random variant when multiple are defined."""
    templates = get_narrative_index().pick_digestion_player_modal_phases(
        entity_type_id(predator),
        narrative_type,
        rng,
    )
    if not templates:
        if is_generic_vore_type(narrative_type):
            templates = GENERIC_PLAYER_DIGESTION_MODAL
        else:
            fallback = PLAYER_DIGESTION_MODAL.get(
                narrative_type, PLAYER_DIGESTION_MODAL["OV"]
            )
            templates = (fallback,)
    return [_format_player_digestion_phase(template, predator) for template in templates]


def player_digestion_modal_line(
    predator: Entity,
    narrative_type: str,
    rng: random.Random | None = None,
) -> str:
    """First phase only; prefer player_digestion_modal_phases for multi-phase modals."""
    import random as random_module

    phases = player_digestion_modal_phases(
        predator,
        narrative_type,
        rng or random_module.Random(),
    )
    return phases[0] if phases else ""


def apply_player_digestion_tick(
    player: Entity,
    predator: Entity,
    message_log: MessageLog | None = None,
) -> PlayerDigestionResult:
    """Digestion tick for engulfed player. Final strike opens the digestion modal."""
    stats = predator.components.get(DigestionStats)
    if stats is None:
        return PlayerDigestionResult()

    fighter = player.components.get(Fighter)
    if fighter is None:
        return PlayerDigestionResult()

    # Potion of antacid: nullify damage and strikes for the duration.
    if Player in player.tags:
        from src.systems.player_effects import has_digestion_ward

        if has_digestion_ward(player):
            return PlayerDigestionResult()

    if fighter.hp > 0:
        raw_tick = stats.damage_per_tick
        mitigated = 0
        if Player in player.tags:
            equip = player.components.get(EquipState)
            inventory = player.components.get(Inventory)
            if equip is not None and equip.worn_slot is not None and inventory is not None:
                instance = inventory.slots.get(equip.worn_slot)
                if instance is not None and instance.category == ItemCategory.ARMOR:
                    armor = item_registry().get_armor(instance.item_id)
                    mitigated = min(raw_tick, armor.digestion_ac)
                    if mitigated > 0 and instance.durability is not None:
                        instance.durability -= mitigated
                        if instance.durability <= 0 and message_log is not None:
                            destroy_item_in_slot(
                                player,
                                equip.worn_slot,
                                message_log,
                            )
        hp_loss = raw_tick - mitigated
        fighter.hp = max(0, fighter.hp - hp_loss)
        sync_stunned_state(player)
        return PlayerDigestionResult()

    strikes = player.components.get(DigestionStrikes)
    if strikes is None:
        strikes = DigestionStrikes(count=0)
        player.components[DigestionStrikes] = strikes
    strikes.count += 1

    if strikes.count >= stats.digest_time:
        return PlayerDigestionResult(open_modal=True, strike_added=True)
    return PlayerDigestionResult(strike_added=True)


def complete_player_digestion(player: Entity, predator: Entity) -> str:
    """Clear engulf state on digest and return predator display name for game over."""
    player.tags.discard(Engulfed)
    player.components.pop(DigestionStrikes, None)
    predator_state = predator.components.get(Predator)
    if predator_state is not None:
        predator_state.failed_struggles = 0
    predator.components.pop(Predator, None)
    player.tags.add(BlocksMovement)
    return entity_display_name(predator)


def complete_npc_digestion(
    predator: Entity,
    prey: Entity,
    game_map: GameMap,
    message_log: MessageLog,
    rng: random.Random,
    *,
    skip_turn_entities: set[Entity] | None = None,
    alternate_cv_mechanics: bool = False,
    difficulty_profile: DifficultyProfile | None = None,
) -> None:
    """Remove digested NPC prey, log completion, and free the predator next turn."""
    from src.data.depth_scaling_loader import default_depth_scaling_config
    from src.systems.dazed import apply_daze, roll_cv_daze_turns

    predator_state = predator.components.get(Predator)
    narrative_type = predator_state.narrative_type if predator_state else "OV"
    on_screen = entity_visible_to_player(game_map, predator) or entity_visible_to_player(
        game_map, prey
    )
    if on_screen:
        templates = get_narrative_index().digestion_complete_lines(
            entity_type_id(predator),
            narrative_type,
        )
        if not templates:
            templates = DIGESTION_COMPLETE_POOL.get(narrative_type, ())
        if not templates and is_generic_vore_type(narrative_type):
            templates = GENERIC_DIGESTION_COMPLETE
        if templates:
            line = _format_digestion_line(rng.choice(templates), predator, prey)
            # Witnessed NPC digest complete: caution by default.
            message_log.add(line, category=MessageCategory.CAUTION)
    else:
        template = get_narrative_index().pick_offscreen_digest_line(
            entity_type_id(predator),
            narrative_type,
            rng,
        )
        if template is None and is_generic_vore_type(narrative_type):
            template = rng.choice(GENERIC_OFFSCREEN_DIGEST)
        if template is not None:
            line = _format_digestion_line(template, predator, prey)
            # Offscreen digest: heard only — keep routine default.
            message_log.add(line)

    prey.clear()
    predator.components.pop(Predator, None)
    if skip_turn_entities is not None:
        skip_turn_entities.add(predator)
    # GENERIC never uses alternate CV mechanics (standard path only).
    if alternate_cv_mechanics and narrative_type == "CV":
        profile = difficulty_profile
        if profile is None:
            profile = default_depth_scaling_config().profile_for(None)
        apply_daze(
            predator,
            roll_cv_daze_turns(profile, rng),
            game_map,
            message_log,
        )


def apply_digestion_tick(
    prey: Entity,
    predator: Entity,
    game_map: GameMap,
    message_log: MessageLog,
    rng: random.Random,
    *,
    skip_turn_entities: set[Entity] | None = None,
    alternate_cv_mechanics: bool = False,
    difficulty_profile: DifficultyProfile | None = None,
) -> bool:
    """
    Apply one digestion tick to engulfed prey.
    Returns True when the prey was digested and removed.
    """
    stats = predator.components.get(DigestionStats)
    if stats is None:
        return False

    fighter = prey.components.get(Fighter)
    if fighter is None:
        return False

    if fighter.hp > 0:
        fighter.hp = max(0, fighter.hp - stats.damage_per_tick)
        sync_stunned_state(prey)
        _maybe_good_plea_message(prey, predator, game_map, message_log, rng)
        return False

    strikes = prey.components.get(DigestionStrikes)
    if strikes is None:
        strikes = DigestionStrikes(count=0)
        prey.components[DigestionStrikes] = strikes
    strikes.count += 1
    _maybe_good_plea_message(prey, predator, game_map, message_log, rng)

    if strikes.count >= stats.digest_time:
        complete_npc_digestion(
            predator,
            prey,
            game_map,
            message_log,
            rng,
            skip_turn_entities=skip_turn_entities,
            alternate_cv_mechanics=alternate_cv_mechanics,
            difficulty_profile=difficulty_profile,
        )
        return True
    return False