"""1v1 arena initialization and victory handling."""

from __future__ import annotations

import random
from collections.abc import Callable
from typing import TYPE_CHECKING

from tcod.ecs import Entity, Registry

from src import events
from src.arena_map import (
    ARENA_ENEMY_X,
    ARENA_PLAYER_X,
    ARENA_WALK_Y,
    build_arena_map,
)
from src.components import (
    BlocksMovement,
    EquipState,
    Fighter,
    Inventory,
    Mobility,
    MobilityType,
    Player,
    PlayerEffects,
    PlayerProgression,
    Position,
    Renderable,
    SpeciesId,
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
from src.data.entity_registry import EntityDefinition
from src.debug.session_log import session_log
from src.spawn import spawn_entity_by_id
from src.systems.inventory import apply_starter_loadout
from src.systems.naming import entity_log_name

if TYPE_CHECKING:
    from src.engine import GameEngine


def is_aquatic_entity(definition: EntityDefinition) -> bool:
    return (
        definition.mobility == MobilityType.AQUATIC
        or definition.spawn_requires_water
    )


def format_arena_victory_message(entity: Entity) -> str:
    """Victory copy: ``You have defeated the rat!``"""
    name = entity_log_name(entity, sentence_start=False)
    return f"You have defeated {name}!"


def _spawn_arena_player(engine: GameEngine, *, target_depth: int) -> None:
    player = engine.world[object()]
    player.components[Position] = Position(ARENA_PLAYER_X, ARENA_WALK_Y)
    player.components[Renderable] = Renderable(ch=ord("@"), fg=(255, 255, 255))
    player.components[Fighter] = Fighter(
        hp=PLAYER_MAX_HP,
        max_hp=PLAYER_MAX_HP,
        accuracy=PLAYER_ACCURACY,
        evade=PLAYER_EVADE,
        ac=PLAYER_AC,
        min_damage=PLAYER_MIN_DAMAGE,
        max_damage=PLAYER_MAX_DAMAGE,
    )
    player.components[Inventory] = Inventory()
    player.components[EquipState] = EquipState()
    player.components[PlayerProgression] = PlayerProgression()
    player.components[PlayerEffects] = PlayerEffects()
    player.components[Mobility] = Mobility(kind=MobilityType.GROUND)
    player.tags.add(Player)

    if target_depth > 1:
        from src.data.floor_rune_loader import load_floor_rune_registry
        from src.depth_jump_loadout import apply_depth_jump_loadout
        from src.systems.inventory import item_registry

        profile = engine.difficulty_profile()
        apply_depth_jump_loadout(
            player,
            target_depth=target_depth,
            rng=engine.rng,
            registry=item_registry(),
            rune_registry=load_floor_rune_registry(),
            runes_per_floor=engine.runes_per_floor(),
            rune_pieces_multiplier=profile.rune_pieces_multiplier,
            run_stats=engine.run_stats,
        )
    else:
        apply_starter_loadout(player)

    player.tags.add(BlocksMovement)
    engine.player = player


def _arena_victory_handler(engine: GameEngine) -> Callable[[Entity], None]:
    def on_entity_defeated(defeated: Entity) -> None:
        if not engine.arena_mode or engine.arena_victory_active:
            return
        arena_enemy = engine.arena_enemy_entity
        if arena_enemy is None:
            return
        defeated_id = defeated.components.get(SpeciesId)
        arena_id = arena_enemy.components.get(SpeciesId)
        if (
            defeated_id is None
            or arena_id is None
            or defeated_id.id != arena_id.id
        ):
            return
        engine.arena_victory_active = True
        engine.arena_victory_message = format_arena_victory_message(defeated)
        engine.vore_modal.reset()
        engine.digestion_modal.reset()
        engine.inventory_modal.reset()
        engine.ground_pickup_modal.reset()
        engine.examine_state.reset()
        engine.dismiss_state.reset()
        engine.macguffin_victory_confirm.reset()
        engine._end_rest_session()
        engine._end_autoexplore_session()
        session_log.log(f"Arena victory vs {arena_id.id}")

    return on_entity_defeated


def register_arena_victory_handler(engine: GameEngine) -> None:
    """Attach defeat hook for the current arena enemy."""
    unregister_arena_victory_handler(engine)
    handler = _arena_victory_handler(engine)
    engine._arena_victory_handler = handler
    events.on_entity_defeated.append(handler)


def unregister_arena_victory_handler(engine: GameEngine) -> None:
    """Remove arena defeat hook if present."""
    handler = getattr(engine, "_arena_victory_handler", None)
    if handler is not None:
        try:
            events.on_entity_defeated.remove(handler)
        except ValueError:
            pass
        engine._arena_victory_handler = None


def clear_arena_state(engine: GameEngine) -> None:
    """Drop arena flags and event hooks."""
    unregister_arena_victory_handler(engine)
    engine.arena_mode = False
    engine.arena_enemy_id = None
    engine.arena_enemy_entity = None
    engine.arena_victory_active = False
    engine.arena_victory_message = ""


def initialize_arena(
    engine: GameEngine,
    entity_id: str,
    *,
    seed: int | None = None,
    registry=None,
) -> Entity:
    """Reset the engine into a single-enemy arena duel."""
    from src import messages

    reg = registry if registry is not None else load_entity_registry()
    definition = reg.get(entity_id)
    min_depth = definition.spawn.min_depth

    clear_arena_state(engine)
    engine.arena_mode = True
    engine.level_warped = True
    engine.arena_enemy_id = entity_id
    engine.depth_jump_start_depth = min_depth if min_depth > 1 else None

    resolved_seed = seed if seed is not None else random.randint(0, 2_147_483_647)
    engine.run_seed = resolved_seed
    engine.rng = random.Random(resolved_seed)
    engine.player_turn_count = 0
    engine.floor_depth = min_depth

    engine.world = Registry()
    engine.player = None
    engine.game_map = build_arena_map(aquatic_enemy=is_aquatic_entity(definition))

    engine.vore_modal.reset()
    engine.digestion_modal.reset()
    engine.game_over.reset()
    engine.run_stats.reset()
    engine.skipped_this_phase.clear()
    engine.examine_state.reset()
    engine.dismiss_state.reset()
    engine.ground_pickup_modal.reset()
    engine.inventory_modal.reset()
    engine.macguffin_discovery.reset()
    engine.macguffin_victory_confirm.reset()
    engine.close_door_pending = False
    engine.last_come_here_turn = -1
    engine._debug_omniscient_vision = False
    engine.log_overlay.close()
    engine.help_overlay.close()
    engine._end_rest_session()
    engine._end_autoexplore_session()
    engine.message_log.clear()

    _spawn_arena_player(engine, target_depth=min_depth)
    enemy = spawn_entity_by_id(
        engine.world,
        entity_id,
        ARENA_ENEMY_X,
        ARENA_WALK_Y,
        registry=reg,
        floor_depth=min_depth,
        difficulty_id=engine.difficulty_id,
        vore_prefs=engine.vore_content_prefs,
    )
    if enemy is None:
        raise ValueError(
            f"arena enemy '{entity_id}' blocked by spawn.requires_vore_types "
            f"for current vore prefs"
        )
    engine.arena_enemy_entity = enemy
    register_arena_victory_handler(engine)

    if engine.floor_prefetch is not None:
        engine.floor_prefetch.cancel()

    engine.message_log.add(messages.welcome())
    engine._update_fov()
    session_log.log(f"Arena start vs {entity_id} at depth {min_depth}")
    return enemy