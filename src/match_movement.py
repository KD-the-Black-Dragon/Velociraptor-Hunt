"""Arena movement legality for Gladiavore matches."""

from __future__ import annotations

from tcod.ecs import Entity

from src.components import Mobility, MobilityType
from src.game_map import GameMap, can_enter_tile


def entity_mobility(entity: Entity) -> MobilityType:
    mob = entity.components.get(Mobility)
    if mob is None:
        return MobilityType.GROUND
    return mob.kind


def can_entity_enter_tile(game_map: GameMap, x: int, y: int, entity: Entity) -> bool:
    return can_enter_tile(game_map, x, y, entity_mobility(entity))
