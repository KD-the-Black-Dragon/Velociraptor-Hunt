"""Group P hot-path helpers (fix-performance-ai-hotpath PR1)."""

from __future__ import annotations

import random

from src.components import AIState, Alignment, MobilityType, Position
from src.constants import MEMORY_SANITIZE_INTERVAL
from src.engine import GameEngine
from src.map_gen import (
    GameMap,
    Tile,
    bfs_path_distances,
    bfs_path_distances_from_mask,
    build_mobility_walk_mask,
    can_enter_tile,
)
from src.systems.ai import (
    ExploreBfsCache,
    ExploreTerrainCache,
    _ensure_explore_goal,
    _sanitize_unreachable_memory_targets,
    explore_reachable_distances,
    spawn_test_npc,
)
from tests.map_test_helpers import ARENA_X, ARENA_Y, carve_floor_rect, isolate_other_ais


def _predicate_distances(game_map: GameMap, origin: tuple[int, int], mobility: MobilityType):
    def can_traverse(x: int, y: int) -> bool:
        return can_enter_tile(game_map, x, y, mobility)

    return bfs_path_distances(
        game_map,
        origin,
        tile_predicate=can_traverse,
        cardinal_only=False,
    )


def test_build_mobility_walk_mask_matches_can_enter_tile() -> None:
    game_map = GameMap(12, 10)
    for y in range(1, 9):
        for x in range(1, 11):
            game_map.tiles[y, x] = int(Tile.FLOOR)
    game_map.tiles[3, 4] = int(Tile.DOOR_CLOSED)
    game_map.tiles[5, 5] = int(Tile.DEEP_WATER)

    mask = build_mobility_walk_mask(game_map, MobilityType.GROUND, include_closed_doors=False)
    for y in range(game_map.height):
        for x in range(game_map.width):
            assert bool(mask[y, x]) is can_enter_tile(game_map, x, y, MobilityType.GROUND)

    mask_doors = build_mobility_walk_mask(
        game_map, MobilityType.GROUND, include_closed_doors=True
    )
    assert mask_doors[3, 4]
    assert not mask[3, 4]


def test_mask_bfs_matches_predicate_bfs() -> None:
    game_map = GameMap(16, 12)
    for y in range(1, 11):
        for x in range(1, 15):
            game_map.tiles[y, x] = int(Tile.FLOOR)
    game_map.tiles[4, 6] = int(Tile.WALL)
    origin = (2, 2)
    mask = build_mobility_walk_mask(game_map, MobilityType.GROUND)
    from_mask = bfs_path_distances_from_mask(origin, mask, cardinal_only=False)
    from_pred = _predicate_distances(game_map, origin, MobilityType.GROUND)
    assert from_mask == from_pred


def test_ensure_explore_goal_short_circuits_with_episode_map() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X + 12, ARENA_Y + 8)
    wolf = spawn_test_npc(
        engine.world,
        x=ARENA_X + 1,
        y=ARENA_Y + 1,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    state = wolf.components[AIState]
    goal = Position(ARENA_X + 8, ARENA_Y + 5)
    origin = wolf.components[Position]
    state.explore_goal = goal
    state.explore_goal_distance_map = {
        origin: 5,
        goal: 0,
        Position(ARENA_X + 2, ARENA_Y + 1): 4,
    }
    cache = ExploreBfsCache(terrain=ExploreTerrainCache())
    returned = _ensure_explore_goal(
        state,
        engine.game_map,
        origin,
        wolf,
        random.Random(0),
        cache=cache,
    )
    assert returned == goal
    assert cache._reachable == {}


def test_sanitize_once_per_visit_via_cache() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X + 10, ARENA_Y + 6)
    wolf = spawn_test_npc(
        engine.world,
        x=ARENA_X + 1,
        y=ARENA_Y + 1,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    state = wolf.components[AIState]
    state.last_known_primary = Position(0, 0)
    cache = ExploreBfsCache()
    _sanitize_unreachable_memory_targets(
        state,
        engine.game_map,
        wolf.components[Position],
        wolf,
        random.Random(0),
        cache=cache,
        player_turn_count=1,
    )
    assert state.last_known_primary is None
    assert cache.sanitize_done is True
    state.last_known_primary = Position(0, 0)
    _sanitize_unreachable_memory_targets(
        state,
        engine.game_map,
        wolf.components[Position],
        wolf,
        random.Random(0),
        cache=cache,
        player_turn_count=1,
    )
    assert state.last_known_primary == Position(0, 0)


def test_sanitize_interval_skips_next_distinct_turn() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X + 10, ARENA_Y + 6)
    wolf = spawn_test_npc(
        engine.world,
        x=ARENA_X + 1,
        y=ARENA_Y + 1,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    state = wolf.components[AIState]
    state.last_known_primary = Position(0, 0)
    _sanitize_unreachable_memory_targets(
        state,
        engine.game_map,
        wolf.components[Position],
        wolf,
        random.Random(0),
        player_turn_count=10,
    )
    assert state.last_known_primary is None
    assert state.memory_sanitize_at_turn == 10

    state.last_known_primary = Position(0, 0)
    _sanitize_unreachable_memory_targets(
        state,
        engine.game_map,
        wolf.components[Position],
        wolf,
        random.Random(0),
        player_turn_count=10 + MEMORY_SANITIZE_INTERVAL - 1,
    )
    assert state.last_known_primary == Position(0, 0)

    _sanitize_unreachable_memory_targets(
        state,
        engine.game_map,
        wolf.components[Position],
        wolf,
        random.Random(0),
        player_turn_count=10 + MEMORY_SANITIZE_INTERVAL,
    )
    assert state.last_known_primary is None


def test_explore_reachable_distances_public_api() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X + 8, ARENA_Y + 6)
    wolf = spawn_test_npc(
        engine.world,
        x=ARENA_X + 2,
        y=ARENA_Y + 2,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    origin = wolf.components[Position]
    reachable = explore_reachable_distances(engine.game_map, origin, wolf)
    assert origin in reachable
    assert reachable[origin] == 0
    assert Position(ARENA_X + 3, ARENA_Y + 2) in reachable
