"""PR2: Credits main-menu integration and phase transitions."""

from __future__ import annotations

import tcod.console
import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.app import App, AppPhase
from src.settings_store import SettingsStore
from src.ui.credits_screen import CREDITS_TITLE, render_credits_screen


def _key(sym: KeySym, *, mod: Modifier = Modifier.NONE) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=mod)


def _onboarded_settings(tmp_path) -> SettingsStore:
    path = tmp_path / "settings.json"
    settings = SettingsStore(
        tutorial_prompt_answered=True,
        vore_prefs_onboarding_complete=True,
        path=path,
    )
    settings.save(path)
    return SettingsStore.load(path)


def test_menu_lists_credits_above_exit(tmp_path) -> None:
    app = App(settings=_onboarded_settings(tmp_path))
    assert "Credits" in app.menu.options
    assert app.menu.options[-2:] == ("Credits", "Exit")


def test_menu_enter_on_credits_opens_screen(tmp_path) -> None:
    app = App(settings=_onboarded_settings(tmp_path))
    while app.menu.highlighted_option != "Credits":
        app.menu.move_down()
    app.handle_event(_key(KeySym.RETURN))
    assert app.phase is AppPhase.CREDITS


def test_credits_escape_returns_to_menu(tmp_path) -> None:
    app = App(settings=_onboarded_settings(tmp_path))
    while app.menu.highlighted_option != "Credits":
        app.menu.move_down()
    app.handle_event(_key(KeySym.RETURN))
    app.handle_event(_key(KeySym.ESCAPE))
    assert app.phase is AppPhase.MENU


def test_credits_ctrl_q_is_no_op(tmp_path) -> None:
    app = App(settings=_onboarded_settings(tmp_path))
    while app.menu.highlighted_option != "Credits":
        app.menu.move_down()
    app.handle_event(_key(KeySym.RETURN))
    assert not app.handle_event(_key(KeySym.Q, mod=Modifier.CTRL))
    assert app.phase is AppPhase.CREDITS


def test_app_render_credits_shows_content(tmp_path) -> None:
    app = App(settings=_onboarded_settings(tmp_path))
    app.phase = AppPhase.CREDITS
    console = tcod.console.Console(80, 44, order="F")
    app.render(console)
    body = ""
    for y in range(console.height - 1):
        for x in range(console.width):
            ch = int(console.rgba[x, y]["ch"])
            body += chr(ch) if ch else " "
    assert CREDITS_TITLE in body
    assert "patreon.com/KD_Dragon" in body

    footer_row = console.height - 1
    footer_text = "".join(
        chr(int(console.rgba[x, footer_row]["ch"]))
        if int(console.rgba[x, footer_row]["ch"])
        else " "
        for x in range(console.width)
    )
    assert "Esc: close" in footer_text


def test_render_credits_screen_matches_app_render() -> None:
    console = tcod.console.Console(80, 44, order="F")
    render_credits_screen(console)
    body = ""
    for y in range(console.height - 1):
        for x in range(console.width):
            ch = int(console.rgba[x, y]["ch"])
            body += chr(ch) if ch else " "
    assert CREDITS_TITLE in body
    assert "furaffinity.net/user/kd" in body