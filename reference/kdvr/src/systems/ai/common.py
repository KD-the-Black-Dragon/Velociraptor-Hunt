"""Shared AI helpers used by explore, chase, and visit (PR8)."""
from __future__ import annotations

import random
from collections import deque

from tcod.ecs import Entity, Registry

from src.components import (
    Abilities,
    AbilityState,
    AI,
    AIState,
    Alignment,
    BlocksMovement,
    Engulfed,
    Fighter,
    MobilityType,
    NPCAlignment,
    Player,
    Position,
    Predator,
)
from src.data.ability_parser import FixedAbility
from src.data.depth_scaling_config import SpawnAiFreezeConfig
from src.constants import (
    BUSY_FLOOR_NPC_THRESHOLD,
    DISTANT_AI_RADIUS,
)
from src.map_gen import GameMap, Tile, can_enter_tile
from src.systems.fov import can_see
from src.systems.movement import MOVEMENT_DIRECTIONS, can_move_to, entity_mobility

DOOR_SPITE_TURNS_MIN = 8
DOOR_SPITE_TURNS_MAX = 12
# Brief "how dare you slam that door" pause before detouring (memory kept).
DOOR_SHOCK_TURNS_MIN = 2
DOOR_SHOCK_TURNS_MAX = 4
# Blind memory pursuit without re-acquiring LOS — trail goes cold.
MEMORY_TRAIL_TURNS_MIN = 12
MEMORY_TRAIL_TURNS_MAX = 18

def _sorted_monsters(world: Registry) -> list[Entity]:
    monsters = [
        monster
        for monster in world.Q.all_of(components=[AI, Position])
        if Player not in monster.tags
    ]
    return sorted(
        monsters,
        key=lambda monster: (
            monster.components[Position].y,
            monster.components[Position].x,
            id(monster),
        ),
    )


def _npc_alignment(entity: Entity) -> Alignment:
    alignment = entity.components.get(NPCAlignment)
    if alignment is None:
        return Alignment.EVIL
    return alignment.alignment


def _get_ai_state(entity: Entity) -> AIState:
    state = entity.components.get(AIState)
    if state is None:
        state = AIState()
        entity.components[AIState] = state
    return state


def _get_ability_state(entity: Entity) -> AbilityState:
    state = entity.components.get(AbilityState)
    if state is None:
        state = AbilityState()
        entity.components[AbilityState] = state
    return state


def _chebyshev(a: Position, b: Position) -> int:
    return max(abs(a.x - b.x), abs(a.y - b.y))


def _floor_is_busy(npc_count: int) -> bool:
    """D4: distant throttles only apply when active AI NPC count exceeds N."""
    return npc_count > BUSY_FLOOR_NPC_THRESHOLD


def _is_distant_from_player(monster_pos: Position, player_pos: Position) -> bool:
    """Distant = Chebyshev distance from player > R (not FOV / viewport)."""
    return _chebyshev(monster_pos, player_pos) > DISTANT_AI_RADIUS


def clear_spawn_ai_freeze(entity: Entity) -> None:
    """End spawn freeze permanently (damage, proximity, or timer). Idempotent."""
    state = entity.components.get(AIState)
    if state is None:
        return
    state.spawn_freeze_remaining = 0
    state.spawn_freeze_consumed = True


def apply_spawn_ai_freeze_at_spawn(
    entity: Entity,
    *,
    spawn_x: int,
    spawn_y: int,
    player_x: int,
    player_y: int,
    freeze_config: SpawnAiFreezeConfig | None,
) -> None:
    """Arm one-shot freeze from Chebyshev distance at materialization."""
    state = entity.components.get(AIState)
    if state is None:
        return
    if freeze_config is None or not freeze_config.enabled:
        state.spawn_freeze_remaining = 0
        state.spawn_freeze_consumed = True
        return
    cheb = max(abs(spawn_x - player_x), abs(spawn_y - player_y))
    turns = freeze_config.freeze_turns_for_chebyshev(cheb)
    state.spawn_freeze_remaining = turns
    state.spawn_freeze_consumed = turns <= 0


def spawn_ai_freeze_blocks_action(
    monster: Entity,
    player: Entity,
    freeze_config: SpawnAiFreezeConfig | None,
) -> bool:
    """Tick spawn freeze; return True if this NPC should skip its AI visit."""
    state = monster.components.get(AIState)
    if state is None:
        return False
    if state.spawn_freeze_consumed:
        return False
    if state.spawn_freeze_remaining <= 0:
        state.spawn_freeze_consumed = True
        return False

    monster_pos = monster.components.get(Position)
    player_pos = player.components.get(Position)
    if monster_pos is None or player_pos is None:
        clear_spawn_ai_freeze(monster)
        return False

    prox = 8 if freeze_config is None else freeze_config.proximity_unfreeze
    if _chebyshev(monster_pos, player_pos) <= prox:
        clear_spawn_ai_freeze(monster)
        return False

    state.spawn_freeze_remaining -= 1
    if state.spawn_freeze_remaining <= 0:
        state.spawn_freeze_consumed = True
    return True


