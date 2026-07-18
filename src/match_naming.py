"""Log names for match entities."""

from __future__ import annotations

from tcod.ecs import Entity

from src.components import DisplayName, Player, SpeciesId


def entity_log_name(entity: Entity, *, sentence_start: bool = False) -> str:
    if Player in entity.tags:
        return "You" if sentence_start else "you"
    if DisplayName in entity.components:
        name = entity.components[DisplayName].name
    elif SpeciesId in entity.components:
        name = entity.components[SpeciesId].id.replace("_", " ")
    else:
        name = "foe"
    if sentence_start and name:
        return name[0].upper() + name[1:]
    return name
