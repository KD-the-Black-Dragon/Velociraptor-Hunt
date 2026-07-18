from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Iterator

import numpy as np
import tcod.los
from numpy.typing import NDArray

from src.components import MobilityType
from src.debug_log import debug_print
from src.constants import (
    MAX_GEN_ATTEMPTS,
    MIN_LAND_TILE_COUNT,
    MIN_PAIRWISE_SPREAD_BFS,
    MIN_SPAWN_CANDIDATE_COUNT,
    MONSTER_SPAWN_MIN_DISTANCE,
    RUNES_PER_FLOOR,
    WATER_FEATURE_CHANCE,
    WATER_LAKE_ATTEMPTS,
    WATER_MIN_FEATURE_SIZE,
    WATER_PLACEMENT_RETRIES,
    WATER_RIVER_CHANCE,
    WATER_TESTING_FEATURE_CHANCE,
    WATER_TESTING_LAKE_ATTEMPTS,
    WATER_TESTING_MIN_FEATURE_SIZE,
    WATER_TESTING_PLACEMENT_RETRIES,
    WATER_TESTING_RIVER_CHANCE,
)

STAIRS_PER_FLOOR = 3

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


class Tile(IntEnum):
    """Static map tile types."""

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
    MobilityType.GROUND: frozenset({
        Tile.FLOOR,
        Tile.STAIRS_DOWN,
        Tile.DOOR_OPEN,
    }),
    MobilityType.FLY: frozenset({
        Tile.FLOOR,
        Tile.DEEP_WATER,
        Tile.STAIRS_DOWN,
        Tile.DOOR_OPEN,
    }),
    MobilityType.AQUATIC: frozenset({Tile.DEEP_WATER}),
    MobilityType.STATIONARY: frozenset({
        Tile.FLOOR,
        Tile.STAIRS_DOWN,
        Tile.DOOR_OPEN,
    }),
}

_LAND_TILES: frozenset[Tile] = frozenset({
    Tile.FLOOR,
    Tile.STAIRS_DOWN,
    Tile.DOOR_OPEN,
})

_CONNECTIVITY_LAND_TILES: frozenset[Tile] = _LAND_TILES | frozenset({Tile.DOOR_CLOSED})


def tile_at(game_map: GameMap, x: int, y: int) -> Tile | None:
    if not game_map.in_bounds(x, y):
        return None
    return Tile(game_map.tiles[y, x])


def is_transparent_tile(tile: Tile) -> bool:
    return tile in _TRANSPARENT_TILES


def is_land_tile(tile: Tile) -> bool:
    return tile in _LAND_TILES


def is_connectivity_land_tile(tile: Tile) -> bool:
    """Land tiles plus closed doors for topology checks (doors can be opened)."""
    return tile in _CONNECTIVITY_LAND_TILES


def can_enter_tile(
    game_map: GameMap,
    x: int,
    y: int,
    mobility: MobilityType,
) -> bool:
    """Return True when `mobility` may enter the tile (ignoring entities)."""
    tile = tile_at(game_map, x, y)
    if tile is None:
        return False
    return tile in _TRAVERSABLE_BY_MOBILITY[mobility]


@dataclass
class GameMap:
    """Dungeon tile grid with exploration and visibility state."""

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
        """Ground traversal (floor and downstairs)."""
        return can_enter_tile(self, x, y, MobilityType.GROUND)

    def is_transparent(self, x: int, y: int) -> bool:
        tile = tile_at(self, x, y)
        return tile is not None and is_transparent_tile(tile)

    def reveal_all(self) -> None:
        """Mark every tile explored and visible (used before FOV is implemented)."""
        self.explored[:] = True
        self.visible[:] = True

    def apply_dimming_demo(self, center_x: int, center_y: int, radius: int = 12) -> None:
        """Explored everywhere; only a circular region stays brightly visible."""
        self.explored[:] = True
        self.visible[:] = False
        radius_sq = radius * radius
        for y in range(self.height):
            for x in range(self.width):
                dx = x - center_x
                dy = y - center_y
                if dx * dx + dy * dy <= radius_sq and self.is_transparent(x, y):
                    self.visible[y, x] = True
        for y in range(self.height):
            for x in range(self.width):
                if self.tiles[y, x] == Tile.WALL and self._adjacent_to_visible_open(x, y):
                    self.visible[y, x] = True

    def _adjacent_to_visible_open(self, x: int, y: int) -> bool:
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if self.in_bounds(nx, ny) and self.visible[ny, nx] and self.is_transparent(nx, ny):
                return True
        return False


