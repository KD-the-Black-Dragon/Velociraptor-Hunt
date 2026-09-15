"""MODDING_README + Sample Mod entities refresh on launch (pinned temp roots)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.mods.seed_sample import (
    MODDING_README_FILENAME,
    MODDING_README_TEXT,
    SAMPLE_ENTITIES_JSON,
    SAMPLE_MOD_FOLDER_NAME,
    refresh_modding_readme,
    refresh_sample_mod_entities,
    seed_first_run_mod_content,
)
from src.mods.state import MOD_STATE_FILENAME, read_mod_state, write_mod_state


def test_refresh_modding_readme_writes_when_missing(tmp_path: Path) -> None:
    refresh_modding_readme(tmp_path)
    path = tmp_path / MODDING_README_FILENAME
    assert path.read_text(encoding="utf-8") == MODDING_README_TEXT


def test_refresh_modding_readme_rewrites_stale_contents(tmp_path: Path) -> None:
    path = tmp_path / MODDING_README_FILENAME
    path.write_text("stale guide text\n", encoding="utf-8")
    refresh_modding_readme(tmp_path)
    assert path.read_text(encoding="utf-8") == MODDING_README_TEXT


def test_refresh_modding_readme_skips_identical_contents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / MODDING_README_FILENAME
    path.write_text(MODDING_README_TEXT, encoding="utf-8")
    calls: list[str] = []

    original = Path.write_text

    def _tracking_write(self: Path, *args: object, **kwargs: object) -> None:
        calls.append(str(self))
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", _tracking_write)
    refresh_modding_readme(tmp_path)
    assert calls == []


def test_seed_refreshes_readme_and_sample_after_onboarding(tmp_path: Path) -> None:
    path = tmp_path / MODDING_README_FILENAME
    path.write_text("old\n", encoding="utf-8")
    seed_first_run_mod_content(
        mods_root=tmp_path,
        tutorial_prompt_answered=True,
        vore_prefs_onboarding_complete=True,
    )
    assert path.read_text(encoding="utf-8") == MODDING_README_TEXT
    sample_entities = tmp_path / SAMPLE_MOD_FOLDER_NAME / "entities.json"
    assert sample_entities.read_text(encoding="utf-8") == SAMPLE_ENTITIES_JSON


def test_refresh_sample_mod_creates_folder_and_disabled_state(tmp_path: Path) -> None:
    refresh_sample_mod_entities(tmp_path)
    sample = tmp_path / SAMPLE_MOD_FOLDER_NAME
    assert sample.is_dir()
    assert (sample / "entities.json").read_text(encoding="utf-8") == SAMPLE_ENTITIES_JSON
    assert read_mod_state(sample / MOD_STATE_FILENAME) == (False, 1)


def test_refresh_sample_mod_rewrites_stale_entities(tmp_path: Path) -> None:
    sample = tmp_path / SAMPLE_MOD_FOLDER_NAME
    sample.mkdir()
    entities = sample / "entities.json"
    entities.write_text('{"schema_version": 1, "entities": []}', encoding="utf-8")
    write_mod_state(sample, enabled=True, order=7)
    refresh_sample_mod_entities(tmp_path)
    assert entities.read_text(encoding="utf-8") == SAMPLE_ENTITIES_JSON
    assert read_mod_state(sample / MOD_STATE_FILENAME) == (True, 7)


def test_refresh_sample_mod_skips_identical_entities(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    refresh_sample_mod_entities(tmp_path)
    sample = tmp_path / SAMPLE_MOD_FOLDER_NAME
    entities = sample / "entities.json"
    write_mod_state(sample, enabled=True, order=3)
    calls: list[str] = []
    original = Path.write_text

    def _tracking_write(self: Path, *args: object, **kwargs: object) -> None:
        calls.append(str(self))
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", _tracking_write)
    refresh_sample_mod_entities(tmp_path)
    assert calls == []
    assert read_mod_state(sample / MOD_STATE_FILENAME) == (True, 3)
    assert entities.read_text(encoding="utf-8") == SAMPLE_ENTITIES_JSON


def test_sample_entities_json_parses() -> None:
    from src.data.entity_loader import parse_entity_registry
    import json

    registry = parse_entity_registry(json.loads(SAMPLE_ENTITIES_JSON))
    creature = registry.get("placeholder_creature")
    assert creature.spawn.requires_vore_types == frozenset()
    assert creature.engulfed_flavor is not None
    assert "OV" in creature.engulfed_flavor


def test_stock_entities_ship_empty_requires_vore_types() -> None:
    """Live stock: every spawn has requires_vore_types []. Not a balance pin."""
    from src.data.entity_loader import ENTITIES_PATH, load_entity_registry

    registry = load_entity_registry(ENTITIES_PATH)
    for entity in registry.entities:
        assert entity.spawn.requires_vore_types == frozenset(), entity.id
