"""PR 3 / PR9: options menu toggles, UI layout preset cycling."""

from __future__ import annotations

import json

import tcod.console
import tcod.event
from tcod.event import KeySym, Scancode

from src.app import App, AppPhase
from src.constants import VoreContentPreferences
from src.engine import GameEngine
from src.options_menu import (
    OptionsAction,
    OptionsMenuState,
    UI_LAYOUT_ROW_INDEX,
    format_ui_layout_line,
    handle_options_event,
    render_options_menu,
    try_toggle_vore_type,
)
from src.settings_store import SettingsStore
from src.ui.layout import cycle_ui_preset, list_ui_preset_ids


def _key(sym: KeySym) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=0)


def test_try_toggle_disables_type() -> None:
    prefs = VoreContentPreferences(enabled=frozenset({"OV", "CV", "AV"}))
    updated = try_toggle_vore_type(prefs, "CV")
    assert updated.enabled == frozenset({"OV", "AV"})


def test_try_toggle_cannot_disable_last_type() -> None:
    prefs = VoreContentPreferences(enabled=frozenset({"AV"}))
    assert try_toggle_vore_type(prefs, "AV") is prefs


def test_try_toggle_enables_type() -> None:
    prefs = VoreContentPreferences(enabled=frozenset({"OV"}))
    updated = try_toggle_vore_type(prefs, "CV")
    assert updated.enabled == frozenset({"OV", "CV"})


def test_ov_can_be_disabled_when_others_remain() -> None:
    prefs = VoreContentPreferences(enabled=frozenset({"OV", "CV", "AV"}))
    updated = try_toggle_vore_type(prefs, "OV")
    assert "OV" not in updated.enabled
    assert updated.is_enabled("OV") is False


def test_options_escape_returns_to_menu() -> None:
    state = OptionsMenuState()
    settings = SettingsStore()
    assert handle_options_event(state, _key(KeySym.ESCAPE), settings=settings) is OptionsAction.BACK


def test_options_toggle_persists(tmp_path) -> None:
    path = tmp_path / "settings.json"
    settings = SettingsStore.load(path)
    state = OptionsMenuState()
    state.highlight = 1  # Cock Vore
    handle_options_event(state, _key(KeySym.RETURN), settings=settings)
    assert settings.vore_content.enabled == frozenset({"OV", "AV"})
    assert path.is_file()


def test_options_ui_layout_row_index() -> None:
    state = OptionsMenuState()
    state.highlight = UI_LAYOUT_ROW_INDEX
    assert state.on_ui_layout_row is True


def test_cycle_ui_preset_wraps() -> None:
    preset_ids = list_ui_preset_ids()
    assert len(preset_ids) >= 2
    first = preset_ids[0]
    second = preset_ids[1]
    assert cycle_ui_preset(first, step=1) == second
    assert cycle_ui_preset(second, step=-1) == first


def test_options_ui_preset_right_persists(tmp_path) -> None:
    path = tmp_path / "settings.json"
    settings = SettingsStore.load(path)
    assert settings.ui_preset == "standard"
    state = OptionsMenuState(highlight=UI_LAYOUT_ROW_INDEX)
    handle_options_event(state, _key(KeySym.RIGHT), settings=settings)
    assert settings.ui_preset == "wide_sidebar"
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["ui_preset"] == "wide_sidebar"


def test_options_ui_preset_left_cycles_back(tmp_path) -> None:
    path = tmp_path / "settings.json"
    settings = SettingsStore(ui_preset="wide_sidebar", path=path)
    settings.save(path)
    state = OptionsMenuState(highlight=UI_LAYOUT_ROW_INDEX)
    handle_options_event(state, _key(KeySym.LEFT), settings=settings)
    assert settings.ui_preset == "standard"


def test_format_ui_layout_line_brackets_active_preset() -> None:
    assert format_ui_layout_line("standard") == "UI Layout:  [Standard] ► Wide"
    assert format_ui_layout_line("wide_sidebar") == "UI Layout:  Standard ► [Wide]"


