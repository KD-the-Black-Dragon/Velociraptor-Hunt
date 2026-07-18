"""Explore intent: BFS goals, frustration, oscillation, door-spite explore ties (PR8)."""
from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field
from typing import Literal

from tcod.ecs import Entity, Registry

from src.components import (
    AI,
    Abilities,
    AIState,
    Alignment,
    BlocksMovement,
    Engulfed,
    MobilityType,
    NPCAlignment,
    Player,
    Position,
)
from src.data.ability_parser import FixedAbility
from src.constants import MEMORY_SANITIZE_INTERVAL
from src.map_gen import (
    GameMap,
    Tile,
    bfs_path_distances_from_mask,
    build_mobility_walk_mask,
    can_enter_tile,
)
from src.systems.abilities import has_coward, has_supercoward, coward_should_flee
from src.systems.movement import (
    MOVEMENT_DIRECTIONS,
    can_move_to,
    can_step_for_chase,
    entity_mobility,
    is_stationary,
)
from src.systems.ai.common import (
    DOOR_SPITE_TURNS_MAX,
    DOOR_SPITE_TURNS_MIN,
    _cancel_door_spite,
    _chebyshev,
    _entity_has_hands_ability,
    _get_ai_state,
    _has_los,
    _is_visible_to_ai,
    _npc_alignment,
    _pick_nearest_tied,
    _pick_random_walkable_tile,
    _start_door_spite,
    _visible_evils,
)

ChaseMode = Literal["attack", "follow", "memory", "explore"]

EXPLORE_FRUSTRATION_MIN = 8
EXPLORE_FRUSTRATION_MAX = 12
EXPLORE_OSCILLATION_HISTORY = 4
EXPLORE_IDLE_CHANCE = 0.2


@dataclass
class ExploreTerrainCache:
    """Per-world-phase walkability masks keyed by (mobility, include_closed_doors)."""

    _masks: dict[tuple[object, bool], object] = field(default_factory=dict)

    def mask(
        self,
        game_map: GameMap,
        mobility: MobilityType,
        *,
        include_closed_doors: bool,
    ):
        key = (mobility, include_closed_doors)
        cached = self._masks.get(key)
        if cached is not None:
            return cached
        built = build_mobility_walk_mask(
            game_map,
            mobility,
            include_closed_doors=include_closed_doors,
        )
        self._masks[key] = built
        return built


@dataclass
class ExploreBfsCache:
    """Per-monster-visit memo for explore reachability BFS (Tier A + hot-path P)."""

    terrain: ExploreTerrainCache = field(default_factory=ExploreTerrainCache)
    sanitize_done: bool = False
    _reachable: dict[tuple[int, int, object, bool], dict[Position, int]] = field(
        default_factory=dict
    )
    _reachable_with_doors: dict[tuple[int, int, object, bool], dict[Position, int]] = field(
        default_factory=dict
    )

    def _origin_key(self, origin: Position, entity: Entity) -> tuple[int, int, object, bool]:
        return (
            origin.x,
            origin.y,
            entity_mobility(entity),
            _entity_has_hands_ability(entity),
        )

    def reachable_from(
        self,
        game_map: GameMap,
        origin: Position,
        entity: Entity,
    ) -> dict[Position, int]:
        key = self._origin_key(origin, entity)
        cached = self._reachable.get(key)
        if cached is not None:
            return cached
        result = _compute_explore_reachable_distances(
            game_map,
            origin,
            entity,
            terrain=self.terrain,
        )
        self._reachable[key] = result
        return result

    def reachable_including_closed_doors(
        self,
        game_map: GameMap,
        origin: Position,
        entity: Entity,
    ) -> dict[Position, int]:
        key = self._origin_key(origin, entity)
        cached = self._reachable_with_doors.get(key)
        if cached is not None:
            return cached
        result = _compute_explore_reachable_including_closed_doors(
            game_map,
            origin,
            entity,
            terrain=self.terrain,
        )
        self._reachable_with_doors[key] = result
        return result


