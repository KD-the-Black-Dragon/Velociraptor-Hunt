"""Good NPC spawn quota: difficulty limit, followers, density exclusion."""

from __future__ import annotations

import random

from tcod.ecs import Registry

from src.components import Alignment, NPCAlignment, Position
from src.constants import GOOD_SPAWN_PATH_MAX, GOOD_SPAWN_PATH_MIN
from src.data.depth_scaling_loader import parse_depth_scaling_config
from src.map_gen import GameMap, Tile
from src.spawn import (
    eligible_good_definitions,
    filter_tiles_by_path_band,
    good_spawn_count_to_place,
    player_path_distances,
    spawn_floor_population,
    valid_spawn_tiles,
)
from src.data.entity_loader import parse_entity_registry
from tests.spawn_test_helpers import (
    expected_spawn_count,
    fixed_spawn_config,
    fixture_depth_scaling_config,
    fixture_difficulty_profile,
)
from tests.test_npc_data_pr1 import _minimal_entity


def _open_map() -> GameMap:
    game_map = GameMap(40, 40)
    game_map.tiles[:, :] = Tile.FLOOR
    game_map.enter_xy = (20, 20)
    return game_map


def _registry_with_goods(*, good_min: int = 1, good_max: int = 10) -> object:
    payload = {
        "schema_version": 1,
        "entities": [
            _minimal_entity(
                id="evil_a",
                display_name="evil a",
                alignment="evil",
                spawn={"weight": 5, "min_depth": 1, "max_depth": 100, "terrain": "land"},
            ),
            _minimal_entity(
                id="good_a",
                display_name="good a",
                alignment="good",
                spawn={
                    "weight": 3,
                    "min_depth": good_min,
                    "max_depth": good_max,
                    "terrain": "land",
                },
            ),
            _minimal_entity(
                id="good_b",
                display_name="good b",
                alignment="good",
                spawn={
                    "weight": 1,
                    "min_depth": good_min,
                    "max_depth": good_max,
                    "terrain": "land",
                },
            ),
        ],
    }
    return parse_entity_registry(payload)


def _count_goods(entities: list) -> int:
    n = 0
    for entity in entities:
        align = entity.components.get(NPCAlignment)
        if align is not None and align.alignment == Alignment.GOOD:
            n += 1
    return n


def test_good_spawn_count_to_place_cap_semantics() -> None:
    assert good_spawn_count_to_place(limit=2, brought=0, has_eligible_goods=True) == 2
    assert good_spawn_count_to_place(limit=2, brought=1, has_eligible_goods=True) == 1
    assert good_spawn_count_to_place(limit=2, brought=2, has_eligible_goods=True) == 0
    assert good_spawn_count_to_place(limit=2, brought=5, has_eligible_goods=True) == 0
    assert good_spawn_count_to_place(limit=3, brought=0, has_eligible_goods=True) == 3
    assert good_spawn_count_to_place(limit=2, brought=0, has_eligible_goods=False) == 0
    assert good_spawn_count_to_place(limit=0, brought=0, has_eligible_goods=True) == 0


def test_no_eligible_goods_spawns_zero_goods() -> None:
    reg = _registry_with_goods(good_min=5, good_max=10)
    game_map = _open_map()
    config = fixed_spawn_config(density_pct=0.15, density_variance=0.0, max_npcs=8)
    scaling = fixture_depth_scaling_config(
        fixture_difficulty_profile(good_spawn_limit=2)
    )
    density = expected_spawn_count(game_map, 20, 20, floor_depth=1, config=config, rng_seed=1)
    world = Registry()
    spawned = spawn_floor_population(
        world,
        game_map,
        20,
        20,
        floor_depth=1,
        rng=random.Random(1),
        registry=reg,
        spawn_config=config,
        depth_scaling=scaling,
        difficulty_id="test",
    )
    assert _count_goods(spawned) == 0
    assert len(spawned) == density


def test_quota_fills_with_zero_followers() -> None:
    reg = _registry_with_goods()
    game_map = _open_map()
    config = fixed_spawn_config(density_pct=0.1, density_variance=0.0, max_npcs=5)
    scaling = fixture_depth_scaling_config(
        fixture_difficulty_profile(good_spawn_limit=2)
    )
    world = Registry()
    spawned = spawn_floor_population(
        world,
        game_map,
        20,
        20,
        floor_depth=1,
        rng=random.Random(2),
        registry=reg,
        spawn_config=config,
        depth_scaling=scaling,
        difficulty_id="test",
        good_followers_brought=0,
    )
    assert _count_goods(spawned) == 2
    distances = player_path_distances(game_map, 20, 20)
    for entity in spawned:
        align = entity.components.get(NPCAlignment)
        if align is None or align.alignment != Alignment.GOOD:
            continue
        pos = entity.components[Position]
        dist = distances[(pos.x, pos.y)]
        assert GOOD_SPAWN_PATH_MIN <= dist <= GOOD_SPAWN_PATH_MAX


def test_quota_with_one_follower() -> None:
    reg = _registry_with_goods()
    game_map = _open_map()
    config = fixed_spawn_config(density_pct=0.1, density_variance=0.0, max_npcs=5)
    scaling = fixture_depth_scaling_config(
        fixture_difficulty_profile(good_spawn_limit=2)
    )
    world = Registry()
    spawned = spawn_floor_population(
        world,
        game_map,
        20,
        20,
        floor_depth=1,
        rng=random.Random(3),
        registry=reg,
        spawn_config=config,
        depth_scaling=scaling,
        difficulty_id="test",
        good_followers_brought=1,
    )
    assert _count_goods(spawned) == 1