def test_options_ui_preset_display_updates_after_toggle(tmp_path) -> None:
    path = tmp_path / "settings.json"
    settings = SettingsStore(ui_preset="wide_sidebar", path=path)
    settings.save(path)
    state = OptionsMenuState(highlight=UI_LAYOUT_ROW_INDEX)
    handle_options_event(state, _key(KeySym.LEFT), settings=settings)
    assert format_ui_layout_line(settings.ui_preset) == "UI Layout:  [Standard] ► Wide"


def test_render_options_menu_shows_ui_layout_row() -> None:
    console = tcod.console.Console(80, 42, order="F")
    settings = SettingsStore()
    render_options_menu(console, OptionsMenuState(), settings=settings)
    text = "".join(
        chr(int(console.rgba[x, y]["ch"])) if int(console.rgba[x, y]["ch"]) else " "
        for y in range(console.height)
        for x in range(console.width)
    )
    assert "UI Layout:" in text
    assert "Standard" in text


def test_app_options_from_main_menu(tmp_path) -> None:
    path = tmp_path / "settings.json"
    settings = SettingsStore(
        tutorial_prompt_answered=True,
        vore_prefs_onboarding_complete=True,
        path=path,
    )
    settings.save(path)
    app = App(settings=SettingsStore.load(path))
    while app.menu.highlighted_option != "Options":
        app.menu.move_down()
    app.handle_event(_key(KeySym.RETURN))
    assert app.phase is AppPhase.OPTIONS


def test_engine_receives_saved_prefs(tmp_path) -> None:
    path = tmp_path / "settings.json"
    SettingsStore(
        vore_content=VoreContentPreferences(enabled=frozenset({"AV"})),
        tutorial_prompt_answered=True,
        vore_prefs_onboarding_complete=True,
    ).save(path)

    from tests.save_test_helpers import app_with_isolated_save
    from tests.ui_test_helpers import make_console

    app = app_with_isolated_save(tmp_path, settings=SettingsStore.load(path))
    console = make_console()
    app.handle_event(_key(KeySym.RETURN), console=console)  # New Game
    app.handle_event(_key(KeySym.RETURN), console=console)  # Anonymous
    assert app.engine is not None
    assert app.engine.vore_content_prefs.enabled == frozenset({"AV"})


def test_engine_receives_saved_ui_preset(tmp_path) -> None:
    path = tmp_path / "settings.json"
    SettingsStore(
        ui_preset="wide_sidebar",
        tutorial_prompt_answered=True,
        vore_prefs_onboarding_complete=True,
    ).save(path)

    from tests.save_test_helpers import app_with_isolated_save
    from tests.ui_test_helpers import make_console

    app = app_with_isolated_save(tmp_path, settings=SettingsStore.load(path))
    console = make_console()
    app.handle_event(_key(KeySym.RETURN), console=console)  # New Game
    app.handle_event(_key(KeySym.RETURN), console=console)  # Anonymous
    assert app.engine is not None
    assert app.engine.ui_layout.preset_id == "wide_sidebar"
    assert app.engine.ui_layout.map_viewport_tiles.w == 44
    assert app.engine.ui_layout.region("sidebar").w == 36


def test_digestion_uses_engulf_type_not_live_prefs() -> None:
    from tests.test_digestion import _engulf_player_on_wolf, _press

    from src.constants import VoreContentPreferences

    prefs = VoreContentPreferences(enabled=frozenset({"CV"}))
    engine = GameEngine(vore_content_prefs=prefs)
    _engulf_player_on_wolf(engine, player_hp=0, narrative_type="CV")
    engine.vore_content_prefs = VoreContentPreferences(enabled=frozenset({"OV"}))
    for _ in range(2):
        _press(engine, KeySym.PERIOD)
    _press(engine, KeySym.PERIOD)
    assert engine.digestion_modal.active
    # Engulf type CV still used for modal text even if prefs later change to OV-only.
    assert engine.digestion_modal.line.strip()