def _filter_reachable_for_neutral_explore(
    reachable: dict[Position, int],
    entity: Entity,
    player: Entity | None,
) -> dict[Position, int]:
    if player is None or _npc_alignment(entity) != Alignment.NEUTRAL:
        return reachable
    player_pos = player.components[Position]
    return {
        position: distance
        for position, distance in reachable.items()
        if position != player_pos
    }


def _explore_can_traverse_including_closed_doors(
    game_map: GameMap,
    x: int,
    y: int,
    entity: Entity,
) -> bool:
    """Routing check for door-only partitions (player may have closed a door)."""
    if entity_explore_can_traverse(game_map, x, y, entity):
        return True
    if not game_map.in_bounds(x, y):
        return False
    return Tile(game_map.tiles[y, x]) == Tile.DOOR_CLOSED


def _positions_from_coord_distances(
    distances: dict[tuple[int, int], int],
) -> dict[Position, int]:
    return {Position(x, y): distance for (x, y), distance in distances.items()}


def _compute_explore_reachable_distances(
    game_map: GameMap,
    origin: Position,
    entity: Entity,
    *,
    terrain: ExploreTerrainCache | None = None,
) -> dict[Position, int]:
    """BFS from origin over explore-walkability mask (P1/P3)."""
    mobility = entity_mobility(entity)
    has_hands = _entity_has_hands_ability(entity)
    if terrain is None:
        terrain = ExploreTerrainCache()
    mask = terrain.mask(game_map, mobility, include_closed_doors=has_hands)
    distances = bfs_path_distances_from_mask(
        (origin.x, origin.y),
        mask,
        cardinal_only=False,
    )
    return _positions_from_coord_distances(distances)


def _compute_explore_reachable_including_closed_doors(
    game_map: GameMap,
    origin: Position,
    entity: Entity,
    *,
    terrain: ExploreTerrainCache | None = None,
) -> dict[Position, int]:
    mobility = entity_mobility(entity)
    if terrain is None:
        terrain = ExploreTerrainCache()
    mask = terrain.mask(game_map, mobility, include_closed_doors=True)
    distances = bfs_path_distances_from_mask(
        (origin.x, origin.y),
        mask,
        cardinal_only=False,
    )
    return _positions_from_coord_distances(distances)


def _explore_reachable_including_closed_doors(
    game_map: GameMap,
    origin: Position,
    entity: Entity,
    *,
    cache: ExploreBfsCache | None = None,
) -> dict[Position, int]:
    if cache is not None:
        return cache.reachable_including_closed_doors(game_map, origin, entity)
    return _compute_explore_reachable_including_closed_doors(game_map, origin, entity)


def _target_blocked_only_by_closed_door(
    game_map: GameMap,
    origin: Position,
    target: Position,
    entity: Entity,
    *,
    cache: ExploreBfsCache | None = None,
) -> bool:
    """True when a closed door is the only terrain obstacle to a memory waypoint."""
    strict = explore_reachable_distances(game_map, origin, entity, cache=cache)
    if target in strict:
        return False
    with_doors = _explore_reachable_including_closed_doors(
        game_map,
        origin,
        entity,
        cache=cache,
    )
    return target in with_doors


def _clear_unreachable_memory(
    state: AIState,
    game_map: GameMap,
    origin: Position,
    entity: Entity,
    rng: random.Random,
    *,
    field: Literal[
        "last_known_primary",
        "last_known_neutral",
        "last_known_evil",
        "last_known_player",
    ],
    start_door_spite: bool,
    cache: ExploreBfsCache | None = None,
) -> None:
    cleared = getattr(state, field)
    if cleared is None:
        return
    setattr(state, field, None)
    if not start_door_spite:
        return
    if _entity_has_hands_ability(entity):
        return
    if _target_blocked_only_by_closed_door(
        game_map,
        origin,
        cleared,
        entity,
        cache=cache,
    ):
        _start_door_spite(state, rng)


