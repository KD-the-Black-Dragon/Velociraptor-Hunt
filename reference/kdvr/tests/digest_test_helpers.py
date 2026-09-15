"""Isolated digestion fixtures for mechanics tests — not live data/ balance."""

from __future__ import annotations

from typing import Any

import tcod.ecs

from src.components import DigestionStats
from src.data.alignment_profiles import DEFAULT_DIGEST_TIME, digest_time_for
from src.data.entity_loader import parse_entity_registry
from src.spawn import spawn_from_definition


def minimal_evil_entity_payload(
    entity_id: str = "test_predator",
    *,
    digest_time: int | None = None,
    digestion_damage_per_tick: int | None = 3,
    **overrides: object,
) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": entity_id,
        "display_name": entity_id.replace("_", " "),
        "glyph": "x",
        "fg": [100, 100, 100],
        "alignment": "evil",
        "mobility": "ground",
        "max_hp": 10,
        "evade": 1,
        "ac": 1,
        "accuracy": 1.0,
        "min_damage": 1,
        "max_damage": 2,
        "abilities": [],
        "spawn": {"weight": 1, "min_depth": 1, "max_depth": 10, "terrain": "land"},
    }
    if digestion_damage_per_tick is not None:
        base["digestion_damage_per_tick"] = digestion_damage_per_tick
    if digest_time is not None:
        base["digest_time"] = digest_time
    base.update(overrides)
    return base


def pin_predator_digest_stats(
    predator: tcod.ecs.Entity,
    *,
    digest_time: int,
    damage_per_tick: int | None = None,
) -> None:
    """Set or replace predator DigestionStats for strike-threshold tests."""
    stats = predator.components.get(DigestionStats)
    tick = damage_per_tick if damage_per_tick is not None else (
        stats.damage_per_tick if stats is not None else 3
    )
    predator.components[DigestionStats] = DigestionStats(
        damage_per_tick=tick,
        digest_time=digest_time,
    )


def spawn_evil_from_fixture(
    world: tcod.ecs.Registry,
    *,
    digest_time: int | None = None,
    entity_id: str = "test_predator",
    x: int = 0,
    y: int = 0,
) -> tcod.ecs.Entity:
    payload = {
        "schema_version": 1,
        "entities": [minimal_evil_entity_payload(entity_id, digest_time=digest_time)],
    }
    definition = parse_entity_registry(payload).get(entity_id)
    entity = spawn_from_definition(world, definition, x, y)
    assert entity is not None
    return entity


def expected_default_digest_time() -> int:
    return DEFAULT_DIGEST_TIME


def resolve_digest_time_from_definition(digest_time: int | None) -> int:
    from src.components import Alignment

    resolved = digest_time_for(Alignment.EVIL, digest_time)
    assert resolved is not None
    return resolved