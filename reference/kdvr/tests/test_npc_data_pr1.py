"""PR 1: entity JSON loaders, alignment profiles, ignore-unknown semantics."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.components import Alignment, MobilityType
from src.data.alignment_profiles import (
    DEFAULT_DIGESTION_DAMAGE_PER_TICK,
    DEFAULT_DIGEST_TIME,
    alignment_profile,
    digest_time_for,
    digestion_damage_for,
)
from src.data.entity_loader import ENTITIES_PATH, EntityLoadError, load_entity_registry, parse_entity_registry
from src.data.loaders import load_game_data


def _minimal_entity(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": "test_creature",
        "display_name": "test creature",
        "glyph": "x",
        "fg": [100, 100, 100],
        "alignment": "neutral",
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
    base.update(overrides)
    return base


def test_load_default_entities_json_smoke() -> None:
    """Live file must parse; do not pin species set or balance numbers."""
    registry = load_entity_registry(ENTITIES_PATH)
    assert registry.schema_version == 1
    by_id = registry.by_id()
    assert len(by_id) >= 1
    for entity in by_id.values():
        assert entity.id
        assert entity.display_name
        assert entity.spawn.weight >= 0


def test_load_game_data_includes_item_registry() -> None:
    """Smoke: loaders wire entities + items; catalog sizes are free to change."""
    data = load_game_data()
    assert data.entities.schema_version == 1
    assert len(data.entities.entities) >= 1
    assert data.items.schema_version == 1
    assert data.items.weapons or data.items.armor or data.items.potions or data.items.wands


def test_alignment_profiles() -> None:
    evil = alignment_profile(Alignment.EVIL)
    good = alignment_profile(Alignment.GOOD)
    neutral = alignment_profile(Alignment.NEUTRAL)

    assert evil.archetype_id == "wolf"
    assert evil.vore_capable is True
    assert evil.digests is True
    assert evil.follows_on_descent is False

    assert good.archetype_id == "knight"
    assert good.vore_capable is False
    assert good.follows_on_descent is True

    assert neutral.archetype_id == "rabbit"
    assert neutral.vore_capable is False

    assert digestion_damage_for(Alignment.EVIL, None) == DEFAULT_DIGESTION_DAMAGE_PER_TICK
    assert digestion_damage_for(Alignment.EVIL, 5) == 5
    assert digestion_damage_for(Alignment.GOOD, None) is None

    assert digest_time_for(Alignment.EVIL, None) == DEFAULT_DIGEST_TIME
    assert digest_time_for(Alignment.EVIL, 10) == 10
    assert digest_time_for(Alignment.GOOD, None) is None


def test_experience_points_parsed_without_warning() -> None:
    payload = {
        "schema_version": 1,
        "entities": [_minimal_entity(experience_points=50)],
    }
    registry = parse_entity_registry(payload)
    assert registry.entities[0].experience_points == 50
    assert registry.warnings == ()


def test_unknown_trait_warns_once() -> None:
    payload = {
        "schema_version": 1,
        "entities": [_minimal_entity(mystery_flag=True)],
    }
    registry = parse_entity_registry(payload)
    assert len(registry.entities) == 1
    assert len(registry.warnings) == 1
    assert any("mystery_flag" in line and "ignored" in line for line in registry.warnings)


def test_unknown_ability_warns(tmp_path: Path) -> None:
    payload = {
        "schema_version": 1,
        "entities": [_minimal_entity(abilities=["MysteryPower"])],
    }
    registry = parse_entity_registry(payload)
    assert registry.entities[0].abilities == ()
    assert any("MysteryPower" in line for line in registry.warnings)


def test_missing_required_field_raises() -> None:
    payload = {"schema_version": 1, "entities": [_minimal_entity()]}
    del payload["entities"][0]["max_hp"]
    with pytest.raises(EntityLoadError, match="max_hp"):
        parse_entity_registry(payload)


def test_invalid_alignment_raises() -> None:
    payload = {
        "schema_version": 1,
        "entities": [_minimal_entity(alignment="chaotic")],
    }
    with pytest.raises(EntityLoadError, match="alignment"):
        parse_entity_registry(payload)


def test_duplicate_id_raises() -> None:
    payload = {
        "schema_version": 1,
        "entities": [_minimal_entity(id="dup"), _minimal_entity(id="dup")],
    }
    with pytest.raises(EntityLoadError, match="duplicate"):
        parse_entity_registry(payload)


def test_min_damage_greater_than_max_raises() -> None:
    payload = {
        "schema_version": 1,
        "entities": [_minimal_entity(min_damage=5, max_damage=2)],
    }
    with pytest.raises(EntityLoadError, match="min_damage"):
        parse_entity_registry(payload)


def test_mobility_walker_alias() -> None:
    payload = {
        "schema_version": 1,
        "entities": [_minimal_entity(mobility="walker")],
    }
    registry = parse_entity_registry(payload)
    assert registry.entities[0].mobility == MobilityType.GROUND


def test_entities_file_on_disk_matches_schema() -> None:
    raw = json.loads(ENTITIES_PATH.read_text(encoding="utf-8"))
    registry = parse_entity_registry(raw)
    assert registry.warnings == ()


def test_vore_narrative_variant_array() -> None:
    payload = {
        "schema_version": 1,
        "entities": [
            _minimal_entity(
                alignment="evil",
                vore_narratives={
                    "OV": [
                        {"attempt": ["a1"], "success": ["s1"]},
                        {"attempt": ["a2"], "success": ["s2", "s3"]},
                    ]
                },
            )
        ],
    }
    registry = parse_entity_registry(payload)
    variants = registry.entities[0].vore_narratives
    assert variants is not None
    assert len(variants["OV"]) == 2
    assert variants["OV"][1].success == ("s2", "s3")


def test_digestion_player_modal_multi_phase() -> None:
    payload = {
        "schema_version": 1,
        "entities": [
            _minimal_entity(
                alignment="evil",
                digestion_player_modal={
                    "OV": [
                        {"phases": ["phase one", "phase two"]},
                        {"phases": ["alt ending"]},
                    ]
                },
            )
        ],
    }
    registry = parse_entity_registry(payload)
    modal = registry.entities[0].digestion_player_modal
    assert modal is not None
    assert modal["OV"][0] == ("phase one", "phase two")
    assert modal["OV"][1] == ("alt ending",)


def test_narrative_index_picks_variant() -> None:
    import random

    from src.data.narrative_index import NarrativeIndex, reset_narrative_index

    payload = {
        "schema_version": 1,
        "entities": [
            _minimal_entity(
                id="goblin",
                alignment="evil",
                vore_narratives={
                    "OV": [
                        {"attempt": ["one"], "success": ["a"]},
                        {"attempt": ["two"], "success": ["b"]},
                    ]
                },
                digestion_complete={"OV": ["{predator} finished {prey}."]},
            )
        ],
    }
    reset_narrative_index()
    registry = parse_entity_registry(payload)
    index = NarrativeIndex.from_registry(registry)
    rng = random.Random(0)
    seen = {index.pick_vore_variant("goblin", "OV", rng).attempt[0] for _ in range(20)}
    assert seen == {"one", "two"}
    assert index.digestion_complete_lines("goblin", "OV") == (
        "{predator} finished {prey}.",
    )