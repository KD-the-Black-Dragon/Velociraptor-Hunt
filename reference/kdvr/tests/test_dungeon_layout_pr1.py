"""PR1: layout archetypes (boxy / organic / hybrid) and F4 force modes."""

from __future__ import annotations

import random

from src.constants import MAP_HEIGHT, MAP_WIDTH, MIN_LAND_TILE_COUNT
from src.map_gen import GameMap, Tile, count_land_tiles, generate_dungeon, validate_min_land_tiles
from src.map_gen_layouts import pick_layout_archetype
from src.map_gen_layouts.common import LayoutRegion
from src.map_gen_layouts.organic import carve_organic_regions


def test_pick_layout_archetype_respects_force() -> None:
    assert pick_layout_archetype(random.Random(1), force="organic") == "organic"
    assert pick_layout_archetype(random.Random(1), force="boxy") == "boxy"
    assert pick_layout_archetype(random.Random(1), force="hybrid") == "hybrid"


def test_forced_archetypes_set_layout_field() -> None:
    for archetype in ("boxy", "organic", "hybrid"):
        dungeon = generate_dungeon(
            MAP_WIDTH,
            MAP_HEIGHT,
            seed=7,
            layout_archetype_force=archetype,
        )
        assert dungeon.layout_archetype == archetype
        assert validate_min_land_tiles(dungeon)


def test_organic_carves_at_least_four_regions() -> None:
    for seed in range(60):
        game_map = GameMap(MAP_WIDTH, MAP_HEIGHT)
        regions = carve_organic_regions(game_map, random.Random(seed))
        if len(regions) < 4:
            continue
        for region in regions:
            assert isinstance(region, LayoutRegion)
            assert region.floor_count(game_map) > 0
        return
    raise AssertionError("no seed produced four organic caverns in 60 attempts")


def test_organic_forced_has_large_open_areas() -> None:
    dungeon = generate_dungeon(
        MAP_WIDTH,
        MAP_HEIGHT,
        seed=11,
        layout_archetype_force="organic",
    )
    assert dungeon.layout_archetype == "organic"
    assert count_land_tiles(dungeon) >= MIN_LAND_TILE_COUNT
    floor_count = sum(
        1
        for y in range(dungeon.height)
        for x in range(dungeon.width)
        if dungeon.tiles[y, x] == Tile.FLOOR
    )
    assert floor_count >= MIN_LAND_TILE_COUNT // 2


def test_boxy_forced_generates_valid_floor() -> None:
    dungeon = generate_dungeon(
        MAP_WIDTH,
        MAP_HEIGHT,
        seed=3,
        layout_archetype_force="boxy",
    )
    assert dungeon.layout_archetype == "boxy"
    assert count_land_tiles(dungeon) >= MIN_LAND_TILE_COUNT


def test_default_mix_includes_all_archetypes() -> None:
    seen: set[str] = set()
    for seed in range(40):
        dungeon = generate_dungeon(MAP_WIDTH, MAP_HEIGHT, seed=seed)
        seen.add(dungeon.layout_archetype)
    assert "boxy" in seen
    assert "organic" in seen
    assert "hybrid" in seen