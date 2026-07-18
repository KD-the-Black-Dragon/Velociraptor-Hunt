"""PR0: ally improvement data loaders (names, gratitude, introduction)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.data.entity_loader import EntityLoadError, load_entity_registry, parse_entity_registry
from src.data.names_loader import (
    NAMES_PATH,
    NamesLoadError,
    get_names_registry,
    load_names_registry,
    parse_names_registry,
    reset_names_registry,
)
from src.data.rescue_gratitude_loader import (
    RESCUE_GRATITUDE_PATH,
    RescueGratitudeLoadError,
    get_rescue_gratitude_registry,
    load_rescue_gratitude_registry,
    parse_rescue_gratitude_registry,
    reset_rescue_gratitude_registry,
)


def _minimal_entity(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": "test_creature",
        "display_name": "test creature",
        "glyph": "x",
        "fg": [100, 100, 100],
        "alignment": "good",
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


def test_load_default_names_json() -> None:
    registry = load_names_registry(NAMES_PATH)
    assert registry.schema_version == 1
    knight_pool = registry.pool_for("knight")
    assert knight_pool is not None
    assert len(knight_pool) >= 4
    assert all(name.startswith("Sir ") for name in knight_pool)


def test_load_default_rescue_gratitude_json() -> None:
    registry = load_rescue_gratitude_registry(RESCUE_GRATITUDE_PATH)
    assert registry.schema_version == 1
    assert len(registry.lines) >= 3
    assert all("{name}" in line for line in registry.lines)


def test_knight_has_introduction_log_category_in_entities_json() -> None:
    from src.log_categories import MessageCategory

    knight = load_entity_registry().get("knight")
    assert knight.introduction_log_category is MessageCategory.SPEECH


def test_knight_has_introduction_in_entities_json() -> None:
    registry = load_entity_registry()
    knight = registry.get("knight")
    assert knight.introduction is not None
    assert len(knight.introduction) >= 2
    assert all("{name}" in line for line in knight.introduction)


def test_introduction_omitted_parses_as_none() -> None:
    registry = parse_entity_registry(
        {"schema_version": 1, "entities": [_minimal_entity(id="ally")]}
    )
    assert registry.entities[0].introduction is None


def test_introduction_empty_array_fails() -> None:
    with pytest.raises(EntityLoadError, match="introduction"):
        parse_entity_registry(
            {
                "schema_version": 1,
                "entities": [_minimal_entity(id="ally", introduction=[])],
            }
        )


def test_introduction_log_category_invalid_fails() -> None:
    with pytest.raises(EntityLoadError, match="introduction_log_category"):
        parse_entity_registry(
            {
                "schema_version": 1,
                "entities": [
                    _minimal_entity(
                        id="ally",
                        introduction=["I am {name}."],
                        introduction_log_category="not_a_color",
                    )
                ],
            }
        )


def test_introduction_invalid_entry_fails() -> None:
    with pytest.raises(EntityLoadError, match="introduction"):
        parse_entity_registry(
            {
                "schema_version": 1,
                "entities": [_minimal_entity(id="ally", introduction=[""])],
            }
        )


def test_names_singleton_and_reset(tmp_path: Path) -> None:
    path = tmp_path / "names.json"
    path.write_text(
        json.dumps(
            {"schema_version": 1, "names": {"knight": ["Sir Test"]}},
            indent=2,
        ),
        encoding="utf-8",
    )
    reset_names_registry()
    first = get_names_registry()
    second = get_names_registry()
    assert first is second

    reset_names_registry()
    loaded = load_names_registry(path)
    assert loaded.pool_for("knight") == ("Sir Test",)


def test_rescue_gratitude_singleton_and_reset(tmp_path: Path) -> None:
    path = tmp_path / "rescue_gratitude.json"
    path.write_text(
        json.dumps(
            {"schema_version": 1, "lines": ["{name} bows."]},
            indent=2,
        ),
        encoding="utf-8",
    )
    reset_rescue_gratitude_registry()
    first = get_rescue_gratitude_registry()
    second = get_rescue_gratitude_registry()
    assert first is second

    reset_rescue_gratitude_registry()
    loaded = load_rescue_gratitude_registry(path)
    assert loaded.lines == ("{name} bows.",)


def test_names_unknown_top_level_field_fails() -> None:
    with pytest.raises(NamesLoadError, match="unknown top-level"):
        parse_names_registry({"schema_version": 1, "names": {"knight": ["A"]}, "extra": 1})


def test_rescue_gratitude_empty_lines_fails() -> None:
    with pytest.raises(RescueGratitudeLoadError, match="lines"):
        parse_rescue_gratitude_registry({"schema_version": 1, "lines": []})