@dataclass(frozen=True)
class _Region:
    center: tuple[int, int]
    x1: int
    y1: int
    x2: int
    y2: int

    def intersects(self, other: _Region, *, padding: int = 1) -> bool:
        return (
            self.x1 - padding <= other.x2
            and self.x2 + padding >= other.x1
            and self.y1 - padding <= other.y2
            and self.y2 + padding >= other.y1
        )


class RectangularRoom:
    """Axis-aligned room used for dungeon generation."""

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
        """Inner floor area as slices for tiles[y, x] indexing."""
        return slice(self.y1 + 1, self.y2), slice(self.x1 + 1, self.x2)

    def intersects(self, other: RectangularRoom) -> bool:
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )


def tunnel_between(
    start: tuple[int, int],
    end: tuple[int, int],
    rng: random.Random,
) -> Iterator[tuple[int, int]]:
    """Yield points along an L-shaped tunnel between two room centers."""
    x1, y1 = start
    x2, y2 = end
    if rng.random() < 0.5:
        corner_x, corner_y = x2, y1
    else:
        corner_x, corner_y = x1, y2

    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y


def land_positions(game_map: GameMap) -> list[tuple[int, int]]:
    """Return all floor and downstairs tile coordinates."""
    coords: list[tuple[int, int]] = []
    for y in range(game_map.height):
        for x in range(game_map.width):
            if is_land_tile(Tile(game_map.tiles[y, x])):
                coords.append((x, y))
    return coords


def water_positions(game_map: GameMap) -> list[tuple[int, int]]:
    coords: list[tuple[int, int]] = []
    for y in range(game_map.height):
        for x in range(game_map.width):
            if game_map.tiles[y, x] == Tile.DEEP_WATER:
                coords.append((x, y))
    return coords


def door_positions(game_map: GameMap) -> list[tuple[int, int]]:
    coords: list[tuple[int, int]] = []
    for y in range(game_map.height):
        for x in range(game_map.width):
            tile = Tile(game_map.tiles[y, x])
            if tile in (Tile.DOOR_CLOSED, Tile.DOOR_OPEN):
                coords.append((x, y))
    return coords


def stairs_positions(game_map: GameMap) -> list[tuple[int, int]]:
    coords: list[tuple[int, int]] = []
    for y in range(game_map.height):
        for x in range(game_map.width):
            if game_map.tiles[y, x] == Tile.STAIRS_DOWN:
                coords.append((x, y))
    return coords


def land_reachable_from(
    game_map: GameMap,
    origin: tuple[int, int],
) -> set[tuple[int, int]]:
    """BFS over land tiles (8-directional) from origin."""
    return _reachable_from(
        game_map,
        origin,
        tile_test=is_land_tile,
    )


def connectivity_land_positions(game_map: GameMap) -> list[tuple[int, int]]:
    """Return floor, stairs, open doors, and closed doors."""
    coords: list[tuple[int, int]] = []
    for y in range(game_map.height):
        for x in range(game_map.width):
            if is_connectivity_land_tile(Tile(game_map.tiles[y, x])):
                coords.append((x, y))
    return coords


def connectivity_land_reachable_from(
    game_map: GameMap,
    origin: tuple[int, int],
) -> set[tuple[int, int]]:
    """BFS treating closed doors as connected (openable) for topology validation."""
    return _reachable_from(
        game_map,
        origin,
        tile_test=is_connectivity_land_tile,
    )


def _reachable_from(
    game_map: GameMap,
    origin: tuple[int, int],
    *,
    tile_test,
) -> set[tuple[int, int]]:
    ox, oy = origin
    if not game_map.in_bounds(ox, oy) or not tile_test(Tile(game_map.tiles[oy, ox])):
        return set()

    visited: set[tuple[int, int]] = {(ox, oy)}
    queue: deque[tuple[int, int]] = deque([(ox, oy)])
    while queue:
        x, y = queue.popleft()
        for dx, dy in _NEIGHBORS8:
            nx, ny = x + dx, y + dy
            if not game_map.in_bounds(nx, ny):
                continue
            if (nx, ny) in visited:
                continue
            if not tile_test(Tile(game_map.tiles[ny, nx])):
                continue
            visited.add((nx, ny))
            queue.append((nx, ny))
    return visited


