"""PR 2: mixed map generation, water features, stairs, connectivity."""

from __future__ import annotations

from collections import deque

from src.constants import (
    MAP_HEIGHT,
    MAP_WIDTH,
    MAX_ROOMS,
    MIN_SPAWN_CANDIDATE_COUNT,
    MONSTER_SPAWN_MIN_DISTANCE,
    ROOM_MAX_SIZE,
    ROOM_MIN_SIZE,
)

from src.map_gen import _spawn_candidate_count
from src.map_gen import (
    STAIRS_PER_FLOOR,
    Tile,
    WATER_MIN_FEATURE_SIZE,
    connectivity_land_positions,
    connectivity_land_reachable_from,
    generate_dungeon,
    land_positions,
    land_reachable_from,
    stairs_positions,
    validate_land_connectivity,
    validate_stairs_reachable,
    water_positions,
)

_NEIGHBORS8 = (
    (-1, -1),
    (0, -1),
    (1, -1),
    (-1, 0),
    (1, 0),
    (-1, 1),
    (0, 1),
    (1, 1),
)


def _largest_water_component(coords: list[tuple[int, int]]) -> int:
    remaining = set(coords)
    best = 0
    while remaining:
        start = remaining.pop()
        queue: deque[tuple[int, int]] = deque([start])
        size = 1
        while queue:
            x, y = queue.popleft()
            for dx, dy in _NEIGHBORS8:
                neighbor = (x + dx, y + dy)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    size += 1
                    queue.append(neighbor)
        best = max(best, size)
    return best


def test_generated_map_has_connected_land() -> None:
    dungeon = generate_dungeon(MAP_WIDTH, MAP_HEIGHT, seed=42)
    assert validate_land_connectivity(dungeon)
    assert dungeon.is_walkable(*dungeon.enter_xy)


def test_three_stairs_all_reachable() -> None:
    dungeon = generate_dungeon(MAP_WIDTH, MAP_HEIGHT, seed=99)
    stairs = stairs_positions(dungeon)
    assert len(stairs) == STAIRS_PER_FLOOR
    assert validate_stairs_reachable(dungeon)
    assert dungeon.enter_xy not in stairs


def test_many_seeds_produce_valid_maps() -> None:
    for seed in range(12):
        dungeon = generate_dungeon(
            MAP_WIDTH,
            MAP_HEIGHT,
            seed=seed,
            max_rooms=MAX_ROOMS,
            room_min_size=ROOM_MIN_SIZE,
            room_max_size=ROOM_MAX_SIZE,
        )
        assert validate_land_connectivity(dungeon)
        assert validate_stairs_reachable(dungeon)
        assert len(stairs_positions(dungeon)) == STAIRS_PER_FLOOR


def test_water_features_are_shaped_when_present() -> None:
    for seed in range(60):
        dungeon = generate_dungeon(MAP_WIDTH, MAP_HEIGHT, seed=seed)
        water = water_positions(dungeon)
        if not water:
            continue
        assert _largest_water_component(water) >= WATER_MIN_FEATURE_SIZE
        assert validate_land_connectivity(dungeon)
        return
    raise AssertionError("expected at least one seeded map with water in 60 attempts")


def test_water_testing_mode_increases_coverage() -> None:
    normal = sum(
        1
        for seed in range(40)
        if water_positions(generate_dungeon(MAP_WIDTH, MAP_HEIGHT, seed=seed))
    )
    testing = sum(
        1
        for seed in range(40)
        if water_positions(
            generate_dungeon(MAP_WIDTH, MAP_HEIGHT, seed=seed, water_testing=True)
        )
    )
    assert testing > normal
    assert testing >= 32


def test_stairs_are_land_traversable() -> None:
    dungeon = generate_dungeon(MAP_WIDTH, MAP_HEIGHT, seed=7)
    for x, y in stairs_positions(dungeon):
        assert dungeon.is_walkable(x, y)


def test_adequate_spawn_space_from_entrance() -> None:
    dungeon = generate_dungeon(MAP_WIDTH, MAP_HEIGHT, seed=21)
    assert (
        _spawn_candidate_count(dungeon, min_distance=MONSTER_SPAWN_MIN_DISTANCE)
        >= MIN_SPAWN_CANDIDATE_COUNT
    )


def test_land_count_matches_reachable() -> None:
    dungeon = generate_dungeon(MAP_WIDTH, MAP_HEIGHT, seed=13)
    all_land = set(connectivity_land_positions(dungeon))
    reachable = connectivity_land_reachable_from(dungeon, dungeon.enter_xy)
    assert all_land == reachable