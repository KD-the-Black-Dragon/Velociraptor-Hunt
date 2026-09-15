"""PR3: floor init loop, rune spread fix, and item non-blocking."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from tcod.ecs import Registry

from src.components import FloorRune, ItemCategory, Position
from src.constants import MAP_HEIGHT, MAP_WIDTH, MIN_PAIRWISE_SPREAD_BFS, RUNES_PER_FLOOR
from src.engine import GameEngine
from src.map_gen import GameMap, Tile, generate_dungeon, min_pairwise_bfs_distance
from src.spawn import spawn_item_entity
from src.systems.floor_runes import (
    RunePlacementError,
    bfs_path_distance_from,
    occupied_rune_blocked_tiles,
    rune_candidates_with_path_distance,
    spawn_floor_rune,
)
from tests.rune_test_helpers import rune_placement_arena


def test_floor_items_do_not_block_rune_candidates() -> None:
    world = Registry()
    game_map = rune_placement_arena(width=30, height=10)
    ex, ey = game_map.enter_xy
    item_x = ex + 8
    spawn_item_entity(world, ItemCategory.WEAPON, "dagger", item_x, ey)

    candidates = rune_candidates_with_path_distance(game_map, world, game_map.enter_xy)
    candidate_coords = {(x, y) for x, y, _dist in candidates}
    assert (item_x, ey) in candidate_coords
    assert (item_x, ey) not in occupied_rune_blocked_tiles(world)


def test_spawn_floor_rune_enforces_pairwise_spread() -> None:
    world = Registry()
    game_map = GameMap(60, 40)
    game_map.tiles[:, :] = Tile.WALL
    game_map.tiles[10:30, 10:50] = Tile.FLOOR
    game_map.enter_xy = (12, 20)

    from src.data.floor_rune_loader import load_floor_rune_registry

    registry = load_floor_rune_registry()
    runes = spawn_floor_rune(
        world,
        game_map,
        floor_depth=1,
        registry=registry,
        min_distance=5,
        min_pairwise=MIN_PAIRWISE_SPREAD_BFS,
        count=RUNES_PER_FLOOR,
    )
    positions = [(r.components[Position].x, r.components[Position].y) for r in runes]
    spread = min_pairwise_bfs_distance(
        game_map,
        positions,
        tile_predicate=lambda x, y: game_map.tiles[y, x] == Tile.FLOOR,
    )
    assert spread >= MIN_PAIRWISE_SPREAD_BFS


def test_all_placed_runes_are_at_least_twenty_from_entrance() -> None:
    import random

    for seed in range(10):
        dungeon = generate_dungeon(MAP_WIDTH, MAP_HEIGHT, seed=seed)
        world = Registry()
        try:
            runes = spawn_floor_rune(
                world,
                dungeon,
                floor_depth=1,
                rng=random.Random(seed),
            )
        except RunePlacementError:
            continue
        distances = bfs_path_distance_from(
            dungeon,
            dungeon.enter_xy,
            tile_filter=lambda x, y: dungeon.tiles[y, x] == Tile.FLOOR,
            cardinal_only=True,
        )
        for rune in runes:
            pos = rune.components[Position]
            assert distances.get((pos.x, pos.y), 0) >= MIN_PAIRWISE_SPREAD_BFS


def test_generated_maps_support_spread_rune_placement() -> None:
    """Rune spread on map geometry (no NPC/item blocking)."""
    import random

    successes = 0
    for seed in range(25):
        dungeon = generate_dungeon(MAP_WIDTH, MAP_HEIGHT, seed=seed)
        world = Registry()
        try:
            runes = spawn_floor_rune(
                world,
                dungeon,
                floor_depth=1,
                rng=random.Random(seed),
            )
        except RunePlacementError:
            continue
        if len(runes) != RUNES_PER_FLOOR:
            continue
        positions = [
            (entity.components[Position].x, entity.components[Position].y)
            for entity in runes
        ]
        spread = min_pairwise_bfs_distance(
            dungeon,
            positions,
            tile_predicate=lambda x, y: dungeon.tiles[y, x] == Tile.FLOOR,
        )
        if spread >= MIN_PAIRWISE_SPREAD_BFS:
            successes += 1
    assert successes >= 10


def test_initialize_floor_regenerates_on_rune_placement_failure() -> None:
    calls = {"spawn": 0, "dungeon": 0}
    original_spawn = GameEngine._spawn_floor_population_and_runes
    original_generate = generate_dungeon

    def counting_generate(*args, **kwargs):
        calls["dungeon"] += 1
        return original_generate(*args, **kwargs)

    def flaky_spawn(self, floor_depth, *, followers=None):
        calls["spawn"] += 1
        if calls["spawn"] == 1:
            raise RunePlacementError("mock failure")
        return original_spawn(self, floor_depth, followers=followers)

    from src.constants import DEFAULT_VORE_CONTENT_PREFS

    engine = GameEngine.__new__(GameEngine)
    engine.water_testing_mode = False
    engine.layout_archetype_force = None
    engine.player_turn_count = 0
    engine.floor_depth = 1
    engine.difficulty_id = "normal"
    engine.floor_prefetch = None
    engine.rng = __import__("random").Random(0)
    # initialize_floor / spawn path reads run prefs (GameEngine.__new__ skips __init__).
    engine.vore_content_prefs = DEFAULT_VORE_CONTENT_PREFS

    with (
        patch("src.engine_floor.generate_dungeon", side_effect=counting_generate),
        patch.object(GameEngine, "_spawn_floor_population_and_runes", flaky_spawn),
    ):
        engine.initialize_floor(seed=0, mode="new")

    assert calls["spawn"] == 2
    assert calls["dungeon"] >= 2
    assert engine.player is not None
    assert len(list(engine.world.Q.all_of(components=[FloorRune]))) == RUNES_PER_FLOOR


def test_pairwise_spread_failure_raises() -> None:
    world = Registry()
    from src.data.floor_rune_loader import load_floor_rune_registry

    registry = load_floor_rune_registry()
    game_map = rune_placement_arena(width=55, height=8)
    with pytest.raises(RunePlacementError, match="pairwise"):
        spawn_floor_rune(
            world,
            game_map,
            floor_depth=1,
            registry=registry,
            min_distance=1,
            min_pairwise=MIN_PAIRWISE_SPREAD_BFS,
            count=RUNES_PER_FLOOR,
        )