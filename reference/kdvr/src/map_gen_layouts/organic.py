"""Organic dungeon layout: large caverns linked by narrow choke corridors."""

from __future__ import annotations

import random

from src.map_gen import (
    GameMap,
    Tile,
    validate_land_connectivity,
    _apply_water_cells,
    _grow_lake,
    _revert_water_cells,
)
from src.map_gen_layouts.common import (
    LayoutRegion,
    carve_cellular_cavern,
    connect_regions_mst,
    set_entrance_largest_region,
)


def _organic_cavern_bounds(game_map: GameMap, rng: random.Random) -> LayoutRegion | None:
    width = rng.randint(14, 22)
    height = rng.randint(12, 18)
    if width + 4 >= game_map.width or height + 4 >= game_map.height:
        return None
    x1 = rng.randint(2, game_map.width - width - 3)
    y1 = rng.randint(2, game_map.height - height - 3)
    x2, y2 = x1 + width, y1 + height
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    return LayoutRegion((cx, cy), x1, y1, x2, y2)


def _carve_organic_cavern_at(
    game_map: GameMap,
    rng: random.Random,
    bounds: LayoutRegion,
) -> LayoutRegion | None:
    width = bounds.x2 - bounds.x1
    height = bounds.y2 - bounds.y1
    region = carve_cellular_cavern(
        game_map,
        rng,
        x1=bounds.x1,
        y1=bounds.y1,
        x2=bounds.x2,
        y2=bounds.y2,
        fill_chance=0.39,
    )
    if region.floor_count(game_map) < width * height // 6:
        for y in range(bounds.y1, bounds.y2):
            for x in range(bounds.x1, bounds.x2):
                if game_map.in_bounds(x, y):
                    game_map.tiles[y, x] = Tile.WALL
        return None
    return region


def carve_organic_regions(
    game_map: GameMap,
    rng: random.Random,
) -> list[LayoutRegion]:
    """Place non-overlapping caverns; exposed for layout tests."""
    target_caverns = rng.randint(4, 6)
    regions: list[LayoutRegion] = []
    attempts = target_caverns * 8

    for _ in range(attempts):
        if len(regions) >= target_caverns:
            break
        bounds = _organic_cavern_bounds(game_map, rng)
        if bounds is None:
            continue
        if any(bounds.intersects(existing, padding=3) for existing in regions):
            continue
        region = _carve_organic_cavern_at(game_map, rng, bounds)
        if region is None:
            continue
        regions.append(region)

    return regions


def _try_cavern_lakes(
    game_map: GameMap,
    regions: list[LayoutRegion],
    rng: random.Random,
) -> None:
    lake_count = rng.randint(0, 2)
    if lake_count <= 0 or not regions:
        return

    for region in rng.sample(regions, min(lake_count, len(regions))):
        floors = [
            (x, y)
            for y in range(region.y1 + 1, region.y2 - 1)
            for x in range(region.x1 + 1, region.x2 - 1)
            if game_map.tiles[y, x] == Tile.FLOOR
        ]
        if len(floors) < 30:
            continue
        max_lake = min(80, len(floors) // 2)
        if max_lake < 18:
            continue
        for _ in range(4):
            seed = rng.choice(floors)
            lake = _grow_lake(
                game_map,
                seed,
                rng,
                min_size=18,
                max_size=max_lake,
            )
            if len(lake) < 18:
                continue
            _apply_water_cells(game_map, lake)
            if validate_land_connectivity(game_map):
                break
            _revert_water_cells(game_map, lake)


def carve_organic_layout(game_map: GameMap, rng: random.Random) -> bool:
    regions = carve_organic_regions(game_map, rng)
    if len(regions) < 4:
        return False

    connect_regions_mst(game_map, regions, rng, default_half_width=0)
    _try_cavern_lakes(game_map, regions, rng)
    set_entrance_largest_region(game_map, regions)
    return True