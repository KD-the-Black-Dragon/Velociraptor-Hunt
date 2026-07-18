from __future__ import annotations

import tcod.map
from numpy.typing import NDArray
import numpy as np
from tcod.ecs import Entity, Registry

from src.components import AI, Alignment, NPCAlignment, Position
from src.constants import FOV_RADIUS
from src.map_gen import GameMap, Tile


def _compute_visibility(
    game_map: GameMap,
    viewer_x: int,
    viewer_y: int,
    radius: int = FOV_RADIUS,
) -> NDArray[np.bool_]:
    transparency = np.isin(
        game_map.tiles,
        [Tile.FLOOR, Tile.DEEP_WATER, Tile.STAIRS_DOWN, Tile.DOOR_OPEN],
    )
    return tcod.map.compute_fov(
        transparency=transparency,
        pov=(viewer_y, viewer_x),
        radius=radius,
        light_walls=True,
    )


def update_fov(game_map: GameMap, player_x: int, player_y: int, radius: int = FOV_RADIUS) -> None:
    """Recompute visible tiles from the player position and merge into explored memory."""
    game_map.visible[:] = _compute_visibility(game_map, player_x, player_y, radius)
    game_map.explored |= game_map.visible


def can_see(
    game_map: GameMap,
    viewer_x: int,
    viewer_y: int,
    target_x: int,
    target_y: int,
    radius: int = FOV_RADIUS,
) -> bool:
    """Return True when target tile is inside viewer FOV."""
    if not game_map.in_bounds(target_x, target_y):
        return False
    visible = _compute_visibility(game_map, viewer_x, viewer_y, radius)
    return bool(visible[target_y, target_x])


def entity_visible_to_player(game_map: GameMap, entity: Entity) -> bool:
    """Return True when entity's tile is in the player's current FOV."""
    pos = entity.components[Position]
    if not game_map.in_bounds(pos.x, pos.y):
        return False
    return bool(game_map.visible[pos.y, pos.x])


def player_has_visible_evil(game_map: GameMap, world: Registry) -> bool:
    """True when any evil NPC occupies a tile in the player's current FOV."""
    for entity in world.Q.all_of(components=[AI, Position, NPCAlignment]):
        if entity.components[NPCAlignment].alignment != Alignment.EVIL:
            continue
        pos = entity.components[Position]
        if not game_map.in_bounds(pos.x, pos.y):
            continue
        if game_map.visible[pos.y, pos.x]:
            return True
    return False