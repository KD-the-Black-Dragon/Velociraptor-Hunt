"""Dismiss ally: Shift+D targeting to remove a good NPC from the dungeon."""

from __future__ import annotations

import attrs
from tcod.ecs import Entity, Registry

from src import messages
from src.components import (
    Alignment,
    Engulfed,
    Fighter,
    NPCAlignment,
    Player,
    Position,
)
from src.message_log import MessageLog
from src.systems.naming import entity_log_name


@attrs.define
class DismissState:
    active: bool = False
    cursor: Position = attrs.field(factory=lambda: Position(0, 0))

    def enter(self, start: Position) -> None:
        self.active = True
        self.cursor = Position(start.x, start.y)

    def reset(self) -> None:
        self.active = False


def fighter_on_tile(world: Registry, x: int, y: int) -> Entity | None:
    """Top fighter on a tile, excluding the player (Examine-style pick)."""
    target = Position(x, y)
    for entity in world.Q.all_of(tags=[target], components=[Fighter]):
        if Player in entity.tags:
            continue
        return entity
    return None


def is_dismissible_ally(entity: Entity) -> bool:
    """True for a free good NPC (not engulfed)."""
    if Engulfed in entity.tags:
        return False
    align = entity.components.get(NPCAlignment)
    if align is None:
        return False
    return align.alignment is Alignment.GOOD


def try_confirm_dismiss(
    world: Registry,
    message_log: MessageLog,
    *,
    x: int,
    y: int,
) -> bool:
    """Confirm dismiss at tile. Return True if an ally was removed."""
    entity = fighter_on_tile(world, x, y)
    if entity is None or not is_dismissible_ally(entity):
        message_log.add(messages.dismiss_invalid_target())
        return False

    name = entity_log_name(entity, sentence_start=True)
    message_log.add(messages.dismiss_exits_dungeon(name))
    entity.clear()
    return True
