"""PR4: menu load/save integration, overwrite confirm, Ctrl+Q/S."""

from __future__ import annotations

from pathlib import Path

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src import messages
from src.app import App, AppPhase
from src.menu import build_menu_options
from src.new_game_confirm import (
    NewGameConfirmAction,
    NewGameConfirmState,
    handle_new_game_confirm_event,
)
from src.save.coordinator import SaveCoordinator
from src.save.store import SaveStore
from src.save.snapshot import build_run_snapshot
from src.systems.vore import VoreModalSegment

from tests.map_test_helpers import isolate_other_ais
from tests.ui_test_helpers import make_console


def _key(sym: KeySym, *, mod: Modifier = Modifier.NONE) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=mod)


def _app_with_store(tmp_path: Path) -> App:
    store = SaveStore(tmp_path)
    coordinator = SaveCoordinator(store=store, time_interval_seconds=9999.0)
    return App(save_coordinator=coordinator)


def _write_save(tmp_path: Path, *, player_name: str = "SavedHero") -> None:
    store = SaveStore(tmp_path)
    engine = __import__("src.engine", fromlist=["GameEngine"]).GameEngine(
        player_name=player_name,
    )
    isolate_other_ais(engine)
    engine.player_turn_count = 11
    store.save_run(build_run_snapshot(engine))


def _start_play(app: App) -> None:
    console = make_console()
    app.handle_event(_key(KeySym.RETURN), console=console)
    app.handle_event(_key(KeySym.RETURN), console=console)


def test_menu_omits_load_game_when_no_save(tmp_path: Path) -> None:
    app = _app_with_store(tmp_path)
    assert app.phase is AppPhase.MENU
    assert "Load Game" not in app.menu.options


def test_menu_includes_load_game_when_save_exists(tmp_path: Path) -> None:
    _write_save(tmp_path)
    app = _app_with_store(tmp_path)
    assert "Load Game" in app.menu.options


def test_load_game_enters_play_with_restored_state(tmp_path: Path) -> None:
    _write_save(tmp_path, player_name="SavedHero")
    app = _app_with_store(tmp_path)
    console = make_console()

    while app.menu.highlighted_option != "Load Game":
        app.menu.move_down()
    app.handle_event(_key(KeySym.RETURN), console=console)

    assert app.phase is AppPhase.PLAY
    assert app.engine is not None
    assert app.engine.player_name == "SavedHero"
    assert app.engine.player_turn_count == 11
    assert app.save_coordinator.store.probe()


def test_new_game_with_existing_save_requires_overwrite_confirm(tmp_path: Path) -> None:
    _write_save(tmp_path)
    app = _app_with_store(tmp_path)
    console = make_console()

    app.handle_event(_key(KeySym.RETURN), console=console)
    assert app.phase is AppPhase.MENU
    assert app.new_game_confirm is not None

    app.handle_event(_key(KeySym.N), console=console)
    assert app.new_game_confirm is None
    assert app.phase is AppPhase.MENU
    assert app.save_coordinator.store.probe()


def test_new_game_overwrite_confirm_y_then_name_deletes_save(tmp_path: Path) -> None:
    _write_save(tmp_path, player_name="OldRun")
    app = _app_with_store(tmp_path)
    console = make_console()

    app.handle_event(_key(KeySym.RETURN), console=console)
    app.handle_event(_key(KeySym.Y, mod=Modifier.SHIFT), console=console)
    assert app.phase is AppPhase.NAME_ENTRY
    assert app.pending_new_game_overwrite

    for ch in "Alex":
        app.handle_event(_key(getattr(KeySym, ch.upper())), console=console)
    app.handle_event(_key(KeySym.RETURN), console=console)

    assert app.phase is AppPhase.PLAY
    assert app.engine is not None
    assert app.engine.player_name == "alex"
    app.save_coordinator.flush()
    assert app.save_coordinator.store.probe()
    loaded = app.save_coordinator.store.load_best()
    assert loaded["player_name"] == "alex"
    assert loaded["player_turn_count"] == 0


def test_new_game_name_cancel_preserves_existing_save(tmp_path: Path) -> None:
    _write_save(tmp_path, player_name="KeepMe")
    app = _app_with_store(tmp_path)
    console = make_console()

    app.handle_event(_key(KeySym.RETURN), console=console)
    app.handle_event(_key(KeySym.Y, mod=Modifier.SHIFT), console=console)
    app.handle_event(_key(KeySym.ESCAPE), console=console)

    assert app.phase is AppPhase.MENU
    assert not app.pending_new_game_overwrite
    assert app.save_coordinator.store.load_best()["player_name"] == "KeepMe"


def test_ctrl_q_queues_save_and_quit_cancel_keeps_save(tmp_path: Path) -> None:
    app = _app_with_store(tmp_path)
    _start_play(app)
    assert app.engine is not None
    app.engine.player_name = "QuitTest"
    app.engine.player_turn_count = 5

    app.handle_event(_key(KeySym.Q, mod=Modifier.CTRL))
    assert app.quit_confirm is not None
    app.save_coordinator.flush()

    assert app.save_coordinator.store.probe()
    saved = app.save_coordinator.store.load_best()
    assert saved["player_name"] == "QuitTest"
    assert saved["player_turn_count"] == 5

    app.handle_event(_key(KeySym.N))
    assert app.phase is AppPhase.PLAY
    assert app.save_coordinator.store.probe()


def test_ctrl_s_sync_save_adds_message(tmp_path: Path) -> None:
    app = _app_with_store(tmp_path)
    _start_play(app)
    assert app.engine is not None
    app.engine.player_turn_count = 3

    app.handle_event(_key(KeySym.S, mod=Modifier.CTRL))

    assert messages.game_saved() in app.engine.message_log.lines()
    assert app.save_coordinator.store.load_best()["player_turn_count"] == 3


def test_ctrl_s_blocked_during_vore_modal(tmp_path: Path) -> None:
    app = _app_with_store(tmp_path)
    _start_play(app)
    assert app.engine is not None
    app.engine.vore_modal.segment = VoreModalSegment.ATTEMPT

    app.handle_event(_key(KeySym.S, mod=Modifier.CTRL))

    assert messages.game_saved() not in app.engine.message_log.lines()
    assert not app.save_coordinator.store.probe()


def test_new_game_confirm_handler_matches_quit_pattern() -> None:
    state = NewGameConfirmState()
    assert (
        handle_new_game_confirm_event(state, _key(KeySym.Y, mod=Modifier.SHIFT))
        is NewGameConfirmAction.CONFIRM
    )
    assert handle_new_game_confirm_event(state, _key(KeySym.ESCAPE)) is NewGameConfirmAction.CANCEL


def test_build_menu_options_shapes() -> None:
    assert build_menu_options(load_available=False, past_runs_available=False) == (
        "New Game",
        "Options",
        "Credits",
        "Exit",
    )
    assert build_menu_options(load_available=True, past_runs_available=True)[1] == "Load Game"
    assert "Past Runs" in build_menu_options(load_available=True, past_runs_available=True)