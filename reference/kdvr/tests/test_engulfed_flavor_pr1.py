"""PR1: engulfed_flavor data parse + narrative index (pinned JSON; no live data/)."""

from __future__ import annotations

import random

import pytest

from src.data.entity_loader import EntityLoadError, parse_entity_registry
from src.data.narrative_index import NarrativeIndex, reset_narrative_index
from tests.test_npc_data_pr1 import _minimal_entity


def test_loader_omits_engulfed_flavor_when_absent() -> None:
    registry = parse_entity_registry(
        {"schema_version": 1, "entities": [_minimal_entity(id="rat")]}
    )
    assert registry.get("rat").engulfed_flavor is None


def test_loader_parses_engulfed_flavor_pools() -> None:
    registry = parse_entity_registry(
        {
            "schema_version": 1,
            "entities": [
                _minimal_entity(
                    id="wolf",
                    alignment="evil",
                    engulfed_flavor={
                        "OV": ["belly squeeze {predator}"],
                        "CV": ["tight tunnel"],
                        "AV": ["rear pressure"],
                    },
                )
            ],
        }
    )
    wolf = registry.get("wolf")
    assert wolf.engulfed_flavor == {
        "OV": ("belly squeeze {predator}",),
        "CV": ("tight tunnel",),
        "AV": ("rear pressure",),
    }


def test_loader_empty_type_array_dropped_all_empty_becomes_none() -> None:
    registry = parse_entity_registry(
        {
            "schema_version": 1,
            "entities": [
                _minimal_entity(
                    id="wolf",
                    alignment="evil",
                    engulfed_flavor={"OV": [], "CV": []},
                )
            ],
        }
    )
    assert registry.get("wolf").engulfed_flavor is None


def test_loader_keeps_nonempty_drops_empty_keys() -> None:
    registry = parse_entity_registry(
        {
            "schema_version": 1,
            "entities": [
                _minimal_entity(
                    id="wolf",
                    alignment="evil",
                    engulfed_flavor={"OV": ["line a"], "CV": [], "AV": ["line b"]},
                )
            ],
        }
    )
    assert registry.get("wolf").engulfed_flavor == {
        "OV": ("line a",),
        "AV": ("line b",),
    }


def test_loader_rejects_non_object_engulfed_flavor() -> None:
    with pytest.raises(EntityLoadError, match="engulfed_flavor must be an object"):
        parse_entity_registry(
            {
                "schema_version": 1,
                "entities": [
                    _minimal_entity(
                        id="wolf",
                        alignment="evil",
                        engulfed_flavor=["not", "an", "object"],
                    )
                ],
            }
        )


def test_loader_rejects_non_string_entries() -> None:
    with pytest.raises(EntityLoadError, match="engulfed_flavor.OV must be a string array"):
        parse_entity_registry(
            {
                "schema_version": 1,
                "entities": [
                    _minimal_entity(
                        id="wolf",
                        alignment="evil",
                        engulfed_flavor={"OV": ["ok", 3]},
                    )
                ],
            }
        )


def test_narrative_index_pick_engulfed_flavor() -> None:
    reset_narrative_index()
    registry = parse_entity_registry(
        {
            "schema_version": 1,
            "entities": [
                _minimal_entity(
                    id="fixture_wolf",
                    alignment="evil",
                    engulfed_flavor={"OV": ["flavor a", "flavor b"]},
                )
            ],
        }
    )
    index = NarrativeIndex.from_registry(registry)
    assert index.engulfed_flavor_lines("fixture_wolf", "OV") == (
        "flavor a",
        "flavor b",
    )
    assert index.engulfed_flavor_lines("fixture_wolf", "CV") == ()
    assert index.pick_engulfed_flavor_line("fixture_wolf", "CV", random.Random(0)) is None
    picked = index.pick_engulfed_flavor_line(
        "fixture_wolf", "OV", random.Random(1)
    )
    assert picked in ("flavor a", "flavor b")


def test_stock_entities_load_without_engulfed_flavor_requirement() -> None:
    """Shipped entities.json must still load (field optional / absent)."""
    from src.data.entity_loader import load_entity_registry, reset_entity_registry_cache

    reset_entity_registry_cache()
    reset_narrative_index()
    registry = load_entity_registry(report_mod_errors=False)
    assert "wolf" in registry.by_id()
    # Stock content intentionally has no fills this PR
    assert registry.get("wolf").engulfed_flavor is None