def validate_land_connectivity(game_map: GameMap) -> bool:
    """True when every land tile is reachable from enter_xy.

    Closed doors count as connected because the player can open them.
    """
    all_land = set(connectivity_land_positions(game_map))
    if not all_land:
        return False
    if game_map.enter_xy not in all_land:
        return False
    reachable = connectivity_land_reachable_from(game_map, game_map.enter_xy)
    return reachable == all_land


def validate_stairs_reachable(game_map: GameMap) -> bool:
    """True when every downstairs tile is reachable from the entrance."""
    reachable = connectivity_land_reachable_from(game_map, game_map.enter_xy)
    return all(stair in reachable for stair in stairs_positions(game_map))


def _is_traversable_land_tile(game_map: GameMap, x: int, y: int) -> bool:
    if not game_map.in_bounds(x, y):
        return False
    return is_land_tile(Tile(game_map.tiles[y, x]))


def _is_rune_floor_tile(game_map: GameMap, x: int, y: int) -> bool:
    if not game_map.in_bounds(x, y):
        return False
    return game_map.tiles[y, x] == Tile.FLOOR


def build_mobility_walk_mask(
    game_map: GameMap,
    mobility: MobilityType,
    *,
    include_closed_doors: bool = False,
) -> NDArray[np.bool_]:
    """Boolean grid of tiles passable for `mobility` (optional closed doors)."""
    allowed = _TRAVERSABLE_BY_MOBILITY[mobility]
    mask = np.isin(game_map.tiles, np.fromiter((int(t) for t in allowed), dtype=np.int8))
    if include_closed_doors:
        mask = mask | (game_map.tiles == int(Tile.DOOR_CLOSED))
    return mask


def bfs_path_distances_from_mask(
    origin: tuple[int, int],
    mask: NDArray[np.bool_],
    *,
    cardinal_only: bool = True,
) -> dict[tuple[int, int], int]:
    """Shortest path distances from origin over True cells in `mask` (array BFS)."""
    height, width = mask.shape
    ox, oy = origin
    if ox < 0 or oy < 0 or ox >= width or oy >= height or not mask[oy, ox]:
        return {}

    directions = _CARDINAL if cardinal_only else _NEIGHBORS8
    # -1 = unvisited; array membership is faster than dict probes in the inner loop.
    dist = np.full((height, width), -1, dtype=np.int32)
    dist[oy, ox] = 0
    queue: deque[tuple[int, int]] = deque([(ox, oy)])
    distances: dict[tuple[int, int], int] = {(ox, oy): 0}

    while queue:
        x, y = queue.popleft()
        current = int(dist[y, x])
        next_d = current + 1
        for dx, dy in directions:
            nx = x + dx
            ny = y + dy
            if nx < 0 or ny < 0 or nx >= width or ny >= height:
                continue
            if not mask[ny, nx] or dist[ny, nx] >= 0:
                continue
            dist[ny, nx] = next_d
            distances[(nx, ny)] = next_d
            queue.append((nx, ny))

    return distances


def bfs_path_distances(
    game_map: GameMap,
    origin: tuple[int, int],
    *,
    tile_predicate,
    cardinal_only: bool = True,
) -> dict[tuple[int, int], int]:
    """Shortest path distances from origin over tiles passing `tile_predicate`."""
    ox, oy = origin
    if not game_map.in_bounds(ox, oy) or not tile_predicate(ox, oy):
        return {}

    directions = _CARDINAL if cardinal_only else _NEIGHBORS8
    distances: dict[tuple[int, int], int] = {(ox, oy): 0}
    queue: deque[tuple[int, int]] = deque([(ox, oy)])

    while queue:
        x, y = queue.popleft()
        current = distances[(x, y)]
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if not game_map.in_bounds(nx, ny):
                continue
            if not tile_predicate(nx, ny):
                continue
            if (nx, ny) in distances:
                continue
            distances[(nx, ny)] = current + 1
            queue.append((nx, ny))

    return distances


def min_pairwise_bfs_distance(
    game_map: GameMap,
    positions: list[tuple[int, int]],
    *,
    tile_predicate,
) -> int:
    """Minimum BFS distance among all pairs; 0 when any pair is unreachable."""
    if len(positions) < 2:
        return MIN_PAIRWISE_SPREAD_BFS

    minimum = MIN_PAIRWISE_SPREAD_BFS
    for index, start in enumerate(positions):
        distances = bfs_path_distances(
            game_map,
            start,
            tile_predicate=tile_predicate,
            cardinal_only=True,
        )
        for other in positions[index + 1 :]:
            distance = distances.get(other)
            if distance is None:
                return 0
            minimum = min(minimum, distance)
    return minimum