def test_quota_at_or_over_limit_spawns_no_new_goods() -> None:
    reg = _registry_with_goods()
    game_map = _open_map()
    config = fixed_spawn_config(density_pct=0.1, density_variance=0.0, max_npcs=5)
    scaling = fixture_depth_scaling_config(
        fixture_difficulty_profile(good_spawn_limit=2)
    )
    for brought in (2, 4):
        world = Registry()
        spawned = spawn_floor_population(
            world,
            game_map,
            20,
            20,
            floor_depth=1,
            rng=random.Random(4 + brought),
            registry=reg,
            spawn_config=config,
            depth_scaling=scaling,
            difficulty_id="test",
            good_followers_brought=brought,
        )
        assert _count_goods(spawned) == 0


def test_easier_limit_three() -> None:
    reg = _registry_with_goods()
    game_map = _open_map()
    config = fixed_spawn_config(density_pct=0.1, density_variance=0.0, max_npcs=5)
    scaling = fixture_depth_scaling_config(
        fixture_difficulty_profile(difficulty_id="easier", good_spawn_limit=3)
    )
    world = Registry()
    spawned = spawn_floor_population(
        world,
        game_map,
        20,
        20,
        floor_depth=1,
        rng=random.Random(9),
        registry=reg,
        spawn_config=config,
        depth_scaling=scaling,
        difficulty_id="easier",
        good_followers_brought=0,
    )
    assert _count_goods(spawned) == 3


def test_density_pass_never_spawns_goods() -> None:
    """Even with high density, only the quota creates goods."""
    reg = _registry_with_goods()
    game_map = _open_map()
    config = fixed_spawn_config(density_pct=1.0, density_variance=0.0, max_npcs=20)
    scaling = fixture_depth_scaling_config(
        fixture_difficulty_profile(good_spawn_limit=2)
    )
    world = Registry()
    spawned = spawn_floor_population(
        world,
        game_map,
        20,
        20,
        floor_depth=1,
        rng=random.Random(11),
        registry=reg,
        spawn_config=config,
        depth_scaling=scaling,
        difficulty_id="test",
        good_followers_brought=0,
    )
    assert _count_goods(spawned) == 2
    # Density filled beyond quota
    assert len(spawned) > 2


def test_eligible_good_definitions_requires_tiles() -> None:
    reg = _registry_with_goods()
    game_map = _open_map()
    land, water = valid_spawn_tiles(game_map, 20, 20)
    goods = eligible_good_definitions(
        reg,
        floor_depth=1,
        map_has_water=False,
        land_cands=land,
        water_place_pool=[],
    )
    assert {d.id for d in goods} == {"good_a", "good_b"}
    empty = eligible_good_definitions(
        reg,
        floor_depth=1,
        map_has_water=False,
        land_cands=[],
        water_place_pool=[],
    )
    assert empty == []


def test_stock_depth_scaling_good_spawn_limits() -> None:
    from src.data.depth_scaling_loader import default_depth_scaling_config

    cfg = default_depth_scaling_config()
    assert cfg.profile_for("easier").good_spawn_limit == 3
    assert cfg.profile_for("normal").good_spawn_limit == 2
    assert cfg.profile_for("hard").good_spawn_limit == 2
    assert cfg.profile_for("nightmare").good_spawn_limit == 2


def test_good_spawn_limit_omitted_defaults_to_two() -> None:
    raw = {
        "schema_version": 1,
        "default_difficulty_id": "solo",
        "difficulties": {
            "solo": {
                "display_name": "Solo",
                "apply_to_alignments": ["evil"],
                "stats": {},
            }
        },
    }
    cfg = parse_depth_scaling_config(raw)
    assert cfg.profile_for("solo").good_spawn_limit == 2


def test_filter_tiles_by_path_band() -> None:
    distances = {
        (0, 0): 0,
        (5, 0): 5,
        (10, 0): 10,
        (12, 0): 12,
        (15, 0): 15,
        (16, 0): 16,
    }
    tiles = list(distances.keys())
    band = filter_tiles_by_path_band(tiles, distances)
    assert set(band) == {(10, 0), (12, 0), (15, 0)}


def test_closed_doors_count_as_path_steps() -> None:
    """Closed doors are walkable for band distance (player can open them)."""
    game_map = GameMap(20, 5)
    game_map.tiles[:, :] = Tile.WALL
    # Horizontal corridor with a closed door at x=5
    for x in range(1, 19):
        game_map.tiles[2, x] = Tile.FLOOR
    game_map.tiles[2, 5] = Tile.DOOR_CLOSED
    distances = player_path_distances(game_map, 1, 2)
    # Path continues through the door
    assert distances.get((6, 2)) == 5
    assert distances.get((11, 2)) == 10


def test_no_band_tiles_spawns_zero_goods() -> None:
    """Tiny map with no tiles at path 10–15 cannot place new goods."""
    reg = _registry_with_goods()
    game_map = GameMap(12, 12)
    game_map.tiles[:, :] = Tile.FLOOR
    game_map.enter_xy = (6, 6)
    # Max Chebyshev from center on 12x12 is 6 — no path 10–15 tiles
    config = fixed_spawn_config(density_pct=0.2, density_variance=0.0, max_npcs=4)
    scaling = fixture_depth_scaling_config(
        fixture_difficulty_profile(good_spawn_limit=2)
    )
    world = Registry()
    spawned = spawn_floor_population(
        world,
        game_map,
        6,
        6,
        floor_depth=1,
        rng=random.Random(0),
        registry=reg,
        spawn_config=config,
        depth_scaling=scaling,
        difficulty_id="test",
        good_followers_brought=0,
    )
    assert _count_goods(spawned) == 0
