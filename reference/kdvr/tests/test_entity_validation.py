"""PR2: friendly entities.json validation formatting."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.data.entity_loader import ENTITIES_PATH, EntityLoadError, parse_entity_registry
from src.data.entity_validation import (
    format_entity_load_error,
    format_json_decode_error,
    load_entities_user_facing,
)

from tests.test_npc_data_pr1 import _minimal_entity


def _format(message: str, *, filename: str = "entities.json") -> str:
    return format_entity_load_error(
        EntityLoadError(message),
        path=Path(filename),
    )


@pytest.mark.parametrize(
    ("message", "expected_tail"),
    [
        (
            "entities file must contain an 'entities' array",
            "Problem:\nmust contain an 'entities' array",
        ),
        (
            "entities[0] must be an object",
            "Problem:\nentities[0] must be an object",
        ),
        (
            "duplicate entity id 'wolf'",
            "Entity: wolf\n\nProblem:\nduplicate entity id 'wolf'",
        ),
        (
            "entity 'wolf': glyph must be exactly one character",
            "Entity: wolf\n\nProblem:\nglyph must be exactly one character",
        ),
        (
            "entity 'wolf': min_damage (5) cannot exceed max_damage (2)",
            "Entity: wolf\n\nProblem:\nmin_damage (5) cannot exceed max_damage (2)",
        ),
        (
            "entity 'wolf': missing required object 'spawn'",
            "Entity: wolf\n\nProblem:\nmissing required object 'spawn'",
        ),
        (
            "entity 'wolf': abilities must be a string array",
            "Entity: wolf\n\nProblem:\nabilities must be a string array",
        ),
        (
            "entity 'wolf': summon target 'dragon' is not a known entity id",
            "Entity: wolf\n\nProblem:\nsummon target 'dragon' is not a known entity id",
        ),
        (
            "entity 'wolf': ranged_min_damage (4) cannot exceed ranged_max_damage (2)",
            "Entity: wolf\n\nProblem:\nranged_min_damage (4) cannot exceed ranged_max_damage (2)",
        ),
        (
            "entity 'wolf': digestion_damage_per_tick must be an integer",
            "Entity: wolf\n\nProblem:\ndigestion_damage_per_tick must be an integer",
        ),
        (
            "entity 'wolf': digest_time must be an integer",
            "Entity: wolf\n\nProblem:\ndigest_time must be an integer",
        ),
        (
            "entity 'wolf': digest_time must be an integer >= 1",
            "Entity: wolf\n\nProblem:\ndigest_time must be an integer >= 1",
        ),
        (
            "entity 'wolf': digest_time is only valid for evil entities",
            "Entity: wolf\n\nProblem:\ndigest_time is only valid for evil entities",
        ),
        (
            "entity 'wolf': experience_points must be an integer",
            "Entity: wolf\n\nProblem:\nexperience_points must be an integer",
        ),
        (
            "entity 'wolf': proper_name must be a string or null",
            "Entity: wolf\n\nProblem:\nproper_name must be a string or null",
        ),
        (
            "entity 'wolf': examine must be a string",
            "Entity: wolf\n\nProblem:\nexamine must be a string",
        ),
        (
            "entity 'wolf': spawn_requires_water must be a boolean",
            "Entity: wolf\n\nProblem:\nspawn_requires_water must be a boolean",
        ),
        (
            "entity 'wolf': 'offscreen_ov' is deprecated; use 'offscreen_vore' object keyed by OV/CV/AV",
            "Entity: wolf\n\nProblem:\n'offscreen_ov' is deprecated; use 'offscreen_vore' object keyed by OV/CV/AV",
        ),
        (
            "entity 'wolf': spawn.weight must be >= 0 (0 means never spawn)",
            "Entity: wolf\n\nProblem:\nspawn.weight must be >= 0 (0 means never spawn)",
        ),
        (
            "entity 'wolf': spawn.min_depth cannot exceed spawn.max_depth",
            "Entity: wolf\n\nProblem:\nspawn.min_depth cannot exceed spawn.max_depth",
        ),
        (
            "entity 'wolf': spawn.terrain must be 'land' or 'water'",
            "Entity: wolf\n\nProblem:\nspawn.terrain must be 'land' or 'water'",
        ),
        (
            "entity 'wolf': vore_narratives must be an object",
            "Entity: wolf\n\nProblem:\nvore_narratives must be an object",
        ),
        (
            "entity 'wolf': invalid vore_narratives entry 'OV'",
            "Entity: wolf\n\nProblem:\ninvalid vore_narratives entry 'OV'",
        ),
        (
            "entity 'wolf': vore_narratives.OV must be an object or variant array",
            "Entity: wolf\n\nProblem:\nvore_narratives.OV must be an object or variant array",
        ),
        (
            "entity 'wolf': vore_narratives.OV must not be empty",
            "Entity: wolf\n\nProblem:\nvore_narratives.OV must not be empty",
        ),
        (
            "entity 'wolf': offscreen_vore must be an object",
            "Entity: wolf\n\nProblem:\noffscreen_vore must be an object",
        ),
        (
            "entity 'wolf': invalid offscreen_vore entry 'OV'",
            "Entity: wolf\n\nProblem:\ninvalid offscreen_vore entry 'OV'",
        ),
        (
            "entity 'wolf': offscreen_vore.OV must be a non-empty string array",
            "Entity: wolf\n\nProblem:\noffscreen_vore.OV must be a non-empty string array",
        ),
        (
            "entity 'wolf': introduction must be a non-empty string array",
            "Entity: wolf\n\nProblem:\nintroduction must be a non-empty string array",
        ),
        (
            "entity 'wolf': introduction must contain non-empty strings",
            "Entity: wolf\n\nProblem:\nintroduction must contain non-empty strings",
        ),
        (
            "entity 'wolf'.introduction_log_category: invalid category 'foo'",
            "Entity: wolf\n\nProblem:\nintroduction_log_category: invalid category 'foo'",
        ),
        (
            "entity 'wolf': digestion_player_modal must be an object",
            "Entity: wolf\n\nProblem:\ndigestion_player_modal must be an object",
        ),
        (
            "entity 'wolf': invalid digestion_player_modal entry 'OV'",
            "Entity: wolf\n\nProblem:\ninvalid digestion_player_modal entry 'OV'",
        ),
        (
            "entity 'wolf': alignment must be good, evil, or neutral",
            "Entity: wolf\n\nProblem:\nalignment must be good, evil, or neutral",
        ),
        (
            "entity 'wolf': mobility must be ground, fly, aquatic, or stationary",
            "Entity: wolf\n\nProblem:\nmobility must be ground, fly, aquatic, or stationary",
        ),
        (
            "entity 'wolf': fg must be [r, g, b]",
            "Entity: wolf\n\nProblem:\nfg must be [r, g, b]",
        ),
        (
            "entity 'wolf': fg values must be integers 0-255",
            "Entity: wolf\n\nProblem:\nfg values must be integers 0-255",
        ),
        (
            "entity 'wolf': missing or invalid string 'display_name'",
            "Entity: wolf\n\nProblem:\nmissing or invalid string 'display_name'",
        ),
        (
            "entity 'wolf': missing or invalid integer 'max_hp'",
            "Entity: wolf\n\nProblem:\nmissing or invalid integer 'max_hp'",
        ),
        (
            "entity 'wolf': missing or invalid number 'accuracy'",
            "Entity: wolf\n\nProblem:\nmissing or invalid number 'accuracy'",
        ),
        (
            "entities file: missing or invalid integer 'schema_version'",
            "Problem:\nmissing or invalid integer 'schema_version'",
        ),
    ],
)
def test_format_entity_load_error_golden(message: str, expected_tail: str) -> None:
    formatted = _format(message)
    assert formatted.startswith("entities.json\n\n")
    assert formatted.endswith(expected_tail)


def test_format_json_decode_error() -> None:
    raw = "{\n  \"entities\": [\n"
    try:
        json.loads(raw)
    except json.JSONDecodeError as exc:
        text = format_json_decode_error(exc, path=Path("entities.json"))
    else:
        raise AssertionError("expected JSONDecodeError")
    assert text.startswith("entities.json\n\nProblem:\nInvalid JSON near line")
    assert "column" in text


def test_load_entities_user_facing_duplicate_id(tmp_path: Path) -> None:
    payload = {
        "schema_version": 1,
        "entities": [
            _minimal_entity(id="wolf"),
            _minimal_entity(id="wolf", glyph="y"),
        ],
    }
    path = tmp_path / "entities.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    registry, error = load_entities_user_facing(path)
    assert registry is None
    assert error is not None
    assert "Entity: wolf" in error
    assert "duplicate" in error


def test_load_entities_user_facing_valid(tmp_path: Path) -> None:
    payload = {
        "schema_version": 1,
        "entities": [_minimal_entity()],
    }
    path = tmp_path / "entities.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    registry, error = load_entities_user_facing(path)
    assert error is None
    assert registry is not None
    assert registry.by_id()["test_creature"].id == "test_creature"


def test_load_entities_user_facing_syntax_error(tmp_path: Path) -> None:
    path = tmp_path / "entities.json"
    path.write_text("{ not json", encoding="utf-8")
    registry, error = load_entities_user_facing(path)
    assert registry is None
    assert error is not None
    assert "Invalid JSON" in error
    assert "entities.json" in error


def test_unknown_ability_still_loads_with_warning(tmp_path: Path) -> None:
    entity = _minimal_entity(abilities=["Range55"])
    payload = {"schema_version": 1, "entities": [entity]}
    path = tmp_path / "entities.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    registry, error = load_entities_user_facing(path)
    assert error is None
    assert registry is not None
    assert any("Unknown ability" in line for line in registry.warnings)


def test_format_vore_variant_paths() -> None:
    for path in (
        "vore_narratives.OV",
        "vore_narratives.OV[0]",
        "digestion_player_modal.OV",
        "digestion_player_modal.OV[1]",
        "digestion_complete.OV",
        "npc_vore_hit.OV",
        "npc_vore_miss.OV",
    ):
        formatted = _format(f"entity 'wolf': {path} must be an object")
        assert "Entity: wolf" in formatted
        assert path in formatted


def test_format_digestion_modal_variant_errors() -> None:
    formatted = _format(
        "entity 'wolf': digestion_player_modal.OV[0] must be a string or object with phases"
    )
    assert "digestion_player_modal.OV[0]" in formatted


def test_parse_entity_registry_still_raises_entity_load_error() -> None:
    with pytest.raises(EntityLoadError):
        parse_entity_registry({"schema_version": 1})