def _sanitize_unreachable_memory_targets(
    state: AIState,
    game_map: GameMap,
    origin: Position,
    entity: Entity,
    rng: random.Random,
    *,
    cache: ExploreBfsCache | None = None,
    player_turn_count: int = 0,
) -> None:
    """Drop memory waypoints that are no longer terrain-reachable."""
    if (
        state.last_known_primary is None
        and state.last_known_neutral is None
        and state.last_known_evil is None
        and state.last_known_player is None
    ):
        return
    # P4: at most once per monster visit (shared ExploreBfsCache flag).
    if cache is not None and cache.sanitize_done:
        return
    # P4: interval K across *distinct* player turns (same turn re-runs without cache
    # so tests that omit player_turn_count still clear memory).
    if (
        state.memory_sanitize_at_turn >= 0
        and player_turn_count != state.memory_sanitize_at_turn
        and player_turn_count - state.memory_sanitize_at_turn < MEMORY_SANITIZE_INTERVAL
    ):
        if cache is not None:
            cache.sanitize_done = True
        return
    if cache is not None:
        cache.sanitize_done = True
    state.memory_sanitize_at_turn = player_turn_count
    reachable = explore_reachable_distances(game_map, origin, entity, cache=cache)
    if state.last_known_primary is not None and state.last_known_primary not in reachable:
        _clear_unreachable_memory(
            state,
            game_map,
            origin,
            entity,
            rng,
            field="last_known_primary",
            start_door_spite=True,
            cache=cache,
        )
    if state.last_known_neutral is not None and state.last_known_neutral not in reachable:
        _clear_unreachable_memory(
            state,
            game_map,
            origin,
            entity,
            rng,
            field="last_known_neutral",
            start_door_spite=False,
            cache=cache,
        )
    if state.last_known_evil is not None and state.last_known_evil not in reachable:
        _clear_unreachable_memory(
            state,
            game_map,
            origin,
            entity,
            rng,
            field="last_known_evil",
            start_door_spite=True,
            cache=cache,
        )
    if state.last_known_player is not None and state.last_known_player not in reachable:
        _clear_unreachable_memory(
            state,
            game_map,
            origin,
            entity,
            rng,
            field="last_known_player",
            start_door_spite=True,
            cache=cache,
        )


def _blocked_tiles_for_explore(
    monster: Entity,
    world: Registry,
    base_blocked: frozenset[Position],
) -> frozenset[Position]:
    """Explore pathing treats other NPC-occupied tiles as impassable."""
    blocked = set(base_blocked)
    for entity in world.Q.all_of(components=[AI, Position, BlocksMovement]):
        if entity is monster:
            continue
        blocked.add(entity.components[Position])
    return frozenset(blocked)


def entity_explore_can_traverse(
    game_map: GameMap,
    x: int,
    y: int,
    entity: Entity,
) -> bool:
    """Terrain passable for explore reachability (BFS). Ignores other entities."""
    if can_enter_tile(game_map, x, y, entity_mobility(entity)):
        return True
    if _entity_has_hands_ability(entity):
        if not game_map.in_bounds(x, y):
            return False
        return Tile(game_map.tiles[y, x]) == Tile.DOOR_CLOSED
    return False


def explore_reachable_distances(
    game_map: GameMap,
    origin: Position,
    entity: Entity,
    *,
    cache: ExploreBfsCache | None = None,
    terrain: ExploreTerrainCache | None = None,
) -> dict[Position, int]:
    """BFS path distances from origin over explore-traversable tiles (8-directional)."""
    if cache is not None:
        return cache.reachable_from(game_map, origin, entity)
    return _compute_explore_reachable_distances(
        game_map,
        origin,
        entity,
        terrain=terrain,
    )


