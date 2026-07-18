"""Floor descent: follower selection and placement on a new dungeon level."""

from __future__ import annotations

from collections import deque

from tcod.ecs import Entity, Registry

from src.components import (
    AI,
    Alignment,
    Engulfed,
    MobilityType,
    NPCAlignment,
    Player,
    Position,
    Predator,
)
from src.map_gen import GameMap, can_enter_tile
from src.systems.fov import can_see
from src.systems.movement import MOVEMENT_DIRECTIONS


def collect_descent_followers(
    world: Registry,
    game_map: GameMap,
    player: Entity,
) -> list[Entity]:
    """Good allies with LOS to the player that may follow downstairs."""
    player_pos = player.components[Position]
    followers: list[Entity] = []
    for entity in world.Q.all_of(components=[AI, NPCAlignment, Position]):
        if entity is player:
            continue
        if Engulfed in entity.tags:
            continue
        if entity.components.get(Predator) is not None:
            continue
        if entity.components[NPCAlignment].alignment != Alignment.GOOD:
            continue
        pos = entity.components[Position]
        if not can_see(game_map, player_pos.x, player_pos.y, pos.x, pos.y):
            continue
        followers.append(entity)
    return followers


def nearest_land_tiles(
    game_map: GameMap,
    origin: tuple[int, int],
    count: int,
    *,
    blocked: set[tuple[int, int]],
) -> list[tuple[int, int]]:
    """BFS land tiles nearest to `origin`, excluding `blocked` and `origin`."""
    if count <= 0:
        return []

    ox, oy = origin
    result: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = {origin}
    queue: deque[tuple[int, int]] = deque([origin])

    while queue and len(result) < count:
        x, y = queue.popleft()
        if (x, y) != origin and (x, y) not in blocked:
            if can_enter_tile(game_map, x, y, MobilityType.GROUND):
                result.append((x, y))

        for dx, dy in MOVEMENT_DIRECTIONS:
            nx, ny = x + dx, y + dy
            if not game_map.in_bounds(nx, ny):
                continue
            if (nx, ny) in seen:
                continue
            if not can_enter_tile(game_map, nx, ny, MobilityType.GROUND):
                continue
            seen.add((nx, ny))
            queue.append((nx, ny))

    return result


def place_descent_followers(
    game_map: GameMap,
    followers: list[Entity],
    *,
    entrance_xy: tuple[int, int],
    player: Entity,
) -> None:
    """Place followers on the nearest open land tiles to the new entrance."""
    player_pos = player.components[Position]
    blocked = {(player_pos.x, player_pos.y)}
    tiles = nearest_land_tiles(
        game_map,
        entrance_xy,
        len(followers),
        blocked=blocked,
    )
    for follower, (x, y) in zip(followers, tiles, strict=False):
        follower.components[Position] = Position(x, y)
        blocked.add((x, y))


def clear_floor_entities(world: Registry, *, keep: set[Entity]) -> None:
    """Remove every entity except those in `keep` (typically player + followers)."""
    for entity in list(world.Q.all_of(components=[Position])):
        if entity in keep:
            continue
        entity.clear()