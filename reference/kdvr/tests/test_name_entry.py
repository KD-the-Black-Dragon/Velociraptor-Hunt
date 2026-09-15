"""PR 2: name entry, player display name, HUD, and recap."""

from __future__ import annotations

import tcod.console
import tcod.event
from tcod.event import KeySym, Scancode

from src.app import App, AppPhase
from src.constants import SCREEN_HEIGHT, SCREEN_WIDTH
from src.engine import GameEngine
from src.name_entry import (
    ANONYMOUS_NAME,
    PLAYER_NAME_MAX_LENGTH,
    NameEntryAction,
    NameEntryState,
    handle_name_entry_event,
    resolve_display_name,
)
from src.game_over_ending import GameOverEnding
from src.systems.render import render_game_over


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
    for _ in range(PLAYER_NAME_MAX_LENGTH):
        handle_name_entry_event(state, _key(KeySym.X))
    assert len(state.buffer) == PLAYER_NAME_MAX_LENGTH
    handle_name_entry_event(state, _key(KeySym.Y))
    assert len(state.buffer) == PLAYER_NAME_MAX_LENGTH


def test_name_entry_confirm_and_cancel() -> None:
    state = NameEntryState()
    handle_name_entry_event(state, _key(KeySym.K))
    assert handle_name_entry_event(state, _key(KeySym.RETURN)) is NameEntryAction.CONFIRM
    assert handle_name_entry_event(state, _key(KeySym.ESCAPE)) is NameEntryAction.CANCEL


def test_app_new_game_goes_to_name_entry_then_play(tmp_path) -> None:
    from tests.save_test_helpers import app_with_isolated_save
    from tests.ui_test_helpers import make_console

    app = app_with_isolated_save(tmp_path)
    console = make_console()
    app.handle_event(_key(KeySym.RETURN), console=console)
    assert app.phase is AppPhase.NAME_ENTRY

    app.handle_event(_key(KeySym.A), console=console)
    app.handle_event(_key(KeySym.L), console=console)
    app.handle_event(_key(KeySym.E), console=console)
    app.handle_event(_key(KeySym.X), console=console)
    app.handle_event(_key(KeySym.RETURN), console=console)
    assert app.phase is AppPhase.PLAY
    assert app.engine is not None
    assert app.engine.player_name == "alex"


def test_app_blank_name_becomes_anonymous(tmp_path) -> None:
    from tests.save_test_helpers import app_with_isolated_save
    from tests.ui_test_helpers import make_console

    app = app_with_isolated_save(tmp_path)
    console = make_console()
    app.handle_event(_key(KeySym.RETURN), console=console)
    app.handle_event(_key(KeySym.RETURN), console=console)
    assert app.engine is not None
    assert app.engine.player_name == ANONYMOUS_NAME


def test_app_name_entry_escape_returns_to_menu(tmp_path) -> None:
    from tests.save_test_helpers import app_with_isolated_save

    app = app_with_isolated_save(tmp_path)
    app.handle_event(_key(KeySym.RETURN))
    app.handle_event(_key(KeySym.ESCAPE))
    assert app.phase is AppPhase.MENU
    assert app.engine is None


def test_engine_stores_player_name() -> None:
    engine = GameEngine(player_name="Morgan")
    assert engine.player_name == "Morgan"


def test_digestion_recap_uses_player_name() -> None:
    from tests.test_digestion import _advance_digestion_modal, _engulf_player_on_wolf, _press

    engine = GameEngine(player_name="Morgan")
    _engulf_player_on_wolf(engine, player_hp=0)
    for _ in range(3):
        _press(engine, KeySym.PERIOD)
    _advance_digestion_modal(engine)
    assert engine.game_over.player_name == "Morgan"


def test_sidebar_shows_player_name_not_game_title() -> None:
    from tests.ui_test_helpers import render_engine_frame, sidebar_text

    engine = GameEngine(player_name="Alex")
    console = render_engine_frame(engine)
    side_text = sidebar_text(console, engine.ui_layout)
    assert "Alex" in side_text
    assert "KD's Vore Roguelike" not in side_text


def test_render_game_over_shows_run_stats() -> None:
    from src.ui.layout import load_ui_layout

    layout = load_ui_layout()
    vp = layout.map_viewport_tiles
    console = tcod.console.Console(vp.w, vp.h, order="F")
    render_game_over(
        console,
        player_name="Alex",
        ending=GameOverEnding(kind="digested", detail="wolf"),
        monsters_defeated=12,
        runes_collected=3,
        depth=7,
    )
    rendered = ""
    for y in range(vp.h):
        rendered += "".join(
            chr(int(console.rgba[x, y]["ch"])) if int(console.rgba[x, y]["ch"]) else " "
            for x in range(vp.w)
        )
    assert "Alex" in rendered
    assert "Digested by wolf" in rendered
    assert "Monsters defeated: 12" in rendered
    assert "Runes collected: 3" in rendered
    assert "Depth: 7" in rendered
    assert "Score:" not in rendered