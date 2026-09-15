"""PR1: Velociraptor Hunt identity and hunt shell."""

from __future__ import annotations

import tcod.event
from tcod.event import KeySym, Scancode

from src.app import App, AppPhase
from src.constants import GAME_TITLE
from src.menu import MainMenuState, MenuAction, build_menu_options, handle_main_menu_event
from src.user_data import APP_NAME
from src.weapon_select import load_hunt_weapons
from tests.save_test_helpers import app_with_isolated_save
from tests.ui_test_helpers import make_console


def _key(sym: KeySym) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=0)


def test_product_identity() -> None:
    assert GAME_TITLE == "Velociraptor Hunt"
    assert APP_NAME == "Velociraptor Hunt"


def test_hunt_weapons_are_the_shipped_trio() -> None:
    weapons = load_hunt_weapons()
    assert tuple(w.weapon_id for w in weapons) == ("rifle", "shotgun", "revolver")


def test_main_menu_is_hunt_shell() -> None:
    assert build_menu_options() == (
        "New Hunt", "Training Mode", "Stats", "Options", "Quit",
    )
    state = MainMenuState()
    assert handle_main_menu_event(state, _key(KeySym.RETURN)) is MenuAction.NEW_HUNT


def test_new_hunt_flow_weapon_then_paddock(tmp_path) -> None:
    app = app_with_isolated_save(tmp_path)
    console = make_console()
    app.handle_event(_key(KeySym.RETURN), console=console)
    assert app.phase is AppPhase.WEAPON_SELECT
    app.handle_event(_key(KeySym.DOWN), console=console)
    app.handle_event(_key(KeySym.RETURN), console=console)
    assert app.phase is AppPhase.HUNT
    assert app.hunt is not None
    assert app.hunt.hunter_name == ""
    assert app.hunt.weapon_id == "shotgun"
    assert app.career is None


def test_weapon_select_escape_returns_to_menu(tmp_path) -> None:
    app = app_with_isolated_save(tmp_path)
    console = make_console()
    app.handle_event(_key(KeySym.RETURN), console=console)
    assert app.phase is AppPhase.WEAPON_SELECT
    app.handle_event(_key(KeySym.ESCAPE), console=console)
    assert app.phase is AppPhase.MENU


def test_hunt_escape_returns_to_menu(tmp_path) -> None:
    app = app_with_isolated_save(tmp_path)
    console = make_console()
    app.handle_event(_key(KeySym.RETURN), console=console)
    app.handle_event(_key(KeySym.RETURN), console=console)
    assert app.phase is AppPhase.HUNT
    app.handle_event(_key(KeySym.ESCAPE), console=console)
    assert app.phase is AppPhase.MENU
    assert app.hunt is None


def test_stats_stub_and_escape(tmp_path) -> None:
    app = app_with_isolated_save(tmp_path)
    while app.menu.highlighted_option != "Stats":
        app.menu.move_down()
    app.handle_event(_key(KeySym.RETURN))
    assert app.phase is AppPhase.STATS
    app.handle_event(_key(KeySym.ESCAPE))
    assert app.phase is AppPhase.MENU


def test_stub_paddock_renders_hunter(tmp_path) -> None:
    app = app_with_isolated_save(tmp_path)
    console = make_console()
    app.handle_event(_key(KeySym.RETURN), console=console)
    app.handle_event(_key(KeySym.RETURN), console=console)
    app.handle_event(_key(KeySym.RETURN), console=console)
    app.render(console)
    chars = {
        chr(int(console.rgba[x, y]["ch"]))
        for y in range(console.height)
        for x in range(console.width)
        if int(console.rgba[x, y]["ch"])
    }
    assert "@" in chars
    assert "#" in chars
