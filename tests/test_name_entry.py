"""Name entry and new-hunt flow."""

from __future__ import annotations

import tcod.event
from tcod.event import KeySym, Scancode

from src.app import AppPhase
from src.name_entry import (
    ANONYMOUS_NAME,
    PLAYER_NAME_MAX_LENGTH,
    NameEntryAction,
    NameEntryState,
    handle_name_entry_event,
    resolve_display_name,
)


def _key(sym: KeySym) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=0)


def test_resolve_display_name_trims_and_defaults() -> None:
    assert resolve_display_name("Alex") == "Alex"
    assert resolve_display_name("  Alex  ") == "Alex"
    assert resolve_display_name("") == ANONYMOUS_NAME
    assert resolve_display_name("   ") == ANONYMOUS_NAME


def test_name_entry_types_and_backspace() -> None:
    state = NameEntryState()
    handle_name_entry_event(state, _key(KeySym.A))
    assert state.buffer == "a"
    handle_name_entry_event(state, _key(KeySym.BACKSPACE))
    assert state.buffer == ""


def test_name_entry_keydown_letters() -> None:
    state = NameEntryState()
    handle_name_entry_event(state, _key(KeySym.A))
    handle_name_entry_event(state, _key(KeySym.B))
    handle_name_entry_event(state, _key(KeySym.C))
    assert state.buffer == "abc"


def test_name_entry_max_length() -> None:
    state = NameEntryState()
    for _ in range(PLAYER_NAME_MAX_LENGTH + 5):
        handle_name_entry_event(state, _key(KeySym.A))
    assert len(state.buffer) == PLAYER_NAME_MAX_LENGTH


def test_name_entry_confirm_and_cancel() -> None:
    state = NameEntryState()
    handle_name_entry_event(state, _key(KeySym.K))
    assert handle_name_entry_event(state, _key(KeySym.RETURN)) is NameEntryAction.CONFIRM
    assert handle_name_entry_event(state, _key(KeySym.ESCAPE)) is NameEntryAction.CANCEL


def test_app_new_hunt_skips_name_goes_to_weapon(tmp_path) -> None:
    from tests.save_test_helpers import app_with_isolated_save
    from tests.ui_test_helpers import make_console

    app = app_with_isolated_save(tmp_path)
    console = make_console()
    app.handle_event(_key(KeySym.RETURN), console=console)
    assert app.phase is AppPhase.WEAPON_SELECT
    app.handle_event(_key(KeySym.RETURN), console=console)
    assert app.phase is AppPhase.HUNT
    assert app.engine is None
    assert app.career is None
    assert app.hunt is not None
    assert app.hunt.hunter_name == ""
    assert app.hunt.weapon_id == "rifle"


def test_app_name_entry_escape_returns_to_menu(tmp_path) -> None:
    from tests.save_test_helpers import app_with_isolated_save

    app = app_with_isolated_save(tmp_path)
    app.handle_event(_key(KeySym.RETURN))
    app.handle_event(_key(KeySym.ESCAPE))
    assert app.phase is AppPhase.MENU
    assert app.engine is None
