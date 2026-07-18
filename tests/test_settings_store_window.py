"""Settings persistence for window preferences."""

from __future__ import annotations

import json

from src.settings_store import SettingsStore
from src.ui.dynamic_layout import DESIGN_PIXEL_HEIGHT, DESIGN_PIXEL_WIDTH


def test_load_missing_window_block_marks_unsaved(tmp_path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"vore_content": {"enabled": ["OV"]}, "ui_preset": "standard"}) + "\n",
        encoding="utf-8",
    )
    settings = SettingsStore.load(path)
    assert settings.window_saved_on_disk is False
    assert settings.window.client_width == DESIGN_PIXEL_WIDTH


def test_window_block_round_trip(tmp_path) -> None:
    path = tmp_path / "settings.json"
    settings = SettingsStore.load(path)
    settings.path = path
    settings.window = settings.window.__class__(
        client_width=1600,
        client_height=900,
        x=80,
        y=90,
        maximized=True,
        fullscreen=False,
    )
    settings.save(path)

    loaded = SettingsStore.load(path)
    assert loaded.window_saved_on_disk is True
    assert loaded.window.client_width == 1600
    assert loaded.window.maximized is True
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["window"]["x"] == 80


def test_invalid_window_sizes_clamped_on_load(tmp_path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps(
            {
                "vore_content": {"enabled": ["OV"]},
                "ui_preset": "standard",
                "window": {
                    "client_width": 640,
                    "client_height": 480,
                    "x": 0,
                    "y": 0,
                    "maximized": False,
                    "fullscreen": False,
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    loaded = SettingsStore.load(path)
    assert loaded.window.client_width == DESIGN_PIXEL_WIDTH
    assert loaded.window.client_height == DESIGN_PIXEL_HEIGHT