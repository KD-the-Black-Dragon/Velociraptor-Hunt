"""Options menu 4K UI scaling row and F10 hotkey."""

from __future__ import annotations

import tcod.console
import tcod.event
from tcod.event import KeySym, Scancode

from src.app import App, AppPhase
from src.options_menu import (
    FOUR_K_SCALING_ROW_INDEX,
    OptionsMenuState,
    format_four_k_scaling_line,
    handle_options_event,
    render_options_menu,
)
from src.settings_store import SettingsStore
from src.ui.bootstrap import load_active_layout


def _key(sym: KeySym) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=0)


def test_format_four_k_scaling_line() -> None:
    assert (
        format_four_k_scaling_line(False)
        == "4K UI scaling:  [Off] ► On  (F10 also toggles)"
    )
    assert (
        format_four_k_scaling_line(True)
        == "4K UI scaling:  Off ► [On]  (F10 also toggles)"
    )


def test_four_k_row_index() -> None:
    state = OptionsMenuState(highlight=FOUR_K_SCALING_ROW_INDEX)
    assert state.on_four_k_scaling_row is True
    assert state.on_fullscreen_row is False


def test_toggle_four_k_scaling_persists(tmp_path) -> None:
    path = tmp_path / "settings.json"
    settings = SettingsStore.load(path)
    settings.path = path
    state = OptionsMenuState(highlight=FOUR_K_SCALING_ROW_INDEX)
    handle_options_event(state, _key(KeySym.RETURN), settings=settings)
    assert settings.four_k_scaling is True
    handle_options_event(state, _key(KeySym.LEFT), settings=settings)
    assert settings.four_k_scaling is False


def test_render_options_shows_four_k_row() -> None:
    console = tcod.console.Console(80, 42, order="F")
    settings = SettingsStore()
    render_options_menu(console, OptionsMenuState(), settings=settings)
    found = False
    for y in range(console.height):
        chars = [
            chr(int(console.rgba[x, y]["ch"])) if int(console.rgba[x, y]["ch"]) else " "
            for x in range(console.width)
        ]
        if "4K UI scaling" in "".join(chars):
            found = True
            break
    assert found


def test_layout_for_run_keeps_four_k_tile_scale(tmp_path) -> None:
    """New Game / Load must not drop 4K scale (that caused a tiny map until F10)."""
    path = tmp_path / "settings.json"
    settings = SettingsStore(path=path, four_k_scaling=True)
    settings.save(path)
    settings = SettingsStore.load(path)
    app = App(settings=settings, phase=AppPhase.MENU)
    console = tcod.console.Console(80, 42, order="F")
    layout = app._layout_for_run(console, ui_preset=settings.ui_preset)
    stock = load_active_layout(SettingsStore(four_k_scaling=False))
    assert settings.four_k_scaling is True
    assert layout.tile_scale == stock.tile_scale * 2


def test_f10_toggles_four_k_scaling_from_menu(tmp_path) -> None:
    path = tmp_path / "settings.json"
    settings = SettingsStore.load(path)
    settings.path = path
    app = App(settings=settings, phase=AppPhase.MENU)
    app.baseline_layout = load_active_layout(settings)
    assert settings.four_k_scaling is False
    scale_before = load_active_layout(settings).tile_scale

    exited = app.handle_event(_key(KeySym.F10), console=None, context=None)
    assert exited is False
    assert settings.four_k_scaling is True
    assert load_active_layout(settings).tile_scale == scale_before * 2
    loaded = SettingsStore.load(path)
    assert loaded.four_k_scaling is True

    app.handle_event(_key(KeySym.F10), console=None, context=None)
    assert settings.four_k_scaling is False
    assert load_active_layout(settings).tile_scale == scale_before
