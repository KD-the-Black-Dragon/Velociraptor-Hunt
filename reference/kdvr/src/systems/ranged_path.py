"""Path-targeted ranged attacks — Bresenham beam with alignment blocks."""

from __future__ import annotations

from enum import Enum, auto
import attrs
import tcod.los
from tcod.ecs import Entity, Registry

from src.components import (
    Alignment,
    Engulfed,
    Fighter,
    NPCAlignment,
    Player,
    Position,
    Predator,
    VoreMercy,
)
from src.map_gen import GameMap, Tile


class PathShotStatus(Enum):
    HIT = auto()
    BLOCKED = auto()
    NO_LINE = auto()
    NO_TARGET = auto()


@attrs.define(frozen=True)
class PathShotResult:
    status: PathShotStatus
    defender: Entity | None = None


def path_tiles(
    origin_x: int,
    origin_y: int,
    target_x: int,
    target_y: int,
) -> list[tuple[int, int]]:
    """Bresenham tiles from origin to target, inclusive."""
    return tcod.los.bresenham((origin_x, origin_y), (target_x, target_y)).tolist()


def tile_blocks_projectile(game_map: GameMap, x: int, y: int) -> bool:
    if not game_map.in_bounds(x, y):
        return True
    tile = Tile(game_map.tiles[y, x])
    return tile in (Tile.WALL, Tile.DOOR_CLOSED)


def _npc_alignment(entity: Entity) -> Alignment | None:
    alignment = entity.components.get(NPCAlignment)
    if alignment is None:
        return None
    return alignment.alignment


def _path_entity_active(entity: Entity) -> bool:
    from src.systems.abilities import is_stunned_prey

    if Engulfed in entity.tags or VoreMercy in entity.tags:
        return False
    if entity.components.get(Fighter) is None:
        return False
    return not is_stunned_prey(entity)


def shooter_can_damage(shooter: Entity, defender: Entity) -> bool:
    """True when `defender` may be struck by a Path shot from `shooter`."""
    if not _path_entity_active(defender):
        return False
    if Player in shooter.tags:
        return _npc_alignment(defender) == Alignment.EVIL
    shooter_alignment = _npc_alignment(shooter)
    if shooter_alignment == Alignment.EVIL:
        if Player in defender.tags:
            return True
        defender_alignment = _npc_alignment(defender)
        return defender_alignment in (Alignment.GOOD, Alignment.NEUTRAL)
    if shooter_alignment == Alignment.GOOD:
        return _npc_alignment(defender) == Alignment.EVIL
    if shooter_alignment == Alignment.NEUTRAL:
        return _npc_alignment(defender) == Alignment.EVIL
    return False


def shooter_blocks_entity(shooter: Entity, entity: Entity) -> bool:
    """True when `entity` on the beam cancels the shot before firing."""
    if not _path_entity_active(entity):
        return False
    return not shooter_can_damage(shooter, entity)


def fighters_on_tile(world: Registry, x: int, y: int) -> list[Entity]:
    found: list[Entity] = []
    for entity in world.Q.all_of(components=[Position, Fighter]):
        pos = entity.components[Position]
        if pos.x != x or pos.y != y:
            continue
        if not _path_entity_active(entity):
            continue
        found.append(entity)
    if not found:
        return []
    for entity in found:
        if entity.components.get(Predator) is not None:
            return [entity]
    return [found[0]]


def resolve_path_shot(
    world: Registry,
    game_map: GameMap,
    shooter: Entity,
    intended: Entity,
) -> PathShotResult:
    """
    Simulate a Path-targeted shot toward `intended`.

    Returns BLOCKED when a same-alignment entity sits on the line before the
    target cell; NO_LINE when terrain blocks; HIT with the first damageable
    Fighter along the beam (may differ from `intended`).
    """
    origin = shooter.components[Position]
    target_pos = intended.components[Position]
    tiles = path_tiles(origin.x, origin.y, target_pos.x, target_pos.y)
    if len(tiles) < 2:
        return PathShotResult(status=PathShotStatus.NO_LINE)

    intended_xy = (target_pos.x, target_pos.y)
    for x, y in tiles[1:]:
        if tile_blocks_projectile(game_map, x, y):
            return PathShotResult(status=PathShotStatus.NO_LINE)
        if (x, y) == intended_xy:
            break
        for entity in fighters_on_tile(world, x, y):
            if shooter_blocks_entity(shooter, entity):
                return PathShotResult(status=PathShotStatus.BLOCKED)

    for x, y in tiles[1:]:
        if tile_blocks_projectile(game_map, x, y):
            return PathShotResult(status=PathShotStatus.NO_LINE)
        for entity in fighters_on_tile(world, x, y):
            if shooter_can_damage(shooter, entity):
                return PathShotResult(status=PathShotStatus.HIT, defender=entity)

    return PathShotResult(status=PathShotStatus.NO_TARGET)