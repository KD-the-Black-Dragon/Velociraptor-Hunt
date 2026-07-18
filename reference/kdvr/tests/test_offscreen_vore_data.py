"""Data layer: offscreen vore/digest objects and narrative index lookup."""

from __future__ import annotations

import random

import pytest

from src.data.entity_loader import EntityLoadError, parse_entity_registry
from src.data.narrative_index import NarrativeIndex, reset_narrative_index

from tests.test_npc_data_pr1 import _minimal_entity


def test_loader_parses_offscreen_vore_object() -> None:
    payload = {
        "schema_version": 1,
        "entities": [
            _minimal_entity(
                id="goblin",
                alignment="evil",
                offscreen_vore={
                    "OV": ["distant gulp"],
                    "CV": ["distant coil"],
                    "AV": ["distant pull"],
                },
                offscreen_digest={
                    "OV": ["distant rumble"],
                    "CV": ["distant slime"],
                    "AV": ["distant compress"],
                },
            )
        ],
    }
    registry = parse_entity_registry(payload)
    goblin = registry.get("goblin")
    assert goblin.offscreen_vore == {
        "OV": ("distant gulp",),
        "CV": ("distant coil",),
        "AV": ("distant pull",),
    }
    assert goblin.offscreen_digest == {
        "OV": ("distant rumble",),
        "CV": ("distant slime",),
        "AV": ("distant compress",),
    }


def test_loader_rejects_empty_offscreen_vore_type_array() -> None:
    payload = {
        "schema_version": 1,
        "entities": [
            _minimal_entity(
                id="goblin",
                alignment="evil",
                offscreen_vore={"OV": []},
            )
        ],
    }
    with pytest.raises(EntityLoadError, match="offscreen_vore.OV must be a non-empty string array"):
        parse_entity_registry(payload)


def test_loader_rejects_invalid_offscreen_vore_shape() -> None:
    payload = {
        "schema_version": 1,
        "entities": [_minimal_entity(id="goblin", alignment="evil", offscreen_vore="nope")],
    }
    with pytest.raises(EntityLoadError, match="offscreen_vore must be an object"):
        parse_entity_registry(payload)


def test_loader_rejects_deprecated_flat_offscreen_keys() -> None:
    payload = {
        "schema_version": 1,
        "entities": [_minimal_entity(id="goblin", alignment="evil", offscreen_ov=["legacy"])],
    }
    with pytest.raises(EntityLoadError, match="offscreen_ov.*deprecated.*offscreen_vore"):
        parse_entity_registry(payload)


def test_loader_parses_npc_vore_log_objects() -> None:
    payload = {
        "schema_version": 1,
        "entities": [
            _minimal_entity(
                id="goblin",
                alignment="evil",
                npc_vore_hit={"OV": ["{predator} swallows {prey}!"]},
                npc_vore_miss={"OV": ["{predator} misses {prey}."]},
            )
        ],
    }
    registry = parse_entity_registry(payload)
    goblin = registry.get("goblin")
    assert goblin.npc_vore_hit == {"OV": ("{predator} swallows {prey}!",)}
    assert goblin.npc_vore_miss == {"OV": ("{predator} misses {prey}.",)}


def test_narrative_index_picks_npc_vore_lines() -> None:
    payload = {
        "schema_version": 1,
        "entities": [
            _minimal_entity(
                id="goblin",
                alignment="evil",
                npc_vore_hit={"OV": ["hit a", "hit b"]},
                npc_vore_miss={"CV": ["miss a"]},
            )
        ],
    }
    reset_narrative_index()
    registry = parse_entity_registry(payload)
    index = NarrativeIndex.from_registry(registry)
    assert index.npc_vore_hit_lines("goblin", "OV") == ("hit a", "hit b")
    assert index.npc_vore_miss_lines("goblin", "CV") == ("miss a",)
    assert index.npc_vore_hit_lines("goblin", "CV") == ()


def test_narrative_index_picks_offscreen_object_lines() -> None:
    payload = {
        "schema_version": 1,
        "entities": [
            _minimal_entity(
                id="goblin",
                alignment="evil",
                offscreen_vore={"OV": ["line a", "line b"]},
                offscreen_digest={"OV": ["digest a", "digest b"]},
            )
        ],
    }
    reset_narrative_index()
    registry = parse_entity_registry(payload)
    index = NarrativeIndex.from_registry(registry)
    rng = random.Random(0)
    assert index.pick_offscreen_vore_line("goblin", "OV", rng) in {"line a", "line b"}
    assert index.pick_offscreen_digest_line("goblin", "OV", rng) in {"digest a", "digest b"}
    assert index.pick_offscreen_vore_line("goblin", "CV", rng) is None
    assert index.pick_offscreen_digest_line("missing", "OV", rng) is None


def test_offscreen_vore_error_names_field_not_digestion_complete() -> None:
    payload = {
        "schema_version": 1,
        "entities": [
            _minimal_entity(
                id="goblin",
                alignment="evil",
                offscreen_vore={"CV": [1, 2]},
            )
        ],
    }
    with pytest.raises(EntityLoadError, match="offscreen_vore.CV") as exc:
        parse_entity_registry(payload)
    assert "digestion_complete" not in str(exc.value)