"""Player BFS navigation shared by autoexplore and balance sim."""

from __future__ import annotations

import random

from tcod.ecs import Entity, Registry

from src.map_gen import GameMap, Tile, bfs_path_distances, stairs_positions
from src.systems.movement import MOVEMENT_DIRECTIONS, is_blocked_for_mover

_CARDINAL: tuple[tuple[int, int], ...] = ((0, -1), (0, 1), (-1, 0), (1, 0))


def player_walk_predicate(game_map: GameMap, x: int, y: int) -> bool:
    """Tiles walkable for pathfinding (doors may open on step)."""
    if not game_map.in_bounds(x, y):
        return False
    tile = Tile(game_map.tiles[y, x])
    return tile in (
        Tile.FLOOR,
        Tile.STAIRS_DOWN,
        Tile.DOOR_OPEN,
        Tile.DOOR_CLOSED,
    )


def _step_directions(*, cardinal_only: bool) -> tuple[tuple[int, int], ...]:
    return _CARDINAL if cardinal_only else MOVEMENT_DIRECTIONS


def player_walk_distances(
    game_map: GameMap,
    origin: tuple[int, int],
    *,
    cardinal_only: bool = True,
) -> dict[tuple[int, int], int]:
    return bfs_path_distances(
        game_map,
        origin,
        tile_predicate=lambda x, y: player_walk_predicate(game_map, x, y),
        cardinal_only=cardinal_only,
    )


def player_walk_distances_with_blockers(
    world: Registry,
    game_map: GameMap,
    origin: tuple[int, int],
    player: Entity,
    *,
    cardinal_only: bool = True,
) -> dict[tuple[int, int], int]:
    """BFS distances treating NPC-blocked tiles as unwalkable (except origin)."""
    ox, oy = origin

    def predicate(x: int, y: int) -> bool:
        if not player_walk_predicate(game_map, x, y):
            return False
        if (x, y) != (ox, oy) and is_blocked_for_mover(world, x, y, player):
            return False
        return True

    return bfs_path_distances(
        game_map,
        origin,
        tile_predicate=predicate,
        cardinal_only=cardinal_only,
    )


def manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def nearest_goal(
    origin: tuple[int, int],
    goals: list[tuple[int, int]],
    distances: dict[tuple[int, int], int],
    rng: random.Random,
) -> tuple[int, int] | None:
    """Pick a reachable goal with minimum BFS distance; random tie-break."""
    best_distance: int | None = None
    candidates: list[tuple[int, int]] = []
    for goal in goals:
        dist = distances.get(goal)
        if dist is None:
            continue
        if best_distance is None or dist < best_distance:
            best_distance = dist
            candidates = [goal]
        elif dist == best_distance:
            candidates.append(goal)
    if not candidates:
        return None
    return rng.choice(candidates)


def nearest_goal_deterministic(
    goals: list[tuple[int, int]],
    distances: dict[tuple[int, int], int],
) -> tuple[int, int] | None:
    """Nearest reachable goal; ties broken by (y, x) ascending."""
    reachable = [(goal, distances[goal]) for goal in goals if goal in distances]
    if not reachable:
        return None
    min_dist = min(dist for _, dist in reachable)
    candidates = [goal for goal, dist in reachable if dist == min_dist]
    return min(candidates, key=lambda coord: (coord[1], coord[0]))


def first_step_toward(
    origin: tuple[int, int],
    goal: tuple[int, int],
    distances_to_goal: dict[tuple[int, int], int],
    *,
    cardinal_only: bool = True,
) -> tuple[int, int] | None:
    """Return a movement direction (dx, dy) for one step closer to goal."""
    origin_dist = distances_to_goal.get(origin)
    if origin_dist is None or origin_dist == 0:
        return None
    ox, oy = origin
    best_direction: tuple[int, int] | None = None
    best_neighbor_dist = origin_dist
    for dx, dy in _step_directions(cardinal_only=cardinal_only):
        nx, ny = ox + dx, oy + dy
        neighbor_dist = distances_to_goal.get((nx, ny))
        if neighbor_dist is None or neighbor_dist >= origin_dist:
            continue
        if neighbor_dist < best_neighbor_dist:
            best_neighbor_dist = neighbor_dist
            best_direction = (dx, dy)
    return best_direction


def explore_frontier_tiles(
    game_map: GameMap,
    *,
    cardinal_only: bool = True,
) -> list[tuple[int, int]]:
    """Explored walkable tiles adjacent to an unexplored walkable neighbor."""
    frontier: list[tuple[int, int]] = []
    for y in range(game_map.height):
        for x in range(game_map.width):
            if not game_map.explored[y, x]:
                continue
            if not player_walk_predicate(game_map, x, y):
                continue
            for dx, dy in _step_directions(cardinal_only=cardinal_only):
                nx, ny = x + dx, y + dy
                if not game_map.in_bounds(nx, ny):
                    continue
                if game_map.explored[ny, nx]:
                    continue
                if not player_walk_predicate(game_map, nx, ny):
                    continue
                frontier.append((x, y))
                break
    return frontier


def flee_goal_maximizing_distance(
    origin: tuple[int, int],
    threats: list[tuple[int, int]],
    distances: dict[tuple[int, int], int],
    rng: random.Random,
) -> tuple[int, int] | None:
    """Among reachable tiles at max min-distance from threats, pick one."""
    if not threats:
        return None
    best_score = -1
    candidates: list[tuple[int, int]] = []
    for tile, _dist in distances.items():
        if tile == origin:
            continue
        score = min(manhattan(tile, threat) for threat in threats)
        if score > best_score:
            best_score = score
            candidates = [tile]
        elif score == best_score:
            candidates.append(tile)
    if not candidates:
        return None
    return rng.choice(candidates)


def direction_toward_position(
    origin: tuple[int, int],
    target: tuple[int, int],
    rng: random.Random,
) -> tuple[int, int] | None:
    """Pick a legal movement direction that reduces Manhattan distance."""
    ox, oy = origin
    tx, ty = target
    options: list[tuple[int, int]] = []
    for dx, dy in MOVEMENT_DIRECTIONS:
        nx, ny = ox + dx, oy + dy
        new_dist = abs(tx - nx) + abs(ty - ny)
        old_dist = abs(tx - ox) + abs(ty - oy)
        if new_dist < old_dist:
            options.append((dx, dy))
    if not options:
        return None
    return rng.choice(options)


def stair_positions_reachable(
    game_map: GameMap,
    distances: dict[tuple[int, int], int],
) -> list[tuple[int, int]]:
    return [pos for pos in stairs_positions(game_map) if pos in distances]