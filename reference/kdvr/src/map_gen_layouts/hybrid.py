"""Hybrid layout: large organic zones plus rectangular rooms."""

from __future__ import annotations

import random

from src.map_gen import GameMap, Tile
from src.map_gen_layouts.boxy import _carve_rect_room
from src.map_gen_layouts.common import (
    LayoutRegion,
    carve_cellular_cavern,
    connect_regions_mst,
    set_entrance_largest_region,
)


def _hybrid_cavern_bounds(game_map: GameMap, rng: random.Random) -> LayoutRegion | None:
    width = rng.randint(12, 18)
    height = rng.randint(10, 14)
    if width + 4 >= game_map.width or height + 4 >= game_map.height:
        return None
    x1 = rng.randint(2, game_map.width - width - 3)
    y1 = rng.randint(2, game_map.height - height - 3)
    x2, y2 = x1 + width, y1 + height
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    return LayoutRegion((cx, cy), x1, y1, x2, y2)


def _carve_hybrid_cavern_at(
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
        fill_chance=0.41,
        smoothing_passes=4,
    )
    if region.floor_count(game_map) < width * height // 7:
        for y in range(bounds.y1, bounds.y2):
            for x in range(bounds.x1, bounds.x2):
                if game_map.in_bounds(x, y):
                    game_map.tiles[y, x] = Tile.WALL
        return None
    return region


def carve_hybrid_layout(
    game_map: GameMap,
    rng: random.Random,
    *,
    room_min_size: int,
    room_max_size: int,
) -> bool:
    regions: list[LayoutRegion] = []

    organic_target = rng.randint(2, 3)
    for _ in range(organic_target * 6):
        if len(regions) >= organic_target:
            break
        bounds = _hybrid_cavern_bounds(game_map, rng)
        if bounds is None:
            continue
        if any(bounds.intersects(existing, padding=3) for existing in regions):
            continue
        region = _carve_hybrid_cavern_at(game_map, rng, bounds)
        if region is None:
            continue
        regions.append(region)

    rect_target = rng.randint(2, 4)
    rect_count = 0
    for _ in range(rect_target * 6):
        if rect_count >= rect_target:
            break
        region = _carve_rect_room(
            game_map,
            rng,
            room_min=max(room_min_size, 7),
            room_max=room_max_size + 2,
        )
        if region is None:
            continue
        if any(region.intersects(existing, padding=2) for existing in regions):
            for y in range(region.y1, region.y2):
                for x in range(region.x1, region.x2):
                    if game_map.in_bounds(x, y) and game_map.tiles[y, x] == Tile.FLOOR:
                        game_map.tiles[y, x] = Tile.WALL
            continue
        regions.append(region)
        rect_count += 1

    if len(regions) < 4:
        return False

    connect_regions_mst(
        game_map,
        regions,
        rng,
        default_half_width=0,
        wide_half_width=1,
        wide_chance=0.35,
    )
    set_entrance_largest_region(game_map, regions)
    return True