def count_land_tiles(game_map: GameMap) -> int:
    return len(land_positions(game_map))


def validate_min_land_tiles(game_map: GameMap, *, minimum: int = MIN_LAND_TILE_COUNT) -> bool:
    return count_land_tiles(game_map) >= minimum


def validate_pairwise_spread(
    game_map: GameMap,
    positions: list[tuple[int, int]],
    *,
    minimum: int = MIN_PAIRWISE_SPREAD_BFS,
    floor_only: bool = False,
) -> bool:
    if len(positions) < 2:
        return True

    if floor_only:
        predicate = lambda x, y: _is_rune_floor_tile(game_map, x, y)
    else:
        predicate = lambda x, y: _is_traversable_land_tile(game_map, x, y)
    return min_pairwise_bfs_distance(
        game_map,
        positions,
        tile_predicate=predicate,
    ) >= minimum


def validate_rune_sites_feasible(
    game_map: GameMap,
    *,
    count: int = RUNES_PER_FLOOR,
    minimum: int = MIN_PAIRWISE_SPREAD_BFS,
) -> bool:
    """True when `count` FLOOR tiles exist with pairwise BFS distance >= minimum."""
    ex, ey = game_map.enter_xy
    candidates = [
        (x, y)
        for x, y in _floor_positions(game_map)
        if (x, y) != (ex, ey)
    ]
    return _can_select_spread_positions(
        game_map,
        candidates,
        count,
        minimum,
        tile_predicate=lambda x, y: _is_rune_floor_tile(game_map, x, y),
    )


def _debug_log_map_reject(attempt: int, reason: str) -> None:
    debug_print(f"[map_gen] rejected attempt {attempt}: {reason}", flush=True)


def _chebyshev_distance(a: tuple[int, int], b: tuple[int, int]) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def _min_distance_to_placed(
    candidate: tuple[int, int],
    placed_distance_maps: list[dict[tuple[int, int], int]],
) -> int:
    if not placed_distance_maps:
        return MIN_PAIRWISE_SPREAD_BFS
    minimum = MIN_PAIRWISE_SPREAD_BFS
    for distances in placed_distance_maps:
        distance = distances.get(candidate)
        if distance is None:
            return 0
        minimum = min(minimum, distance)
    return minimum


def _distance_maps_for_placed(
    game_map: GameMap,
    placed: list[tuple[int, int]],
    *,
    tile_predicate,
) -> list[dict[tuple[int, int], int]]:
    return [
        bfs_path_distances(
            game_map,
            position,
            tile_predicate=tile_predicate,
            cardinal_only=True,
        )
        for position in placed
    ]


