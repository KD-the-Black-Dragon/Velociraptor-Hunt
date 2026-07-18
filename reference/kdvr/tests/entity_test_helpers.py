"""Pinned entity JSON for mechanics tests — not live data/entities.json."""

from __future__ import annotations

from typing import Any

import tcod.ecs

from src.components import Abilities, AbilityState
from src.data.ability_parser import parse_abilities
from src.data.entity_loader import parse_entity_registry
from src.spawn import spawn_from_definition


def minimal_entity_payload(entity_id: str, **overrides: object) -> dict[str, Any]:
    """Minimal evil entity dict suitable for ``parse_entity_registry``."""
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
        "accuracy": 0.5,
        "min_damage": 2,
        "max_damage": 3,
        "ranged_accuracy": 0.0,
        "ranged_min_damage": 0,
        "ranged_max_damage": 0,
        "abilities": [],
        "spawn": {"weight": 1, "min_depth": 1, "max_depth": 10, "terrain": "land"},
        "digestion_damage_per_tick": 3,
        "digest_time": 5,
        "vore_narratives": {
            "OV": [
                {
                    "attempt": ["[fixture] attempt"],
                    "success": ["[fixture] success"],
                }
            ]
        },
        "digestion_complete": {"OV": ["[fixture] done"]},
        "npc_vore_hit": {"OV": ["[fixture] hit"]},
        "npc_vore_miss": {"OV": ["[fixture] miss"]},
        "offscreen_vore": {"OV": ["[fixture] off vore"]},
        "offscreen_digest": {"OV": ["[fixture] off dig"]},
    }
    base.update(overrides)
    return base


def fixture_wolf_payload(**overrides: object) -> dict[str, Any]:
    """Pinned wolf-shaped payload — abilities/stats independent of data/entities.json."""
    defaults: dict[str, object] = {
        "display_name": "wolf",
        "glyph": "w",
        "fg": [80, 80, 80],
        "max_hp": 10,
        "evade": 2,
        "ac": 2,
        "accuracy": 0.5,
        "min_damage": 4,
        "max_damage": 6,
        "abilities": [],
    }
    defaults.update(overrides)
    return minimal_entity_payload("wolf", **defaults)


def spawn_fixture_wolf(
    world: tcod.ecs.Registry,
    x: int,
    y: int,
    *,
    payload_overrides: dict[str, object] | None = None,
) -> tcod.ecs.Entity:
    payload = fixture_wolf_payload(**(payload_overrides or {}))
    registry = parse_entity_registry({"schema_version": 1, "entities": [payload]})
    definition = registry.get("wolf")
    assert definition is not None
    return spawn_from_definition(world, definition, x, y)


def spawn_fixture_wolf_with_abilities(
    world: tcod.ecs.Registry,
    x: int,
    y: int,
    abilities: list[str],
) -> tcod.ecs.Entity:
    """Spawn a fixture wolf and assign explicit ability tokens (ignores live data/)."""
    wolf = spawn_fixture_wolf(world, x, y)
    wolf.components[AbilityState] = AbilityState()
    parsed = parse_abilities(abilities)
    if parsed:
        wolf.components[Abilities] = Abilities(parsed=parsed)
    else:
        wolf.components.pop(Abilities, None)
    return wolf