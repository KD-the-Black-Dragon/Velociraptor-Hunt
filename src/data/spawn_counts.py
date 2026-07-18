from __future__ import annotations

from functools import lru_cache

from src.data.entity_loader import load_entity_registry
from src.data.entity_registry import EntityRegistry


@lru_cache(maxsize=1)
def default_entity_registry() -> EntityRegistry:
    return load_entity_registry()


def spawn_weight(entity_id: str, *, registry: EntityRegistry | None = None) -> int:
    reg = registry or default_entity_registry()
    return int(reg.get(entity_id).spawn.weight)


def land_spawn_weight_total(*, registry: EntityRegistry | None = None) -> int:
    reg = registry or default_entity_registry()
    return sum(
        int(entity.spawn.weight)
        for entity in reg.entities
        if entity.spawn.terrain == "land"
    )


def aquatic_spawn_weight_total(*, registry: EntityRegistry | None = None) -> int:
    reg = registry or default_entity_registry()
    return sum(
        int(entity.spawn.weight)
        for entity in reg.entities
        if entity.spawn.terrain == "water"
    )