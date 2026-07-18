from __future__ import annotations

import random

from tcod.ecs import Entity, Registry

from typing import Final

from src.components import (
    Alignment,
    BlocksMovement,
    FloorRune,
    Macguffin,
    Mobility,
    MobilityType,
    NPCAlignment,
    Player,
    Position,
)
from src import messages
from src.map_gen import GameMap, Tile, can_enter_tile
from src.message_log import MessageCategory, MessageLog

from src.systems.fov import entity_visible_to_player
from src.systems.naming import entity_log_name

HANDS_DOOR_BREAK_CHANCE: Final[float] = 0.20

MOVEMENT_DIRECTIONS: Final[tuple[tuple[int, int], ...]] = (
    (-1, 0),
    (1, 0),
    (0, -1),
    (0, 1),
    (-1, -1),
    (-1, 1),
    (1, -1),
    (1, 1),
)


def entity_mobility(entity: Entity) -> MobilityType:
    """Return traversal class for an entity; missing component defaults to ground."""
    mobility = entity.components.get(Mobility)
    if mobility is None:
        return MobilityType.GROUND
    return mobility.kind


def is_stationary(entity: Entity) -> bool:
    """True when the entity does not take voluntary movement steps."""
    return entity_mobility(entity) == MobilityType.STATIONARY


def can_entity_enter_tile(game_map: GameMap, x: int, y: int, entity: Entity) -> bool:
    return can_enter_tile(game_map, x, y, entity_mobility(entity))


def _mover_has_hands(mover: Entity) -> bool:
    from src.systems.abilities import has_hands

    return has_hands(mover)


def terrain_passable_for_mover(
    game_map: GameMap,
    x: int,
    y: int,
    mover: Entity,
) -> bool:
    """Terrain legality for a move attempt (ignores blocking entities)."""
    if can_entity_enter_tile(game_map, x, y, mover):
        return True
    if (
        _mover_has_hands(mover)
        and game_map.in_bounds(x, y)
        and game_map.tiles[y, x] == Tile.DOOR_CLOSED
    ):
        return True
    return False


def _blocking_entity_at(
    world: Registry,
    x: int,
    y: int,
    mover: Entity,
) -> Entity | None:
    """Return the BlocksMovement entity on a tile, excluding the mover."""
    target = Position(x, y)
    for entity in world.Q.all_of(tags=[target, BlocksMovement]):
        if entity is mover:
            continue
        if Player in mover.tags and entity.components.get(FloorRune) is not None:
            continue
        if Player in mover.tags and entity.components.get(Macguffin) is not None:
            continue
        return entity
    return None


def _is_blocked_by_entity(world: Registry, x: int, y: int, mover: Entity) -> bool:
    """Return True if a BlocksMovement entity occupies the tile (excluding mover)."""
    return _blocking_entity_at(world, x, y, mover) is not None


def is_blocked_for_mover(world: Registry, x: int, y: int, mover: Entity) -> bool:
    """Public: True if a blocking entity occupies the tile (excluding mover)."""
    return _is_blocked_by_entity(world, x, y, mover)


def can_move_to(
    world: Registry,
    game_map: GameMap,
    mover: Entity,
    origin: Position,
    direction: tuple[int, int],
    *,
    blocked_tiles: frozenset[Position] = frozenset(),
) -> bool:
    """Check movement legality including terrain mobility and blocking entities."""
    dx, dy = direction
    dest_x = origin.x + dx
    dest_y = origin.y + dy

    if not terrain_passable_for_mover(game_map, dest_x, dest_y, mover):
        return False

    if Position(dest_x, dest_y) in blocked_tiles:
        return False

    if _is_blocked_by_entity(world, dest_x, dest_y, mover):
        return False

    return True


