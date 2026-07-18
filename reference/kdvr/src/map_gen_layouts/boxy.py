"""Boxy dungeon layout: rectangular rooms and varied corridor widths."""

from __future__ import annotations

import random

from src.map_gen import GameMap, Tile
from src.map_gen_layouts.common import (
    LayoutRegion,
    carve_tunnel,
    connect_regions_mst,
    set_entrance_largest_region,
)


class RectangularRoom:
    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> tuple[int, int]:
        return (self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2

    @property
    def inner(self) -> tuple[slice, slice]:
        return slice(self.y1 + 1, self.y2), slice(self.x1 + 1, self.x2)


def _carve_rect_room(
    game_map: GameMap,
    rng: random.Random,
    *,
    room_min: int,
    room_max: int,
) -> LayoutRegion | None:
    room_w = rng.randint(room_min, room_max)
    room_h = rng.randint(room_min, room_max)
    if room_w + 2 >= game_map.width or room_h + 2 >= game_map.height:
        return None
    x = rng.randint(1, game_map.width - room_w - 2)
    y = rng.randint(1, game_map.height - room_h - 2)
    room = RectangularRoom(x, y, room_w, room_h)
    game_map.tiles[room.inner] = Tile.FLOOR
    return LayoutRegion(room.center, room.x1, room.y1, room.x2, room.y2)


def _carve_small_blob(game_map: GameMap, rng: random.Random) -> LayoutRegion | None:
    radius = rng.randint(4, 6)
    cx = rng.randint(radius + 1, game_map.width - radius - 2)
    cy = rng.randint(radius + 1, game_map.height - radius - 2)
    x1, y1 = cx - radius, cy - radius
    x2, y2 = cx + radius + 1, cy + radius + 1
    x, y = cx, cy
    game_map.tiles[y, x] = Tile.FLOOR
    steps = rng.randint(radius * radius * 2, radius * radius * 4)
    for _ in range(steps):
        dx, dy = rng.choice(((0, -1), (0, 1), (-1, 0), (1, 0)))
        x = max(x1, min(x2 - 1, x + dx))
        y = max(y1, min(y2 - 1, y + dy))
        game_map.tiles[y, x] = Tile.FLOOR
    return LayoutRegion((cx, cy), x1, y1, x2, y2)


def carve_boxy_layout(
    game_map: GameMap,
    rng: random.Random,
    *,
    max_rooms: int,
    room_min_size: int,
    room_max_size: int,
) -> bool:
    regions: list[LayoutRegion] = []
    placement_attempts = max_rooms * 2

    for _ in range(placement_attempts):
        if len(regions) >= max_rooms:
            break

        if rng.random() < 0.92:
            region = _carve_rect_room(
                game_map,
                rng,
                room_min=room_min_size,
                room_max=room_max_size,
            )
        else:
            region = _carve_small_blob(game_map, rng)

        if region is None:
            continue
        if any(region.intersects(existing) for existing in regions):
            for y in range(region.y1, region.y2):
                for x in range(region.x1, region.x2):
                    if (
                        game_map.in_bounds(x, y)
                        and game_map.tiles[y, x] == Tile.FLOOR
                    ):
                        game_map.tiles[y, x] = Tile.WALL
            continue

        if regions:
            anchor = rng.choice(regions)
            half_width = (
                rng.randint(1, 2)
                if rng.random() < 0.45
                else rng.randint(0, 1)
            )
            carve_tunnel(
                game_map,
                anchor.center,
                region.center,
                rng,
                half_width=half_width,
            )
        regions.append(region)

    if not regions:
        return False

    connect_regions_mst(
        game_map,
        regions,
        rng,
        default_half_width=0,
        wide_half_width=2,
        wide_chance=0.18,
    )
    set_entrance_largest_region(game_map, regions)
    return True