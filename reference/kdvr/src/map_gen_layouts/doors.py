"""Procedural closed-door placement at corridor mouths."""

from __future__ import annotations

import random

from src.constants import DOOR_CHANCE_STDDEV, DOOR_CORRIDOR_MOUTH_CHANCE
from src.map_gen import GameMap, Tile, validate_land_connectivity

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

_LANDLIKE_TILES: frozenset[Tile] = frozenset({
    Tile.FLOOR,
    Tile.STAIRS_DOWN,
    Tile.DOOR_OPEN,
})

_DOOR_TILES: frozenset[Tile] = frozenset({Tile.DOOR_CLOSED, Tile.DOOR_OPEN})


def _is_landlike(tile: Tile) -> bool:
    return tile in _LANDLIKE_TILES


def _is_door(tile: Tile) -> bool:
    return tile in _DOOR_TILES


def _cardinal_landlike_directions(
    game_map: GameMap,
    x: int,
    y: int,
) -> list[tuple[int, int]]:
    directions: list[tuple[int, int]] = []
    for dx, dy in _CARDINAL:
        nx, ny = x + dx, y + dy
        if not game_map.in_bounds(nx, ny):
            continue
        if _is_landlike(Tile(game_map.tiles[ny, nx])):
            directions.append((dx, dy))
    return directions


def _directions_are_opposite(
    first: tuple[int, int],
    second: tuple[int, int],
) -> bool:
    return first[0] == -second[0] and first[1] == -second[1]


def _cardinal_landlike_count(game_map: GameMap, x: int, y: int) -> int:
    return len(_cardinal_landlike_directions(game_map, x, y))


def _cardinal_wall_count(game_map: GameMap, x: int, y: int) -> int:
    count = 0
    for dx, dy in _CARDINAL:
        nx, ny = x + dx, y + dy
        if not game_map.in_bounds(nx, ny):
            count += 1
            continue
        if Tile(game_map.tiles[ny, nx]) == Tile.WALL:
            count += 1
    return count


def _is_corridor_mouth(game_map: GameMap, x: int, y: int) -> bool:
    """True when a 1-wide corridor tile meets a wider room on the opposite side.

    Requires exactly two opposite land neighbors (corridor axis), at least two
    wall neighbors (corridor flanks), and openness <= 2 on the narrow side vs
    >= 4 on the room side. Excludes room interiors and corners.
    """
    if Tile(game_map.tiles[y, x]) != Tile.FLOOR:
        return False

    land_dirs = _cardinal_landlike_directions(game_map, x, y)
    if len(land_dirs) != 2:
        return False
    if not _directions_are_opposite(land_dirs[0], land_dirs[1]):
        return False
    if _cardinal_wall_count(game_map, x, y) < 2:
        return False

    first, second = land_dirs[0], land_dirs[1]
    fx, fy = x + first[0], y + first[1]
    sx, sy = x + second[0], y + second[1]
    first_open = _cardinal_landlike_count(game_map, fx, fy)
    second_open = _cardinal_landlike_count(game_map, sx, sy)
    return (first_open >= 4 and second_open <= 2) or (
        second_open >= 4 and first_open <= 2
    )


def find_corridor_mouth_tiles(game_map: GameMap) -> list[tuple[int, int]]:
    mouths: list[tuple[int, int]] = []
    for y in range(game_map.height):
        for x in range(game_map.width):
            if _is_corridor_mouth(game_map, x, y):
                mouths.append((x, y))
    return mouths


def _adjacent_door_pairs(
    game_map: GameMap,
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    doors = [
        (x, y)
        for y in range(game_map.height)
        for x in range(game_map.width)
        if _is_door(Tile(game_map.tiles[y, x]))
    ]
    seen: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    pairs: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for x, y in doors:
        for dx, dy in _NEIGHBORS8:
            nx, ny = x + dx, y + dy
            if not game_map.in_bounds(nx, ny):
                continue
            if not _is_door(Tile(game_map.tiles[ny, nx])):
                continue
            pair = tuple(sorted((((x, y), (nx, ny)))))
            if pair in seen:
                continue
            seen.add(pair)
            pairs.append((pair[0], pair[1]))
    return pairs


def _remove_adjacent_doors(game_map: GameMap, rng: random.Random) -> int:
    """Remove one door from each adjacent pair until none remain."""
    removed = 0
    while True:
        pairs = _adjacent_door_pairs(game_map)
        if not pairs:
            break
        first, second = rng.choice(pairs)
        rx, ry = rng.choice([first, second])
        game_map.tiles[ry, rx] = Tile.FLOOR
        removed += 1
    return removed


def place_doors(game_map: GameMap, rng: random.Random) -> int:
    """Place closed doors at corridor mouths; revert any that disconnect land."""
    mouths = find_corridor_mouth_tiles(game_map)
    if not mouths:
        return 0

    chance = max(
        0.25,
        min(0.75, rng.gauss(DOOR_CORRIDOR_MOUTH_CHANCE, DOOR_CHANCE_STDDEV)),
    )
    placed = 0
    for x, y in mouths:
        if rng.random() >= chance:
            continue
        game_map.tiles[y, x] = Tile.DOOR_CLOSED
        if validate_land_connectivity(game_map):
            placed += 1
        else:
            game_map.tiles[y, x] = Tile.FLOOR

    _remove_adjacent_doors(game_map, rng)
    return sum(
        1
        for y in range(game_map.height)
        for x in range(game_map.width)
        if _is_door(Tile(game_map.tiles[y, x]))
    )