def can_step_for_chase(
    world: Registry,
    game_map: GameMap,
    mover: Entity,
    origin: Position,
    direction: tuple[int, int],
    *,
    blocked_tiles: frozenset[Position] = frozenset(),
    swappable_defender_alignments: frozenset[Alignment] | None = None,
) -> bool:
    """Like can_move_to, but treats swappable NPC bumps as legal chase steps."""
    if can_move_to(
        world,
        game_map,
        mover,
        origin,
        direction,
        blocked_tiles=blocked_tiles,
    ):
        return True

    dx, dy = direction
    dest_x = origin.x + dx
    dest_y = origin.y + dy
    if not terrain_passable_for_mover(game_map, dest_x, dest_y, mover):
        return False

    dest = Position(dest_x, dest_y)
    if dest in blocked_tiles:
        return False

    defender = _blocking_entity_at(world, dest_x, dest_y, mover)
    if defender is None:
        return False

    from src.systems.combat import can_npc_swap

    if not can_npc_swap(mover, defender):
        return False
    if swappable_defender_alignments is None:
        return True
    alignment = defender.components.get(NPCAlignment)
    if alignment is None:
        return False
    return alignment.alignment in swappable_defender_alignments


def log_hands_door_open(
    game_map: GameMap,
    opener: Entity,
    door_x: int,
    door_y: int,
    message_log: MessageLog,
) -> None:
    """FOV-gated routine log when a ``Hands`` NPC opens a closed door."""
    if not game_map.in_bounds(door_x, door_y):
        return
    door_visible = bool(game_map.visible[door_y, door_x])
    opener_visible = entity_visible_to_player(game_map, opener)
    if opener_visible:
        message_log.add(
            messages.npc_opens_door(entity_log_name(opener, sentence_start=True)),
            category=MessageCategory.ROUTINE,
        )
    elif door_visible:
        message_log.add(messages.something_opens_door(), category=MessageCategory.ROUTINE)


def log_hands_door_break(
    game_map: GameMap,
    opener: Entity,
    door_x: int,
    door_y: int,
    message_log: MessageLog,
) -> None:
    """FOV-gated caution log when a ``Hands`` NPC breaks a closed door."""
    if not game_map.in_bounds(door_x, door_y):
        return
    door_visible = bool(game_map.visible[door_y, door_x])
    opener_visible = entity_visible_to_player(game_map, opener)
    if opener_visible:
        message_log.add(
            messages.npc_breaks_down_door(entity_log_name(opener, sentence_start=True)),
            category=MessageCategory.CAUTION,
        )
    elif door_visible:
        message_log.add(
            messages.something_breaks_down_door(),
            category=MessageCategory.CAUTION,
        )


def try_hands_closed_door(
    world: Registry,
    game_map: GameMap,
    actor: Entity,
    direction: tuple[int, int],
    message_log: MessageLog,
    rng: random.Random,
) -> bool:
    """
    ``Hands`` bump on a closed door: open (80%) or break to floor (20%).
    Consumes the turn without moving the actor (matches player door-open).
    """
    if not _mover_has_hands(actor):
        return False
    origin = actor.components[Position]
    if not can_move_to(world, game_map, actor, origin, direction):
        return False
    dest = origin + direction
    if (
        not game_map.in_bounds(dest.x, dest.y)
        or game_map.tiles[dest.y, dest.x] != Tile.DOOR_CLOSED
    ):
        return False
    if rng.random() < HANDS_DOOR_BREAK_CHANCE:
        game_map.tiles[dest.y, dest.x] = Tile.FLOOR
        log_hands_door_break(game_map, actor, dest.x, dest.y, message_log)
    else:
        game_map.tiles[dest.y, dest.x] = Tile.DOOR_OPEN
        log_hands_door_open(game_map, actor, dest.x, dest.y, message_log)
    return True


def try_move(
    world: Registry,
    game_map: GameMap,
    entity: Entity,
    direction: tuple[int, int],
    *,
    message_log: MessageLog | None = None,
) -> bool:
    """Move entity if legal. Return True when position changed (turn consumed)."""
    origin = entity.components[Position]
    if is_stationary(entity):
        return False
    if not can_move_to(world, game_map, entity, origin, direction):
        return False

    dest = origin + direction
    if (
        _mover_has_hands(entity)
        and game_map.in_bounds(dest.x, dest.y)
        and game_map.tiles[dest.y, dest.x] == Tile.DOOR_CLOSED
    ):
        return False
    entity.components[Position] = dest
    return True