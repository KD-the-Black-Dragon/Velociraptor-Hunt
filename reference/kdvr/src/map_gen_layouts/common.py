"""Shared layout helpers for dungeon archetype generators."""

from __future__ import annotations

import random
from dataclasses import dataclass

from src.constants import (
    LAYOUT_ARCHETYPE_BOXY_WEIGHT,
    LAYOUT_ARCHETYPE_HYBRID_WEIGHT,
    LAYOUT_ARCHETYPE_ORGANIC_WEIGHT,
)
from src.map_gen import GameMap, Tile, tunnel_between

_CARDINAL: tuple[tuple[int, int], ...] = ((0, -1), (0, 1), (-1, 0), (1, 0))
_NEIGHBORS8: tuple[tuple[int, int], ...] = (
    (-1, -1),
    (0, -1),
    (1, -1),
    (-1, 0),
    (1, 0),
    (-1, 1),
    (0, 1),
    (1, 1),
)


@dataclass(frozen=True)
class LayoutRegion:
    """Axis-aligned region metadata for procedural layout carving."""

    center: tuple[int, int]
    x1: int
    y1: int
    x2: int
    y2: int

    def intersects(self, other: LayoutRegion, *, padding: int = 2) -> bool:
        return (
            self.x1 - padding <= other.x2
            and self.x2 + padding >= other.x1
            and self.y1 - padding <= other.y2
            and self.y2 + padding >= other.y1
        )

    def floor_count(self, game_map: GameMap) -> int:
        count = 0
        for y in range(self.y1, self.y2):
            for x in range(self.x1, self.x2):
                if game_map.in_bounds(x, y) and game_map.tiles[y, x] == Tile.FLOOR:
                    count += 1
        return count


def pick_layout_archetype(
    rng: random.Random,
    *,
    force: str | None = None,
) -> str:
    if force:
        return force
    roll = rng.random()
    if roll < LAYOUT_ARCHETYPE_BOXY_WEIGHT:
        return "boxy"
    if roll < LAYOUT_ARCHETYPE_BOXY_WEIGHT + LAYOUT_ARCHETYPE_ORGANIC_WEIGHT:
        return "organic"
    return "hybrid"


def carve_disk(game_map: GameMap, x: int, y: int, half_width: int) -> None:
    for dy in range(-half_width, half_width + 1):
        for dx in range(-half_width, half_width + 1):
            nx, ny = x + dx, y + dy
            if game_map.in_bounds(nx, ny):
                game_map.tiles[ny, nx] = Tile.FLOOR


def carve_tunnel(
    game_map: GameMap,
    start: tuple[int, int],
    end: tuple[int, int],
    rng: random.Random,
    *,
    half_width: int,
) -> None:
    for px, py in tunnel_between(start, end, rng):
        carve_disk(game_map, px, py, half_width)


def mst_edges(centers: list[tuple[int, int]]) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """Minimum spanning tree over region centers (Prim's, squared Euclidean weight)."""
    if len(centers) < 2:
        return []

    in_tree = {0}
    edges: list[tuple[tuple[int, int], tuple[int, int]]] = []

    while len(in_tree) < len(centers):
        best_dist = None
        best_edge: tuple[tuple[int, int], tuple[int, int]] | None = None
        for index in in_tree:
            origin = centers[index]
            for other_index, target in enumerate(centers):
                if other_index in in_tree:
                    continue
                dx = origin[0] - target[0]
                dy = origin[1] - target[1]
                dist = dx * dx + dy * dy
                if best_dist is None or dist < best_dist:
                    best_dist = dist
                    best_edge = (origin, target)
        if best_edge is None:
            break
        edges.append(best_edge)
        for other_index, target in enumerate(centers):
            if target == best_edge[1]:
                in_tree.add(other_index)
                break

    return edges


def connect_regions_mst(
    game_map: GameMap,
    regions: list[LayoutRegion],
    rng: random.Random,
    *,
    default_half_width: int = 0,
    wide_half_width: int = 1,
    wide_chance: float = 0.0,
) -> None:
    if len(regions) < 2:
        return
    centers = [region.center for region in regions]
    for start, end in mst_edges(centers):
        half_width = (
            wide_half_width
            if rng.random() < wide_chance
            else default_half_width
        )
        carve_tunnel(game_map, start, end, rng, half_width=half_width)


def count_wall_neighbors(game_map: GameMap, x: int, y: int) -> int:
    count = 0
    for dx, dy in _NEIGHBORS8:
        nx, ny = x + dx, y + dy
        if not game_map.in_bounds(nx, ny) or game_map.tiles[ny, nx] == Tile.WALL:
            count += 1
    return count


def carve_cellular_cavern(
    game_map: GameMap,
    rng: random.Random,
    *,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    fill_chance: float = 0.40,
    smoothing_passes: int | None = None,
) -> LayoutRegion:
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    for y in range(y1, y2):
        for x in range(x1, x2):
            game_map.tiles[y, x] = Tile.FLOOR if rng.random() < fill_chance else Tile.WALL

    passes = smoothing_passes if smoothing_passes is not None else rng.randint(4, 6)
    for _ in range(passes):
        snapshot = game_map.tiles.copy()
        for y in range(y1 + 1, y2 - 1):
            for x in range(x1 + 1, x2 - 1):
                walls = count_wall_neighbors(game_map, x, y)
                snapshot[y, x] = Tile.WALL if walls >= 5 else Tile.FLOOR
        game_map.tiles[y1:y2, x1:x2] = snapshot[y1:y2, x1:x2]

    game_map.tiles[cy, cx] = Tile.FLOOR
    return LayoutRegion((cx, cy), x1, y1, x2, y2)


def set_entrance_largest_region(game_map: GameMap, regions: list[LayoutRegion]) -> None:
    if not regions:
        return
    best = max(regions, key=lambda region: region.floor_count(game_map))
    game_map.enter_xy = best.center