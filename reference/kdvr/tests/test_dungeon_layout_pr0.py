"""PR0: map sanity validation, spread-aware stairs, fallback room."""

from __future__ import annotations

from unittest.mock import patch

from src.constants import (
    MAP_HEIGHT,
    MAP_WIDTH,
    MIN_LAND_TILE_COUNT,
    MIN_PAIRWISE_SPREAD_BFS,
    MIN_SPAWN_CANDIDATE_COUNT,
    MONSTER_SPAWN_MIN_DISTANCE,
    RUNES_PER_FLOOR,
)
from src.map_gen import (
    STAIRS_PER_FLOOR,
    GameMap,
    Tile,
    _attempt_generate_dungeon,
    _fallback_giant_room,
    _is_traversable_land_tile,
    _spawn_candidate_count,
    count_land_tiles,
    generate_dungeon,
    min_pairwise_bfs_distance,
    stairs_positions,
    validate_land_connectivity,
    validate_min_land_tiles,
    validate_pairwise_spread,
    validate_rune_sites_feasible,
    validate_stairs_reachable,
)


def _fill_floor_box(game_map: GameMap, x1: int, y1: int, x2: int, y2: int) -> None:
    game_map.tiles[y1 : y2 + 1, x1 : x2 + 1] = Tile.FLOOR


def test_validate_min_land_tiles_rejects_small_map() -> None:
    game_map = GameMap(20, 20)
    _fill_floor_box(game_map, 5, 5, 14, 14)
    game_map.enter_xy = (10, 10)
    assert count_land_tiles(game_map) == 100
    assert not validate_min_land_tiles(game_map)


def test_validate_pairwise_spread_detects_clustered_stairs() -> None:
    game_map = GameMap(30, 30)
    _fill_floor_box(game_map, 1, 1, 28, 28)
    game_map.enter_xy = (15, 15)
    clustered = [(10, 10), (11, 10), (10, 11)]
    assert not validate_pairwise_spread(game_map, clustered)


def test_validate_pairwise_spread_accepts_spread_stairs() -> None:
    game_map = GameMap(40, 40)
    _fill_floor_box(game_map, 1, 1, 38, 38)
    game_map.enter_xy = (20, 20)
    spread = [(4, 4), (4, 34), (34, 4)]
    assert validate_pairwise_spread(game_map, spread)


def test_validate_rune_sites_feasible_on_large_floor() -> None:
    game_map = GameMap(50, 50)
    _fill_floor_box(game_map, 1, 1, 48, 48)
    game_map.enter_xy = (25, 25)
    assert validate_rune_sites_feasible(game_map, count=RUNES_PER_FLOOR)


def test_validate_rune_sites_infeasible_on_narrow_corridor() -> None:
    game_map = GameMap(30, 10)
    _fill_floor_box(game_map, 1, 4, 28, 5)
    game_map.enter_xy = (2, 4)
    assert not validate_rune_sites_feasible(game_map, count=RUNES_PER_FLOOR)


def test_fallback_giant_room_is_large_and_valid() -> None:
    dungeon = _fallback_giant_room(MAP_WIDTH, MAP_HEIGHT)
    assert count_land_tiles(dungeon) >= MIN_LAND_TILE_COUNT
    assert validate_land_connectivity(dungeon)
    assert validate_stairs_reachable(dungeon)
    assert len(stairs_positions(dungeon)) == STAIRS_PER_FLOOR
    assert validate_pairwise_spread(dungeon, stairs_positions(dungeon))
    assert validate_rune_sites_feasible(dungeon)


def test_generate_dungeon_uses_fallback_when_all_attempts_fail() -> None:
    with patch("src.map_gen._attempt_generate_dungeon", return_value=(None, "too_few_land_tiles")):
        dungeon = generate_dungeon(MAP_WIDTH, MAP_HEIGHT, seed=1)
    assert count_land_tiles(dungeon) >= MIN_LAND_TILE_COUNT
    assert validate_pairwise_spread(dungeon, stairs_positions(dungeon))


def test_many_seeds_pass_sanity_gates() -> None:
    for seed in range(30):
        dungeon = generate_dungeon(MAP_WIDTH, MAP_HEIGHT, seed=seed)
        assert validate_min_land_tiles(dungeon)
        assert (
            _spawn_candidate_count(dungeon, min_distance=MONSTER_SPAWN_MIN_DISTANCE)
            >= MIN_SPAWN_CANDIDATE_COUNT
        )
        assert validate_land_connectivity(dungeon)
        assert validate_stairs_reachable(dungeon)
        assert len(stairs_positions(dungeon)) == STAIRS_PER_FLOOR
        stairs = stairs_positions(dungeon)
        assert min_pairwise_bfs_distance(
            dungeon,
            stairs,
            tile_predicate=lambda x, y, gm=dungeon: _is_traversable_land_tile(gm, x, y),
        ) >= MIN_PAIRWISE_SPREAD_BFS
        # Rune-site feasibility is checked during generation before doors are placed.


def test_spread_aware_stairs_via_attempt_generate() -> None:
    import random

    dungeon = None
    reason = "no_attempt"
    for seed in range(200):
        dungeon, reason = _attempt_generate_dungeon(
            MAP_WIDTH,
            MAP_HEIGHT,
            random.Random(seed),
            max_rooms=30,
            room_min_size=6,
            room_max_size=10,
        )
        if dungeon is not None:
            break
    assert reason is None
    assert dungeon is not None
    stairs = stairs_positions(dungeon)
    assert validate_pairwise_spread(dungeon, stairs)