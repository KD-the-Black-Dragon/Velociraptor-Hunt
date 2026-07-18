from __future__ import annotations

import random

from tcod.ecs import Entity, Registry

from src.components import (
    AI,
    Alignment,
    Engulfed,
    NPCAlignment,
    Player,
    Position,
    ProperName,
    Stunned,
)
from src.data.entity_registry import EntityRegistry
from src.data.names_registry import NamesRegistry
from src.map_gen import GameMap
from src.log_categories import MessageCategory
from src.message_log import MessageLog
from src.systems.ai.targeting import _visible_good_evils
from src.systems.fov import entity_visible_to_player, player_has_visible_evil
from src.systems.naming import entity_type_id
from src.systems.vore import is_adjacent


def _sorted_good_allies(world: Registry, player: Entity) -> list[Entity]:
    allies: list[Entity] = []
    for entity in world.Q.all_of(components=[AI, Position, NPCAlignment]):
        if entity is player:
            continue
        if entity.components[NPCAlignment].alignment != Alignment.GOOD:
            continue
        allies.append(entity)
    return sorted(
        allies,
        key=lambda entity: (
            entity.components[Position].y,
            entity.components[Position].x,
            id(entity),
        ),
    )


def try_good_introductions(
    world: Registry,
    game_map: GameMap,
    player: Entity,
    message_log: MessageLog,
    *,
    rng: random.Random,
    entity_registry: EntityRegistry,
    names_registry: NamesRegistry,
) -> None:
    """Assign ProperName and log introduction for eligible adjacent good allies."""
    if Engulfed in player.tags:
        return

    player_pos = player.components[Position]
    if player_has_visible_evil(game_map, world):
        return

    definitions = entity_registry.by_id()
    for entity in _sorted_good_allies(world, player):
        if entity.components.get(ProperName) is not None:
            continue
        if Stunned in entity.tags:
            continue
        if not is_adjacent(player_pos, entity.components[Position]):
            continue
        if _visible_good_evils(entity, world, game_map):
            continue

        entity_id = entity_type_id(entity)
        definition = definitions.get(entity_id)
        if definition is None:
            continue

        pool = names_registry.pool_for(entity_id)
        introduction = definition.introduction
        if pool is None or introduction is None:
            continue

        name = rng.choice(pool)
        template = rng.choice(introduction)
        entity.components[ProperName] = ProperName(name=name)
        line = template.replace("{name}", name)
        if entity_visible_to_player(game_map, entity):
            category = (
                definition.introduction_log_category or MessageCategory.ROUTINE
            )
            message_log.add(line, category=category)