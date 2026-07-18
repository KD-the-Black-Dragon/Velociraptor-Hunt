"""PR 3: settings persistence for vore content preferences."""

from __future__ import annotations

import json

from src.constants import DEFAULT_VORE_CONTENT_PREFS, VoreContentPreferences
from src.settings_store import SettingsStore


def test_load_missing_file_returns_defaults(tmp_path) -> None:
    path = tmp_path / "settings.json"
    store = SettingsStore.load(path)
    assert store.vore_content == DEFAULT_VORE_CONTENT_PREFS
    assert store.ui_preset == "standard"


def test_save_and_load_round_trip(tmp_path) -> None:
    path = tmp_path / "settings.json"
    prefs = VoreContentPreferences(enabled=frozenset({"OV", "AV"}))
    store = SettingsStore(vore_content=prefs)
    store.save(path)

    loaded = SettingsStore.load(path)
    assert loaded.vore_content == prefs
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["vore_content"]["enabled"] == ["AV", "OV"]
    assert raw["ui_preset"] == "standard"


def test_invalid_json_falls_back_to_defaults(tmp_path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("{not json", encoding="utf-8")
    store = SettingsStore.load(path)
    assert store.vore_content == DEFAULT_VORE_CONTENT_PREFS


def test_empty_enabled_list_falls_back_to_defaults() -> None:
    store = SettingsStore.from_dict({"vore_content": {"enabled": []}})
    assert store.vore_content == DEFAULT_VORE_CONTENT_PREFS


def test_set_ui_preset_persists(tmp_path) -> None:
    path = tmp_path / "settings.json"
    settings = SettingsStore.load(path)
    settings.path = path
    settings.set_ui_preset("wide_sidebar")
    assert settings.ui_preset == "wide_sidebar"
    loaded = SettingsStore.load(path)
    assert loaded.ui_preset == "wide_sidebar"