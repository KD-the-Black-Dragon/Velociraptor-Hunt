"""PR2: tile scale, runtime console sizing, settings-driven layout preset."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.settings_store import SettingsStore
from src.ui.bootstrap import (
    load_active_layout,
    runtime_console_dimensions,
    window_pixel_size,
)
from src.ui.layout import load_ui_layout


def test_runtime_console_matches_layout_preset() -> None:
    layout = load_ui_layout()
    width, height = runtime_console_dimensions(layout)
    assert width == layout.root_cols
    assert height == layout.root_rows


def test_load_active_layout_uses_settings_preset(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"vore_content": {"enabled": ["OV"]}, "ui_preset": "wide_sidebar"}),
        encoding="utf-8",
    )
    settings = SettingsStore.load(path)
    layout = load_active_layout(settings)
    assert layout.preset_id == "wide_sidebar"
    assert layout.map_viewport_tiles.w == 44


def test_settings_invalid_ui_preset_falls_back_to_default(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"vore_content": {"enabled": ["OV"]}, "ui_preset": "not_a_preset"}),
        encoding="utf-8",
    )
    settings = SettingsStore.load(path)
    assert settings.ui_preset == "standard"


def test_settings_ui_preset_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    store = SettingsStore(ui_preset="wide_sidebar")
    store.save(path)
    loaded = SettingsStore.load(path)
    assert loaded.ui_preset == "wide_sidebar"


def test_default_layout_tile_scale_is_two() -> None:
    layout = load_active_layout()
    assert layout.tile_scale == 2


def test_window_pixel_size_doubles_tile_scale() -> None:
    layout = load_active_layout()
    pixel_w, pixel_h = window_pixel_size(layout, 80, 50)
    assert pixel_w == 80 * layout.tile_px * 2
    assert pixel_h == 50 * layout.tile_px * 2


def test_main_opens_with_first_launch_window_size(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import importlib

    import src.main as main_module
    import src.settings_store
    import src.user_data

    monkeypatch.setenv("KDS_USER_DATA_DIR", str(tmp_path))
    importlib.reload(src.user_data)
    importlib.reload(src.settings_store)
    importlib.reload(main_module)

    captured: dict[str, object] = {}

    class FakeContext:
        def __enter__(self):
            return self

        def __exit__(self, *args: object) -> None:
            return None

    def fake_context_new(**kwargs: object) -> FakeContext:
        captured.update(kwargs)
        return FakeContext()

    monkeypatch.setattr(
        "src.ui.window_state.primary_desktop_pixel_size",
        lambda: (1920, 1080),
    )
    monkeypatch.setattr(main_module.tcod.context, "new", fake_context_new)
    monkeypatch.setattr(main_module, "run_loop", lambda *args, **kwargs: (_ for _ in ()).throw(SystemExit()))
    monkeypatch.setattr(main_module.tcod.event, "wait", lambda: iter([]))
    monkeypatch.setattr(main_module.settings_coordinator, "flush", lambda *args, **kwargs: None)
    monkeypatch.setattr(main_module.settings_coordinator, "close", lambda: None)

    with pytest.raises(SystemExit):
        main_module.main()

    assert captured.get("width") == 1920 - 96
    assert captured.get("height") == 1080 - 96
    console = captured.get("console")
    assert console is not None
    layout = load_active_layout()
    cols, rows = runtime_console_dimensions(layout)
    assert console.width == cols
    assert console.height == rows