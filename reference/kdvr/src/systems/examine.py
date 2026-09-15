from __future__ import annotations

import attrs
from tcod.ecs import Entity, Registry

from src import messages
from src.components import ExamineDescription, Fighter, Item, Player, Position
from src.map_gen import GameMap
from src.systems.item_modals import (
    format_floor_item_detail_text,
    format_floor_items_list_text,
)


@attrs.define
class ExamineState:
    active: bool = False
    cursor: Position = attrs.field(factory=lambda: Position(0, 0))
    showing_description: bool = False
    description_text: str = ""

    def enter(self, start: Position) -> None:
        self.active = True
        self.cursor = Position(start.x, start.y)
        self.showing_description = False
        self.description_text = ""

    def reset(self) -> None:
        self.active = False
        self.showing_description = False
        self.description_text = ""


def move_examine_cursor(
    cursor: Position,
    direction: tuple[int, int],
    game_map: GameMap,
) -> Position:
    """Move the examine cursor one step, clamped to map bounds."""
    dest = cursor + direction
    if not game_map.in_bounds(dest.x, dest.y):
        return cursor
    return dest


def inspectable_at(world: Registry, x: int, y: int) -> Entity | None:
    """Return the top inspectable entity on a tile (fighters before items)."""
    target = Position(x, y)
    for entity in world.Q.all_of(tags=[target], components=[ExamineDescription, Fighter]):
        if Player in entity.tags:
            continue
        return entity
    for entity in world.Q.all_of(tags=[target], components=[ExamineDescription, Item]):
        return entity
    for entity in world.Q.all_of(tags=[target], components=[ExamineDescription]):
        if Player in entity.tags:
            continue
        return entity
    return None


def floor_item_entities_at(world: Registry, x: int, y: int) -> list[Entity]:
    """All floor item entities on a tile (stable query order)."""
    target = Position(x, y)
    return list(world.Q.all_of(tags=[target], components=[Item]))


def description_for_tile(world: Registry, x: int, y: int) -> str:
    """Description text for examine Enter on a tile."""
    target = Position(x, y)
    for entity in world.Q.all_of(tags=[target], components=[ExamineDescription, Fighter]):
        if Player in entity.tags:
            continue
        desc = entity.components.get(ExamineDescription)
        if desc is None:
            return messages.examine_nothing_here()
        return desc.text

    items = floor_item_entities_at(world, x, y)
    if items:
        if len(items) == 1:
            return format_floor_item_detail_text(items[0].components[Item])
        return format_floor_items_list_text([e.components[Item] for e in items])

    for entity in world.Q.all_of(tags=[target], components=[ExamineDescription]):
        if Player in entity.tags:
            continue
        desc = entity.components.get(ExamineDescription)
        if desc is None:
            continue
        return desc.text
    return messages.examine_nothing_here()