def _pick_weighted_far_explore_goal(
    reachable: dict[Position, int],
    origin: Position,
    rng: random.Random,
) -> Position | None:
    candidates = [
        (position, distance)
        for position, distance in reachable.items()
        if position.x != origin.x or position.y != origin.y
    ]
    if not candidates:
        return None
    positions = [position for position, _distance in candidates]
    weights = [max(distance, 1) for _position, distance in candidates]
    return rng.choices(positions, weights=weights, k=1)[0]


def _pick_farthest_explore_goal(
    reachable: dict[Position, int],
    origin: Position,
    rng: random.Random,
) -> Position | None:
    candidates = [
        (position, distance)
        for position, distance in reachable.items()
        if position.x != origin.x or position.y != origin.y
    ]
    if not candidates:
        return None
    max_distance = max(distance for _position, distance in candidates)
    farthest = [
        position
        for position, distance in candidates
        if distance == max_distance
    ]
    return rng.choice(farthest)


def _pick_explore_goal_from_reachable(
    reachable: dict[Position, int],
    origin: Position,
    state: AIState,
    rng: random.Random,
) -> Position | None:
    if state.explore_force_farthest_on_repick:
        state.explore_force_farthest_on_repick = False
        return _pick_farthest_explore_goal(reachable, origin, rng)
    return _pick_weighted_far_explore_goal(reachable, origin, rng)


def _reset_explore_frustration(state: AIState) -> None:
    state.explore_frustration = 0
    state.explore_frustration_limit = 0


def _clear_explore_goal_distance_map(state: AIState) -> None:
    state.explore_goal_distance_map = None


def _compute_explore_distances_to_goal(
    game_map: GameMap,
    goal: Position,
    entity: Entity,
    *,
    terrain: ExploreTerrainCache | None = None,
) -> dict[Position, int]:
    """BFS from goal over explore-walkability mask (P1/P3)."""
    mobility = entity_mobility(entity)
    has_hands = _entity_has_hands_ability(entity)
    if terrain is None:
        terrain = ExploreTerrainCache()
    mask = terrain.mask(game_map, mobility, include_closed_doors=has_hands)
    distances = bfs_path_distances_from_mask(
        (goal.x, goal.y),
        mask,
        cardinal_only=False,
    )
    return _positions_from_coord_distances(distances)


def _goal_distances_for_explore(
    state: AIState,
    game_map: GameMap,
    goal: Position,
    entity: Entity,
    *,
    terrain: ExploreTerrainCache | None = None,
) -> dict[Position, int]:
    """Episode cache (A2): one BFS from goal until goal changes."""
    if state.explore_goal == goal and state.explore_goal_distance_map is not None:
        return state.explore_goal_distance_map
    distance_map = _compute_explore_distances_to_goal(
        game_map,
        goal,
        entity,
        terrain=terrain,
    )
    state.explore_goal_distance_map = distance_map
    return distance_map


def _begin_explore_goal_episode(
    state: AIState,
    goal: Position,
    rng: random.Random,
    *,
    game_map: GameMap,
    entity: Entity,
    terrain: ExploreTerrainCache | None = None,
) -> None:
    state.explore_goal = goal
    state.explore_frustration = 0
    state.explore_frustration_limit = rng.randint(
        EXPLORE_FRUSTRATION_MIN,
        EXPLORE_FRUSTRATION_MAX,
    )
    state.explore_recent_positions.clear()
    state.explore_recent_goal_distances.clear()
    state.explore_goal_distance_map = _compute_explore_distances_to_goal(
        game_map,
        goal,
        entity,
        terrain=terrain,
    )


def _explore_frustration_give_up(state: AIState) -> None:
    state.explore_goal = None
    _reset_explore_frustration(state)
    state.explore_force_farthest_on_repick = True
    _clear_explore_goal_distance_map(state)