def _distant_throttle_applies(
    monster: Entity,
    player: Entity,
    *,
    busy: bool,
) -> bool:
    """True when D2/D3 should apply: busy floor and monster beyond R."""
    if not busy:
        return False
    monster_pos = monster.components.get(Position)
    player_pos = player.components.get(Position)
    if monster_pos is None or player_pos is None:
        return False
    return _is_distant_from_player(monster_pos, player_pos)


def _half_turn_should_act(state: AIState, player_turn_count: int) -> bool:
    """D2: act when (turn + salt) is even."""
    return (player_turn_count + (state.ai_turn_salt & 1)) % 2 == 0


def _distance_squared_to(origin: Position, target: Position) -> int:
    return (target.x - origin.x) ** 2 + (target.y - origin.y) ** 2


def _has_los(game_map: GameMap, origin: Position, target: Position) -> bool:
    return can_see(game_map, origin.x, origin.y, target.x, target.y)


def _is_visible_to_ai(entity: Entity) -> bool:
    """Engulfed prey is hidden from all AI targeting."""
    return Engulfed not in entity.tags


def _forbidden_tiles(monster: Entity, player: Entity) -> frozenset[Position]:
    if _npc_alignment(monster) in (Alignment.GOOD, Alignment.NEUTRAL):
        return frozenset({player.components[Position]})
    return frozenset()


def _entity_has_hands_ability(entity: Entity) -> bool:
    """True when entity has ``Hands`` (closed-door traverse + open on step)."""
    from src.systems.abilities import has_hands

    return has_hands(entity)


def _pick_nearest_tied(
    origin: Position,
    candidates: list[Entity],
    rng: random.Random,
) -> Entity:
    best_distance = min(_chebyshev(origin, c.components[Position]) for c in candidates)
    tied = [
        candidate
        for candidate in candidates
        if _chebyshev(origin, candidate.components[Position]) == best_distance
    ]
    return rng.choice(tied)


def _pick_random_walkable_tile(
    game_map: GameMap,
    rng: random.Random,
    *,
    exclude: Position | None = None,
    mobility: MobilityType = MobilityType.GROUND,
) -> Position:
    tiles = [
        Position(x, y)
        for y in range(game_map.height)
        for x in range(game_map.width)
        if can_enter_tile(game_map, x, y, mobility)
        and (exclude is None or x != exclude.x or y != exclude.y)
    ]
    if not tiles:
        return exclude or Position(0, 0)
    return rng.choice(tiles)


def _start_door_spite(
    state: AIState,
    rng: random.Random,
    *,
    turns_min: int | None = None,
    turns_max: int | None = None,
) -> None:
    """Stand still for a rolled wait. Does not clear last-known by itself."""
    if state.door_spite_turns_left > 0:
        return
    # Read module globals at call time so tests can monkeypatch durations.
    lo = DOOR_SPITE_TURNS_MIN if turns_min is None else turns_min
    hi = DOOR_SPITE_TURNS_MAX if turns_max is None else turns_max
    lo, hi = min(lo, hi), max(lo, hi)
    state.door_spite_turns_left = rng.randint(lo, hi)
    # Inline chase-pursuit reset (same as chase._reset_chase_pursuit) so
    # common does not import chase.
    state.chase_momentum_direction = None
    state.chase_momentum_turns_left = 0
    state.chase_frustration = 0
    state.chase_frustration_limit = 0
    state.memory_pursuit_distance_map = None
    state.memory_pursuit_map_target = None


def _start_door_shock(state: AIState, rng: random.Random) -> None:
    """Short door-slam indignation; keeps last-known so detour can follow."""
    _start_door_spite(
        state,
        rng,
        turns_min=DOOR_SHOCK_TURNS_MIN,  # module globals; monkeypatch-friendly
        turns_max=DOOR_SHOCK_TURNS_MAX,
    )


def _closed_door_toward_target(
    game_map: GameMap,
    origin: Position,
    target: Position,
) -> bool:
    """True when a closed door is an adjacent Euclidean step toward the target."""
    origin_dist = (target.x - origin.x) ** 2 + (target.y - origin.y) ** 2
    for direction in MOVEMENT_DIRECTIONS:
        dest = origin + direction
        if not game_map.in_bounds(dest.x, dest.y):
            continue
        if Tile(game_map.tiles[dest.y, dest.x]) != Tile.DOOR_CLOSED:
            continue
        dest_dist = (target.x - dest.x) ** 2 + (target.y - dest.y) ** 2
        if dest_dist < origin_dist:
            return True
    return False


def _cancel_door_spite(state: AIState) -> None:
    state.door_spite_turns_left = 0


def _visible_evils(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
) -> list[Entity]:
    origin = monster.components[Position]
    evils: list[Entity] = []
    for entity in world.Q.all_of(components=[AI, Position, NPCAlignment]):
        if entity is monster or Player in entity.tags:
            continue
        if not _is_visible_to_ai(entity):
            continue
        if _npc_alignment(entity) != Alignment.EVIL:
            continue
        target_pos = entity.components[Position]
        if _has_los(game_map, origin, target_pos):
            evils.append(entity)
    return evils


