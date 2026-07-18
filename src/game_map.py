"""Minimal tile grid for Gladiavore arenas (no dungeon generation)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum

import numpy as np
from numpy.typing import NDArray

from src.components import MobilityType


class Tile(IntEnum):
    WALL = 0
    FLOOR = 1
    DEEP_WATER = 2
    STAIRS_DOWN = 3
    DOOR_CLOSED = 4
    DOOR_OPEN = 5


_TRANSPARENT_TILES: frozenset[Tile] = frozenset({
    Tile.FLOOR,
    Tile.DEEP_WATER,
    Tile.STAIRS_DOWN,
    Tile.DOOR_OPEN,
})

_TRAVERSABLE_BY_MOBILITY: dict[MobilityType, frozenset[Tile]] = {
    MobilityType.GROUND: frozenset({Tile.FLOOR, Tile.STAIRS_DOWN, Tile.DOOR_OPEN}),
    MobilityType.FLY: frozenset({
        Tile.FLOOR,
        Tile.DEEP_WATER,
        Tile.STAIRS_DOWN,
        Tile.DOOR_OPEN,
    }),
    MobilityType.AQUATIC: frozenset({Tile.DEEP_WATER}),
    MobilityType.STATIONARY: frozenset({Tile.FLOOR, Tile.STAIRS_DOWN, Tile.DOOR_OPEN}),
}


def tile_at(game_map: GameMap, x: int, y: int) -> Tile | None:
    if not game_map.in_bounds(x, y):
        return None
    return Tile(game_map.tiles[y, x])


def is_transparent_tile(tile: Tile) -> bool:
    return tile in _TRANSPARENT_TILES


def can_enter_tile(
    game_map: GameMap,
    x: int,
    y: int,
    mobility: MobilityType,
) -> bool:
    tile = tile_at(game_map, x, y)
    if tile is None:
        return False
    return tile in _TRAVERSABLE_BY_MOBILITY[mobility]


@dataclass
class GameMap:
    """Tile grid with exploration / visibility flags."""

    width: int
    height: int
    tiles: NDArray[np.int8] = field(init=False)
    explored: NDArray[np.bool_] = field(init=False)
    visible: NDArray[np.bool_] = field(init=False)
    enter_xy: tuple[int, int] = (0, 0)
    layout_archetype: str = ""

    def __post_init__(self) -> None:
        self.tiles = np.full((self.height, self.width), Tile.WALL, dtype=np.int8)
        self.explored = np.zeros((self.height, self.width), dtype=bool)
        self.visible = np.zeros((self.height, self.width), dtype=bool)

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x: int, y: int) -> bool:
        return can_enter_tile(self, x, y, MobilityType.GROUND)

    def is_transparent(self, x: int, y: int) -> bool:
        tile = tile_at(self, x, y)
        return tile is not None and is_transparent_tile(tile)

    def reveal_all(self) -> None:
        self.explored[:] = True
        self.visible[:] = True