def explore_distances_to_goal(
    game_map: GameMap,
    goal: Position,
    entity: Entity,
    *,
    terrain: ExploreTerrainCache | None = None,
) -> dict[Position, int]:
    """BFS path distances to `goal` over explore-traversable tiles."""
    return _compute_explore_distances_to_goal(
        game_map,
        goal,
        entity,
        terrain=terrain,
    )


def _explore_path_distance_to_goal(
    game_map: GameMap,
    origin: Position,
    goal: Position,
    entity: Entity,
    *,
    state: AIState | None = None,
    terrain: ExploreTerrainCache | None = None,
) -> int | None:
    if state is not None:
        return _goal_distances_for_explore(
            state,
            game_map,
            goal,
            entity,
            terrain=terrain,
        ).get(origin)
    return explore_distances_to_goal(game_map, goal, entity, terrain=terrain).get(origin)


def _pick_opposite_explore_goal(
    reachable: dict[Position, int],
    origin: Position,
    failed_goal: Position,
    rng: random.Random,
) -> Position | None:
    candidates = [
        position
        for position in reachable
        if position.x != origin.x or position.y != origin.y
    ]
    if not candidates:
        return None
    max_away = max(_chebyshev(position, failed_goal) for position in candidates)
    away = [position for position in candidates if _chebyshev(position, failed_goal) == max_away]
    return rng.choice(away)


def _explore_positions_oscillating(recent: deque[Position]) -> bool:
    if len(recent) < EXPLORE_OSCILLATION_HISTORY:
        return False
    last_four = list(recent)[-EXPLORE_OSCILLATION_HISTORY:]
    unique = {(position.x, position.y) for position in last_four}
    if len(unique) != 2:
        return False
    return (
        last_four[0] == last_four[2]
        and last_four[1] == last_four[3]
        and last_four[0] != last_four[1]
    )


def _explore_distances_oscillating(recent: deque[int]) -> bool:
    if len(recent) < EXPLORE_OSCILLATION_HISTORY:
        return False
    last_four = list(recent)[-EXPLORE_OSCILLATION_HISTORY:]
    if len(set(last_four)) != 2:
        return False
    return last_four[0] == last_four[2] and last_four[1] == last_four[3]


def _explore_is_oscillating(state: AIState) -> bool:
    return _explore_positions_oscillating(
        state.explore_recent_positions
    ) or _explore_distances_oscillating(state.explore_recent_goal_distances)


def _explore_oscillation_repick(
    state: AIState,
    entity: Entity,
    game_map: GameMap,
    origin: Position,
    failed_goal: Position,
    rng: random.Random,
    *,
    player: Entity | None = None,
    cache: ExploreBfsCache | None = None,
) -> None:
    state.explore_goal = None
    _clear_explore_goal_distance_map(state)
    _reset_explore_frustration(state)
    state.explore_recent_positions.clear()
    state.explore_recent_goal_distances.clear()
    reachable = _filter_reachable_for_neutral_explore(
        explore_reachable_distances(game_map, origin, entity, cache=cache),
        entity,
        player,
    )
    terrain = cache.terrain if cache is not None else None
    picked = _pick_opposite_explore_goal(reachable, origin, failed_goal, rng)
    if picked is None:
        _ensure_explore_goal(
            state,
            game_map,
            origin,
            entity,
            rng,
            player=player,
            cache=cache,
        )
        return
    _begin_explore_goal_episode(
        state,
        picked,
        rng,
        game_map=game_map,
        entity=entity,
        terrain=terrain,
    )