def _can_select_spread_positions(
    game_map: GameMap,
    candidates: list[tuple[int, int]],
    count: int,
    minimum: int,
    *,
    tile_predicate,
) -> bool:
    if len(candidates) < count:
        return False

    entrance = game_map.enter_xy
    ranked = sorted(
        candidates,
        key=lambda pos: _chebyshev_distance(pos, entrance),
        reverse=True,
    )
    quartile_start = max(0, (len(ranked) * 3) // 4 - 1)
    first_pool = ranked[quartile_start:] or ranked
    placed = [first_pool[0]]
    placed_distance_maps = _distance_maps_for_placed(
        game_map,
        placed,
        tile_predicate=tile_predicate,
    )

    while len(placed) < count:
        best_distance = -1
        best_candidates: list[tuple[int, int]] = []
        for candidate in candidates:
            if candidate in placed:
                continue
            separation = _min_distance_to_placed(candidate, placed_distance_maps)
            if separation < minimum:
                continue
            if separation > best_distance:
                best_distance = separation
                best_candidates = [candidate]
            elif separation == best_distance:
                best_candidates.append(candidate)
        if not best_candidates:
            return False
        choice = best_candidates[0]
        placed.append(choice)
        placed_distance_maps.append(
            bfs_path_distances(
                game_map,
                choice,
                tile_predicate=tile_predicate,
                cardinal_only=True,
            )
        )

    return min_pairwise_bfs_distance(
        game_map,
        placed,
        tile_predicate=tile_predicate,
    ) >= minimum


def _place_spread_features(
    game_map: GameMap,
    rng: random.Random,
    candidates: list[tuple[int, int]],
    count: int,
    minimum: int,
    *,
    tile_predicate,
    place_tile: Tile,
) -> list[tuple[int, int]] | None:
    if len(candidates) < count:
        return None

    entrance = game_map.enter_xy
    ranked = sorted(
        candidates,
        key=lambda pos: _chebyshev_distance(pos, entrance),
        reverse=True,
    )
    quartile_start = max(0, (len(ranked) * 3) // 4 - 1)
    first_pool = ranked[quartile_start:] or ranked
    placed: list[tuple[int, int]] = [rng.choice(first_pool)]
    game_map.tiles[placed[0][1], placed[0][0]] = place_tile
    placed_distance_maps = _distance_maps_for_placed(
        game_map,
        placed,
        tile_predicate=tile_predicate,
    )

    while len(placed) < count:
        best_distance = -1
        best_candidates: list[tuple[int, int]] = []
        for candidate in candidates:
            if candidate in placed:
                continue
            separation = _min_distance_to_placed(candidate, placed_distance_maps)
            if separation < minimum:
                continue
            if separation > best_distance:
                best_distance = separation
                best_candidates = [candidate]
            elif separation == best_distance:
                best_candidates.append(candidate)
        if not best_candidates:
            return None
        choice = rng.choice(best_candidates)
        placed.append(choice)
        game_map.tiles[choice[1], choice[0]] = place_tile
        placed_distance_maps.append(
            bfs_path_distances(
                game_map,
                choice,
                tile_predicate=tile_predicate,
                cardinal_only=True,
            )
        )

    if min_pairwise_bfs_distance(
        game_map,
        placed,
        tile_predicate=tile_predicate,
    ) < minimum:
        for x, y in placed:
            game_map.tiles[y, x] = Tile.FLOOR
        return None
    return placed


def _carve_disk(game_map: GameMap, x: int, y: int, half_width: int) -> None:
    for dy in range(-half_width, half_width + 1):
        for dx in range(-half_width, half_width + 1):
            nx, ny = x + dx, y + dy
            if game_map.in_bounds(nx, ny):
                game_map.tiles[ny, nx] = Tile.FLOOR


def _carve_tunnel(
    game_map: GameMap,
    start: tuple[int, int],
    end: tuple[int, int],
    rng: random.Random,
    *,
    half_width: int,
) -> None:
    for x, y in tunnel_between(start, end, rng):
        _carve_disk(game_map, x, y, half_width)


def _carve_rect_room(
    game_map: GameMap,
    rng: random.Random,
    *,
    room_min: int,
    room_max: int,
) -> _Region | None:
    room_w = rng.randint(room_min, room_max)
    room_h = rng.randint(room_min, room_max)
    if room_w + 2 >= game_map.width or room_h + 2 >= game_map.height:
        return None
    x = rng.randint(1, game_map.width - room_w - 2)
    y = rng.randint(1, game_map.height - room_h - 2)
    room = RectangularRoom(x, y, room_w, room_h)
    game_map.tiles[room.inner] = Tile.FLOOR
    return _Region(room.center, room.x1, room.y1, room.x2, room.y2)


def _carve_blob_room(game_map: GameMap, rng: random.Random) -> _Region | None:
    radius = rng.randint(4, 7)
    cx = rng.randint(radius + 1, game_map.width - radius - 2)
    cy = rng.randint(radius + 1, game_map.height - radius - 2)
    x1, y1 = cx - radius, cy - radius
    x2, y2 = cx + radius + 1, cy + radius + 1
    x, y = cx, cy
    game_map.tiles[y, x] = Tile.FLOOR
    steps = rng.randint(radius * radius * 3, radius * radius * 6)
    for _ in range(steps):
        dx, dy = rng.choice(_CARDINAL)
        x = max(x1, min(x2 - 1, x + dx))
        y = max(y1, min(y2 - 1, y + dy))
        game_map.tiles[y, x] = Tile.FLOOR
    return _Region((cx, cy), x1, y1, x2, y2)


def _count_wall_neighbors(game_map: GameMap, x: int, y: int) -> int:
    count = 0
    for dx, dy in _NEIGHBORS8:
        nx, ny = x + dx, y + dy
        if not game_map.in_bounds(nx, ny) or game_map.tiles[ny, nx] == Tile.WALL:
            count += 1
    return count


def _carve_cavern_room(game_map: GameMap, rng: random.Random) -> _Region | None:
    w = rng.randint(10, 16)
    h = rng.randint(8, 14)
    if w + 2 >= game_map.width or h + 2 >= game_map.height:
        return None
    x1 = rng.randint(1, game_map.width - w - 2)
    y1 = rng.randint(1, game_map.height - h - 2)
    x2, y2 = x1 + w, y1 + h
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

    for y in range(y1, y2):
        for x in range(x1, x2):
            game_map.tiles[y, x] = Tile.FLOOR if rng.random() < 0.42 else Tile.WALL

    for _ in range(rng.randint(3, 5)):
        snapshot = game_map.tiles.copy()
        for y in range(y1 + 1, y2 - 1):
            for x in range(x1 + 1, x2 - 1):
                walls = _count_wall_neighbors(game_map, x, y)
                snapshot[y, x] = Tile.WALL if walls >= 5 else Tile.FLOOR
        game_map.tiles[y1:y2, x1:x2] = snapshot[y1:y2, x1:x2]

    game_map.tiles[cy, cx] = Tile.FLOOR
    return _Region((cx, cy), x1, y1, x2, y2)


def _floor_positions(game_map: GameMap) -> list[tuple[int, int]]:
    return [
        (x, y)
        for y in range(game_map.height)
        for x in range(game_map.width)
        if game_map.tiles[y, x] == Tile.FLOOR
    ]


def _apply_water_cells(game_map: GameMap, cells: set[tuple[int, int]]) -> None:
    for x, y in cells:
        if game_map.tiles[y, x] == Tile.FLOOR:
            game_map.tiles[y, x] = Tile.DEEP_WATER


def _revert_water_cells(game_map: GameMap, cells: set[tuple[int, int]]) -> None:
    for x, y in cells:
        if game_map.tiles[y, x] == Tile.DEEP_WATER:
            game_map.tiles[y, x] = Tile.FLOOR


def _grow_lake(
    game_map: GameMap,
    seed: tuple[int, int],
    rng: random.Random,
    *,
    min_size: int,
    max_size: int,
) -> set[tuple[int, int]]:
    sx, sy = seed
    if game_map.tiles[sy, sx] != Tile.FLOOR:
        return set()

    target = rng.randint(min_size, max_size)
    lake: set[tuple[int, int]] = set()
    frontier: list[tuple[int, int]] = [seed]
    while frontier and len(lake) < target:
        index = rng.randrange(len(frontier))
        x, y = frontier.pop(index)
        if (x, y) in lake:
            continue
        if game_map.tiles[y, x] != Tile.FLOOR:
            continue
        lake.add((x, y))
        for dx, dy in _CARDINAL:
            frontier.append((x + dx, y + dy))
    return lake


def _grow_river(
    game_map: GameMap,
    start: tuple[int, int],
    end: tuple[int, int],
    rng: random.Random,
) -> set[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    for x, y in tunnel_between(start, end, rng):
        cells.add((x, y))
        if rng.random() < 0.35:
            for dx, dy in _CARDINAL:
                nx, ny = x + dx, y + dy
                if game_map.in_bounds(nx, ny) and game_map.tiles[ny, nx] == Tile.FLOOR:
                    cells.add((nx, ny))
    return cells


def _try_apply_water_feature(
    game_map: GameMap,
    cells: set[tuple[int, int]],
    *,
    min_size: int,
) -> bool:
    if len(cells) < min_size:
        return False
    _apply_water_cells(game_map, cells)
    if validate_land_connectivity(game_map):
        return True
    _revert_water_cells(game_map, cells)
    return False


def _try_place_lake(
    game_map: GameMap,
    rng: random.Random,
    floors: list[tuple[int, int]],
    *,
    min_size: int,
    placement_retries: int,
) -> bool:
    if len(floors) < min_size + 4:
        return False
    max_size = rng.randint(min_size, min_size * 3)
    for _ in range(placement_retries):
        seed = rng.choice(floors)
        lake = _grow_lake(
            game_map,
            seed,
            rng,
            min_size=min_size,
            max_size=max_size,
        )
        if _try_apply_water_feature(game_map, lake, min_size=min_size):
            return True
    return False


def _try_place_river(
    game_map: GameMap,
    rng: random.Random,
    floors: list[tuple[int, int]],
    *,
    min_size: int,
    placement_retries: int,
) -> bool:
    if len(floors) < min_size:
        return False
    for _ in range(placement_retries):
        start = rng.choice(floors)
        end = rng.choice(floors)
        if start == end:
            continue
        river = _grow_river(game_map, start, end, rng)
        if _try_apply_water_feature(game_map, river, min_size=min_size):
            return True
    return False


def _add_water_features(
    game_map: GameMap,
    rng: random.Random,
    *,
    water_testing: bool = False,
) -> None:
    if water_testing:
        feature_chance = WATER_TESTING_FEATURE_CHANCE
        min_size = WATER_TESTING_MIN_FEATURE_SIZE
        lake_attempts = rng.randint(*WATER_TESTING_LAKE_ATTEMPTS)
        river_chance = WATER_TESTING_RIVER_CHANCE
        placement_retries = WATER_TESTING_PLACEMENT_RETRIES
    else:
        feature_chance = WATER_FEATURE_CHANCE
        min_size = WATER_MIN_FEATURE_SIZE
        lake_attempts = rng.randint(*WATER_LAKE_ATTEMPTS)
        river_chance = WATER_RIVER_CHANCE
        placement_retries = WATER_PLACEMENT_RETRIES

    if rng.random() > feature_chance:
        return

    floors = _floor_positions(game_map)
    if len(floors) < min_size + 10:
        return

    placed_any = False
    for _ in range(lake_attempts):
        if _try_place_lake(
            game_map,
            rng,
            floors,
            min_size=min_size,
            placement_retries=placement_retries,
        ):
            placed_any = True
        floors = _floor_positions(game_map)

    if rng.random() < river_chance:
        if _try_place_river(
            game_map,
            rng,
            floors,
            min_size=min_size,
            placement_retries=placement_retries,
        ):
            placed_any = True

    if water_testing and not placed_any and not water_positions(game_map):
        floors = _floor_positions(game_map)
        _try_place_lake(
            game_map,
            rng,
            floors,
            min_size=min_size,
            placement_retries=placement_retries * 2,
        )


def _place_stairs(game_map: GameMap, rng: random.Random) -> bool:
    reachable = land_reachable_from(game_map, game_map.enter_xy)
    reachable.discard(game_map.enter_xy)
    candidates = [
        (x, y)
        for x, y in reachable
        if game_map.tiles[y, x] == Tile.FLOOR
    ]
    placed = _place_spread_features(
        game_map,
        rng,
        candidates,
        STAIRS_PER_FLOOR,
        MIN_PAIRWISE_SPREAD_BFS,
        tile_predicate=lambda x, y: _is_traversable_land_tile(game_map, x, y),
        place_tile=Tile.STAIRS_DOWN,
    )
    return placed is not None


def _floor_components(game_map: GameMap) -> list[set[tuple[int, int]]]:
    """Return connected floor components (4-directional)."""
    floors = set(_floor_positions(game_map))
    components: list[set[tuple[int, int]]] = []
    while floors:
        start = floors.pop()
        component: set[tuple[int, int]] = {start}
        queue: deque[tuple[int, int]] = deque([start])
        while queue:
            x, y = queue.popleft()
            for dx, dy in _CARDINAL:
                neighbor = (x + dx, y + dy)
                if neighbor in floors:
                    floors.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def _connect_orphan_land(game_map: GameMap, rng: random.Random) -> bool:
    """Tunnel orphan floor regions into the largest component; set entrance there."""
    components = _floor_components(game_map)
    if not components:
        return False

    main = max(components, key=len)
    game_map.enter_xy = rng.choice(sorted(main))

    for orphan in components:
        if orphan is main:
            continue
        start = rng.choice(sorted(main))
        end = rng.choice(sorted(orphan))
        for x, y in tunnel_between(start, end, rng):
            _carve_disk(game_map, x, y, 0)
        main |= orphan

    return True


def _spawn_candidate_count(game_map: GameMap, *, min_distance: int = 6) -> int:
    """Count land tiles at least `min_distance` from the entrance (Chebyshev)."""
    ex, ey = game_map.enter_xy
    min_dist_sq = min_distance * min_distance
    count = 0
    for x, y in land_positions(game_map):
        dx = x - ex
        dy = y - ey
        if dx * dx + dy * dy >= min_dist_sq:
            count += 1
    return count


def _carve_land_layout(
    game_map: GameMap,
    rng: random.Random,
    *,
    max_rooms: int,
    room_min_size: int,
    room_max_size: int,
    layout_archetype_force: str | None = None,
) -> bool:
    from src.constants import LAYOUT_ARCHETYPE_FORCE
    from src.map_gen_layouts import carve_layout, pick_layout_archetype

    archetype = pick_layout_archetype(
        rng,
        force=layout_archetype_force or LAYOUT_ARCHETYPE_FORCE,
    )
    return carve_layout(
        game_map,
        rng,
        archetype,
        max_rooms=max_rooms,
        room_min_size=room_min_size,
        room_max_size=room_max_size,
    )


def _attempt_generate_dungeon(
    map_width: int,
    map_height: int,
    rng: random.Random,
    *,
    max_rooms: int,
    room_min_size: int,
    room_max_size: int,
    water_testing: bool = False,
    layout_archetype_force: str | None = None,
    runes_per_floor: int = RUNES_PER_FLOOR,
) -> tuple[GameMap | None, str | None]:
    dungeon = GameMap(map_width, map_height)
    if not _carve_land_layout(
        dungeon,
        rng,
        max_rooms=max_rooms,
        room_min_size=room_min_size,
        room_max_size=room_max_size,
        layout_archetype_force=layout_archetype_force,
    ):
        return None, "layout_carve_failed"
    if not _connect_orphan_land(dungeon, rng):
        return None, "connect_orphan_failed"
    if not validate_land_connectivity(dungeon):
        return None, "disconnected_land"

    _add_water_features(dungeon, rng, water_testing=water_testing)
    if not validate_land_connectivity(dungeon):
        return None, "disconnected_land_after_water"
    if not validate_min_land_tiles(dungeon):
        return None, "too_few_land_tiles"
    if (
        _spawn_candidate_count(dungeon, min_distance=MONSTER_SPAWN_MIN_DISTANCE)
        < MIN_SPAWN_CANDIDATE_COUNT
    ):
        return None, "too_few_spawn_candidates"
    if not _place_stairs(dungeon, rng):
        return None, "stairs_placement_failed"
    if not validate_stairs_reachable(dungeon):
        return None, "stairs_unreachable"
    stair_coords = stairs_positions(dungeon)
    if len(stair_coords) != STAIRS_PER_FLOOR:
        return None, "stairs_placement_failed"
    if not validate_pairwise_spread(dungeon, stair_coords):
        return None, "stairs_too_clustered"
    from src.systems.macguffins import macguffins_per_floor_max

    spread_object_count = max(0, int(runes_per_floor)) + macguffins_per_floor_max()
    if spread_object_count > 0 and not validate_rune_sites_feasible(
        dungeon, count=spread_object_count
    ):
        return None, "rune_sites_infeasible"

    from src.map_gen_layouts.doors import place_doors

    place_doors(dungeon, rng)
    if not validate_land_connectivity(dungeon):
        return None, "disconnected_land_after_doors"
    if not validate_pairwise_spread(dungeon, stair_coords):
        return None, "stairs_too_clustered_after_doors"
    return dungeon, None


def _fallback_giant_room(map_width: int, map_height: int) -> GameMap:
    """Single large chamber used when sanity-checked generation exhausts retries."""
    margin = 4
    x1, y1 = margin, margin
    x2, y2 = map_width - margin - 1, map_height - margin - 1
    dungeon = GameMap(map_width, map_height)
    dungeon.tiles[y1 : y2 + 1, x1 : x2 + 1] = Tile.FLOOR
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    dungeon.enter_xy = (cx, cy)
    dungeon.layout_archetype = "fallback"
    stair_spots = [(x1 + 2, y1 + 2), (x2 - 2, y1 + 2), (x1 + 2, y2 - 2)]
    for x, y in stair_spots:
        dungeon.tiles[y, x] = Tile.STAIRS_DOWN
    return dungeon


def generate_dungeon(
    map_width: int,
    map_height: int,
    *,
    max_rooms: int = 30,
    room_min_size: int = 6,
    room_max_size: int = 10,
    seed: int | None = None,
    water_testing: bool = False,
    layout_archetype_force: str | None = None,
    runes_per_floor: int = RUNES_PER_FLOOR,
) -> GameMap:
    """Build a mixed dungeon with optional water, three downstairs, and validated land."""
    for attempt in range(1, MAX_GEN_ATTEMPTS + 1):
        attempt_seed: int | None
        if seed is None:
            attempt_seed = None
        else:
            attempt_seed = seed + attempt - 1
        rng = random.Random(attempt_seed)
        dungeon, reject_reason = _attempt_generate_dungeon(
            map_width,
            map_height,
            rng,
            max_rooms=max_rooms,
            room_min_size=room_min_size,
            room_max_size=room_max_size,
            water_testing=water_testing,
            layout_archetype_force=layout_archetype_force,
            runes_per_floor=runes_per_floor,
        )
        if dungeon is not None:
            return dungeon
        if reject_reason is not None:
            _debug_log_map_reject(attempt, reject_reason)

    debug_print(
        f"[map_gen] using fallback giant room after {MAX_GEN_ATTEMPTS} failed attempts",
        flush=True,
    )
    return _fallback_giant_room(map_width, map_height)