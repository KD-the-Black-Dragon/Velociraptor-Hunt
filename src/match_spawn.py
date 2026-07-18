"""Spawn match NPCs from entity definitions without dungeon depth scaling."""

from __future__ import annotations

import random

from tcod.ecs import Entity, Registry

from src.components import (
    AI,
    AIState,
    Alignment,
    BlocksMovement,
    DisplayName,
    Fighter,
    Mobility,
    MobilityType,
    NPCAlignment,
    Position,
    Renderable,
    SpeciesId,
    VoreCapable,
)
from src.data.entity_loader import EntityDefinition


def spawn_match_entity(
    world: Registry,
    definition: EntityDefinition,
    x: int,
    y: int,
    *,
    rng: random.Random | None = None,
) -> Entity:
    """Materialize one opponent for an arena match (base stats from definition)."""
    _ = rng  # reserved for future prefix rolls
    entity = world[object()]
    entity.components[Position] = Position(x, y)
    glyph = definition.glyph if definition.glyph else "?"
    entity.components[Renderable] = Renderable(
        ch=ord(glyph[0]),
        fg=tuple(definition.fg) if definition.fg else (200, 200, 200),
    )
    entity.components[Fighter] = Fighter(
        hp=int(definition.max_hp),
        max_hp=int(definition.max_hp),
        accuracy=float(definition.accuracy),
        evade=float(definition.evade),
        ac=int(definition.ac),
        min_damage=int(definition.min_damage),
        max_damage=int(definition.max_damage),
        ranged_accuracy=float(definition.ranged_accuracy),
        ranged_min_damage=int(definition.ranged_min_damage),
        ranged_max_damage=int(definition.ranged_max_damage),
    )
    entity.components[DisplayName] = DisplayName(name=str(definition.display_name))
    entity.components[SpeciesId] = SpeciesId(id=definition.id)
    entity.components[NPCAlignment] = NPCAlignment(alignment=definition.alignment)
    entity.components[Mobility] = Mobility(kind=definition.mobility)
    entity.components[AI] = AI()
    entity.components[AIState] = AIState()
    entity.tags.add(BlocksMovement)
    # All match enemies are vore-capable per design
    entity.tags.add(VoreCapable)
    return entity