def _ensure_explore_goal(
    state: AIState,
    game_map: GameMap,
    origin: Position,
    entity: Entity,
    rng: random.Random,
    *,
    player: Entity | None = None,
    cache: ExploreBfsCache | None = None,
) -> Position:
    if is_stationary(entity):
        state.explore_goal = None
        _reset_explore_frustration(state)
        _clear_explore_goal_distance_map(state)
        return origin
    goal = state.explore_goal
    # P2: episode distance map already proves path-reachability — skip full reachable BFS.
    if (
        goal is not None
        and goal != origin
        and state.explore_goal_distance_map is not None
        and origin in state.explore_goal_distance_map
    ):
        if player is not None and _npc_alignment(entity) == Alignment.NEUTRAL:
            if goal == player.components[Position]:
                pass  # fall through and re-pick away from player tile
            else:
                return goal
        else:
            return goal

    terrain = cache.terrain if cache is not None else None
    reachable = _filter_reachable_for_neutral_explore(
        explore_reachable_distances(game_map, origin, entity, cache=cache, terrain=terrain),
        entity,
        player,
    )
    if goal is not None and goal != origin and goal in reachable:
        return goal
    picked = _pick_explore_goal_from_reachable(reachable, origin, state, rng)
    if picked is None:
        state.explore_goal = None
        _reset_explore_frustration(state)
        _clear_explore_goal_distance_map(state)
        return origin
    _begin_explore_goal_episode(
        state,
        picked,
        rng,
        game_map=game_map,
        entity=entity,
        terrain=terrain,
    )
    return picked


def _is_explore_step(
    alignment: Alignment,
    state: AIState,
    entity_target: Entity | None,
    pos_target: Position | None,
    chase_mode: ChaseMode,
) -> bool:
    if entity_target is not None or pos_target is None:
        return False
    if alignment == Alignment.GOOD:
        return chase_mode == "explore"
    if alignment == Alignment.EVIL:
        return state.explore_goal is not None and pos_target == state.explore_goal
    return False


def _complete_explore_step(
    state: AIState,
    entity: Entity,
    game_map: GameMap,
    origin: Position,
    rng: random.Random,
    *,
    moved: bool,
    player: Entity | None = None,
    cache: ExploreBfsCache | None = None,
) -> None:
    goal = state.explore_goal
    if goal is None:
        return
    if state.explore_frustration_limit == 0:
        state.explore_frustration_limit = rng.randint(
            EXPLORE_FRUSTRATION_MIN,
            EXPLORE_FRUSTRATION_MAX,
        )
        state.explore_frustration = 0

    distance_before = _explore_path_distance_to_goal(
        game_map,
        origin,
        goal,
        entity,
        state=state,
    )
    if distance_before is None:
        _ensure_explore_goal(
            state,
            game_map,
            origin,
            entity,
            rng,
            player=player,
            cache=cache,
        )
        return

    if not moved:
        state.explore_frustration += 1
    else:
        current = entity.components[Position]
        distance_after = _explore_path_distance_to_goal(
            game_map,
            current,
            goal,
            entity,
            state=state,
        )
        if distance_after is None or distance_after >= distance_before:
            state.explore_frustration += 1
        else:
            state.explore_frustration = 0

    current = entity.components[Position]
    distance_record = (
        _explore_path_distance_to_goal(
            game_map,
            current,
            goal,
            entity,
            state=state,
        )
        if moved
        else distance_before
    )
    if distance_record is not None:
        state.explore_recent_positions.append(current)
        state.explore_recent_goal_distances.append(distance_record)

    if _explore_is_oscillating(state):
        _explore_oscillation_repick(
            state,
            entity,
            game_map,
            current,
            goal,
            rng,
            player=player,
            cache=cache,
        )
        return

    if state.explore_frustration >= state.explore_frustration_limit:
        _explore_frustration_give_up(state)
        _ensure_explore_goal(
            state,
            game_map,
            current,
            entity,
            rng,
            player=player,
            cache=cache,
        )


def _is_neutral_explore_step(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
) -> bool:
    if _npc_alignment(monster) != Alignment.NEUTRAL:
        return False
    evils = _visible_evils(monster, world, game_map)
    if not evils:
        return True
    return (
        has_coward(monster)
        and not has_supercoward(monster)
        and not coward_should_flee(monster)
    )


