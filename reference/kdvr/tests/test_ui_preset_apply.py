"""PR11: ui_preset applies on new game and after Options toggle."""

from __future__ import annotations

from unittest.mock import MagicMock

import tcod.console
import tcod.context
import tcod.event
from tcod.event import KeySym, Scancode
from tcod.sdl.video import WindowFlags

from src.app import App, AppPhase
from src.options_menu import UI_LAYOUT_ROW_INDEX
from src.settings_store import SettingsStore
from src.ui.dynamic_layout import cells_from_pixels
from src.ui.layout import load_ui_layout
from src.ui.window_state import WindowPreferences

from tests.ui_test_helpers import default_layout, make_console


def _key(sym: KeySym) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=0)


def test_new_game_uses_wide_sidebar_preset_from_settings(tmp_path) -> None:
    path = tmp_path / "settings.json"
    SettingsStore(ui_preset="wide_sidebar").save(path)
    app = App(settings=SettingsStore.load(path))
    console = make_console()
    layout = app.layout_for_new_game(console)
    assert layout.preset_id == "wide_sidebar"
    assert layout.region("sidebar").w == 36
    assert layout.map_viewport_tiles.w == 44


def test_new_game_uses_standard_preset_from_settings(tmp_path) -> None:
    path = tmp_path / "settings.json"
    SettingsStore(ui_preset="standard").save(path)
    app = App(settings=SettingsStore.load(path))
    console = make_console()
    layout = app.layout_for_new_game(console)
    assert layout.preset_id == "standard"
    assert layout.region("sidebar").w == 23
    assert layout.map_viewport_tiles.w == 57


def test_options_preset_switch_updates_baseline_before_new_game(tmp_path) -> None:
    from src.options_menu import UI_LAYOUT_ROW_INDEX, handle_options_event

    path = tmp_path / "settings.json"
    settings = SettingsStore(ui_preset="standard", path=path)
    settings.save(path)
    app = App(settings=settings, baseline_layout=default_layout())
    console = make_console(80, 42)

    state = app.options
    state.highlight = UI_LAYOUT_ROW_INDEX
    handle_options_event(state, _key(KeySym.RIGHT), settings=settings)
    assert settings.ui_preset == "wide_sidebar"
    app.reload_baseline_from_settings()
    layout = app.layout_for_new_game(console)
    assert layout.region("sidebar").w == 36


def test_options_toggle_to_wide_via_app_handle_event(tmp_path) -> None:
    path = tmp_path / "settings.json"
    settings = SettingsStore(ui_preset="standard", path=path)
    settings.save(path)
    from tests.save_test_helpers import app_with_isolated_save

    app = app_with_isolated_save(tmp_path, settings=settings)
    console = make_console(80, 42)

    app.phase = AppPhase.OPTIONS
    app.options.highlight = UI_LAYOUT_ROW_INDEX
    app.handle_event(_key(KeySym.RIGHT), console=console)

    assert settings.ui_preset == "wide_sidebar"
    assert app.ui_layout is not None
    assert app.ui_layout.preset_id == "wide_sidebar"
    assert app.ui_layout.region("sidebar").w == 36
    assert app.ui_layout.map_viewport_tiles.w == 44
    assert app.ui_layout.sidebar.hp_bar_width == 18

    app.phase = AppPhase.MENU
    app.handle_event(_key(KeySym.RETURN), console=console)
    app.handle_event(_key(KeySym.RETURN), console=console)

    assert app.engine is not None
    assert app.engine.ui_layout.preset_id == "wide_sidebar"
    assert app.engine.ui_layout.region("sidebar").w == 36
    assert app.engine.ui_layout.map_viewport_tiles.w == 44


def test_resize_app_console_refreshes_baseline_from_settings(tmp_path) -> None:
    from src.app import App
    from src.ui.window_state import resize_app_console

    path = tmp_path / "settings.json"
    settings = SettingsStore(ui_preset="standard", path=path)
    settings.save(path)
    app = App(settings=settings)
    assert app.baseline_layout is None

    settings.set_ui_preset("wide_sidebar")
    console = make_console(80, 42)
    resize_app_console(app, pixel_w=80 * 24, pixel_h=42 * 24)

    assert app.baseline_layout is not None
    assert app.baseline_layout.preset_id == "wide_sidebar"
    assert app.ui_layout is not None
    assert app.ui_layout.preset_id == "wide_sidebar"
    assert app.ui_layout.region("sidebar").w == 36


def test_load_game_uses_settings_preset_not_save_snapshot(tmp_path) -> None:
    from src.engine import GameEngine
    from src.save.snapshot import build_run_snapshot
    from src.ui.layout import load_ui_layout
    from tests.save_test_helpers import app_with_isolated_save

    path = tmp_path / "settings.json"
    settings = SettingsStore(ui_preset="wide_sidebar", path=path)
    settings.save(path)
    app = app_with_isolated_save(tmp_path, settings=settings)

    engine = GameEngine(ui_layout=load_ui_layout("standard"))
    snap = build_run_snapshot(engine)
    assert snap["ui_preset"] == "standard"
    app.save_coordinator.store.save_run(snap)

    console = make_console(80, 42)
    app._load_saved_game(console)

    assert app.engine is not None
    assert app.engine.ui_layout.preset_id == "wide_sidebar"
    assert app.engine.ui_layout.region("sidebar").w == 36


class _MaximizedFakeWindow:
    def __init__(self, *, size: tuple[int, int]) -> None:
        self._size = size

    @property
    def size(self) -> tuple[int, int]:
        return self._size

    @property
    def flags(self) -> WindowFlags:
        return WindowFlags.MAXIMIZED


def test_ui_preset_toggle_uses_live_maximized_client_size(tmp_path) -> None:
    """Regression: preset toggle must not shrink the console to stored windowed size."""
    path = tmp_path / "settings.json"
    settings = SettingsStore(
        ui_preset="standard",
        path=path,
        window=WindowPreferences(
            client_width=1360,
            client_height=768,
            maximized=True,
        ),
    )
    app = App(settings=settings, baseline_layout=default_layout())
    console = make_console(80, 45)

    context = MagicMock(spec=tcod.context.Context)
    context.sdl_window = _MaximizedFakeWindow(size=(1920, 1080))

    app.phase = AppPhase.OPTIONS
    app.options.highlight = UI_LAYOUT_ROW_INDEX
    app.handle_event(_key(KeySym.RIGHT), console=console, context=context)

    assert settings.ui_preset == "wide_sidebar"
    assert app.pending_console_replace is not None
    expected_cols, expected_rows = cells_from_pixels(
        load_ui_layout("wide_sidebar"),
        1920,
        1080,
    )
    assert app.pending_console_replace.width == expected_cols
    assert app.pending_console_replace.height == expected_rows


def test_standard_and_wide_presets_differ_at_default_console_size() -> None:
    from src.ui.dynamic_layout import resolve_dynamic_layout
    from src.ui.layout import load_ui_layout

    standard = resolve_dynamic_layout(load_ui_layout("standard"), 80, 42)
    wide = resolve_dynamic_layout(load_ui_layout("wide_sidebar"), 80, 42)

    assert standard.region("sidebar").w != wide.region("sidebar").w
    assert standard.map_viewport_tiles.w != wide.map_viewport_tiles.w
    assert standard.sidebar.hp_bar_width != wide.sidebar.hp_bar_width