"""Options menu fullscreen row."""

from __future__ import annotations

import tcod.event
from tcod.event import KeySym, Scancode

from src.options_menu import (
    FULLSCREEN_ROW_INDEX,
    OptionsMenuState,
    format_fullscreen_line,
    handle_options_event,
    option_row_count,
)
from src.settings_store import SettingsStore


def _key(sym: KeySym) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=0)


def test_option_row_count_includes_fullscreen_and_mods() -> None:
    # UI + difficulty + post-swallow + fullscreen + tutorial + mods
    assert option_row_count() == 6


def test_format_fullscreen_line() -> None:
    assert format_fullscreen_line(False) == "Fullscreen:  [Off] ► On"
    assert format_fullscreen_line(True) == "Fullscreen:  Off ► [On]"


def test_fullscreen_row_index_after_ui_layout() -> None:
    state = OptionsMenuState(highlight=FULLSCREEN_ROW_INDEX)
    assert state.on_fullscreen_row is True
    assert state.on_ui_layout_row is False


def test_toggle_fullscreen_without_callback_updates_settings() -> None:
    settings = SettingsStore()
    state = OptionsMenuState(highlight=FULLSCREEN_ROW_INDEX)
    handle_options_event(state, _key(KeySym.RETURN), settings=settings)
    assert settings.window.fullscreen is True
    handle_options_event(state, _key(KeySym.LEFT), settings=settings)
    assert settings.window.fullscreen is False


def test_toggle_fullscreen_invokes_callback() -> None:
    settings = SettingsStore()
    state = OptionsMenuState(highlight=FULLSCREEN_ROW_INDEX)
    calls: list[str] = []

    def _toggle() -> None:
        calls.append("toggle")

    handle_options_event(
        state,
        _key(KeySym.RIGHT),
        settings=settings,
        toggle_fullscreen=_toggle,
    )
    assert calls == ["toggle"]