def _is_explore_target_step(
    monster: Entity,
    state: AIState | None,
    target_position: Position | None,
    chase_mode: ChaseMode,
) -> bool:
    if state is None or target_position is None or state.explore_goal is None:
        return False
    if target_position != state.explore_goal:
        return False
    if chase_mode == "explore":
        return True
    return _npc_alignment(monster) == Alignment.EVIL


def _choose_explore_sidestep(
    world: Registry,
    game_map: GameMap,
    monster: Entity,
    origin: Position,
    goal: Position,
    entity: Entity,
    rng: random.Random,
    *,
    blocked_tiles: frozenset[Position] = frozenset(),
    recent_positions: deque[Position],
    state: AIState | None = None,
) -> tuple[int, int] | None:
    if state is not None:
        distances = _goal_distances_for_explore(state, game_map, goal, entity)
    else:
        distances = explore_distances_to_goal(game_map, goal, entity)
    origin_dist = distances.get(origin)
    candidates: list[tuple[int, int, int, int]] = []
    for direction in MOVEMENT_DIRECTIONS:
        dest = origin + direction
        if dest in blocked_tiles:
            continue
        if not can_move_to(
            world,
            game_map,
            monster,
            origin,
            direction,
            blocked_tiles=blocked_tiles,
        ):
            continue
        dest_dist = distances.get(dest, origin_dist)
        recent_penalty = 1 if dest in recent_positions else 0
        away_score = 0 if origin_dist is None or dest_dist is None else dest_dist - origin_dist
        candidates.append((recent_penalty, -away_score, direction[0], direction[1]))
    if not candidates:
        return None
    candidates.sort()
    best = candidates[0]
    tied = [entry for entry in candidates if entry[:2] == best[:2]]
    choice = rng.choice(tied)
    return (choice[2], choice[3])


def _choose_explore_direction(
    world: Registry,
    game_map: GameMap,
    monster: Entity,
    origin: Position,
    goal: Position,
    entity: Entity,
    rng: random.Random,
    *,
    blocked_tiles: frozenset[Position] = frozenset(),
    recent_positions: deque[Position],
    state: AIState | None = None,
    allow_idle: bool = True,
) -> tuple[int, int] | None:
    """BFS one-step toward goal; sidestep away from goal when blocked."""
    if is_stationary(monster):
        return None
    if allow_idle and rng.random() < EXPLORE_IDLE_CHANCE:
        return None
    if state is not None:
        distances = _goal_distances_for_explore(state, game_map, goal, entity)
    else:
        distances = explore_distances_to_goal(game_map, goal, entity)
    origin_dist = distances.get(origin)
    if origin_dist is None:
        return _choose_explore_sidestep(
            world,
            game_map,
            monster,
            origin,
            goal,
            entity,
            rng,
            blocked_tiles=blocked_tiles,
            recent_positions=recent_positions,
            state=state,
        )

    best_distance = origin_dist
    best_directions: list[tuple[int, int]] = []
    for direction in MOVEMENT_DIRECTIONS:
        dest = origin + direction
        if dest in blocked_tiles:
            continue
        if not can_move_to(
            world,
            game_map,
            monster,
            origin,
            direction,
            blocked_tiles=blocked_tiles,
        ):
            continue
        dest_dist = distances.get(dest)
        if dest_dist is None:
            continue
        if dest_dist < best_distance:
            best_distance = dest_dist
            best_directions = [direction]
        elif dest_dist == best_distance:
            best_directions.append(direction)

    if best_distance < origin_dist and best_directions:
        return rng.choice(best_directions)

    return _choose_explore_sidestep(
        world,
        game_map,
        monster,
        origin,
        goal,
        entity,
        rng,
        blocked_tiles=blocked_tiles,
        recent_positions=recent_positions,
        state=state,
    )


