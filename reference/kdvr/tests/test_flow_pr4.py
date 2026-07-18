"""PR 4: quit confirmation, stubs, recap to menu."""

from __future__ import annotations

from pathlib import Path

import pytest
import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.app import App, AppPhase
from src.engine import EngineEventResult, GameEngine
from src.quit_confirm import QUIT_INVALID_MESSAGE, QuitConfirmAction, handle_quit_confirm_event
from src.quit_confirm import QuitConfirmState
from src.save.coordinator import SaveCoordinator
from src.save.store import SaveStore
from src.past_runs.schema import PastRunRecord
from src.past_runs.store import PastRunsStore
from src.ui.past_runs_screen import PastRunsAction, handle_past_runs_event


def _key(sym: KeySym, *, mod: Modifier = Modifier.NONE) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=mod)


@pytest.fixture
def app(tmp_path: Path) -> App:
    store = SaveStore(tmp_path)
    past_runs = PastRunsStore(tmp_path / "past_runs.json")
    past_runs.append(
        PastRunRecord(
            character_name="Tester",
            ending_kind="digested",
            ending_detail="wolf",
            monsters_defeated=0,
            runes_collected=0,
            depth=1,
            date="01/01/2026",
        )
    )
    return App(
        save_coordinator=SaveCoordinator(store=store),
        past_runs_store=past_runs,
    )


def _start_play(app: App):
    from tests.ui_test_helpers import make_console

    console = make_console()
    app.handle_event(_key(KeySym.RETURN), console=console)
    app.handle_event(_key(KeySym.RETURN), console=console)
    return console


def test_quit_confirm_y_and_n() -> None:
    state = QuitConfirmState()
    assert handle_quit_confirm_event(state, _key(KeySym.Y, mod=Modifier.SHIFT)) is QuitConfirmAction.CONFIRM
    assert handle_quit_confirm_event(state, _key(KeySym.N)) is QuitConfirmAction.CANCEL


def test_quit_confirm_rejects_invalid_keys() -> None:
    state = QuitConfirmState()
    assert handle_quit_confirm_event(state, _key(KeySym.Y)) is QuitConfirmAction.NONE
    assert QUIT_INVALID_MESSAGE in state.error_message
    assert handle_quit_confirm_event(state, _key(KeySym.N, mod=Modifier.SHIFT)) is QuitConfirmAction.NONE


def test_quit_confirm_bare_shift_does_not_show_error() -> None:
    state = QuitConfirmState()
    assert handle_quit_confirm_event(state, _key(KeySym.LSHIFT)) is QuitConfirmAction.NONE
    assert state.error_message == ""


def test_ctrl_q_in_play_opens_quit_confirm(app: App) -> None:
    _start_play(app)
    assert app.phase is AppPhase.PLAY
    app.handle_event(_key(KeySym.Q, mod=Modifier.CTRL))
    assert app.quit_confirm is not None
    assert app.phase is AppPhase.PLAY


def test_quit_confirm_y_returns_to_menu(app: App) -> None:
    _start_play(app)
    app.handle_event(_key(KeySym.Q, mod=Modifier.CTRL))
    app.handle_event(_key(KeySym.Y, mod=Modifier.SHIFT))
    assert app.phase is AppPhase.MENU
    assert app.engine is None


def test_quit_confirm_n_resumes_play(app: App) -> None:
    _start_play(app)
    app.handle_event(_key(KeySym.Q, mod=Modifier.CTRL))
    app.handle_event(_key(KeySym.N))
    assert app.phase is AppPhase.PLAY
    assert app.quit_confirm is None
    assert app.engine is not None


def test_ctrl_q_during_vore_modal_is_no_op(app: App) -> None:
    from tests.test_vore_modal import _open_vore_modal

    _start_play(app)
    assert app.engine is not None
    _open_vore_modal(app.engine)
    app.handle_event(_key(KeySym.Q, mod=Modifier.CTRL))
    assert app.quit_confirm is None
    assert app.engine.vore_modal.active


def test_ctrl_q_during_digestion_modal_is_no_op(app: App) -> None:
    from tests.test_digestion import _engulf_player_on_wolf, _press

    _start_play(app)
    _engulf_player_on_wolf(app.engine, player_hp=0)
    for _ in range(2):
        _press(app.engine, KeySym.PERIOD)
    _press(app.engine, KeySym.PERIOD)
    assert app.engine.digestion_modal.active
    app.handle_event(_key(KeySym.Q, mod=Modifier.CTRL))
    assert app.quit_confirm is None


def test_ctrl_q_during_game_over_recap_is_no_op(app: App) -> None:
    from tests.test_digestion import _advance_digestion_modal, _engulf_player_on_wolf, _press

    _start_play(app)
    _engulf_player_on_wolf(app.engine, player_hp=0)
    for _ in range(3):
        _press(app.engine, KeySym.PERIOD)
    _advance_digestion_modal(app.engine)
    assert app.engine.game_over.active
    app.handle_event(_key(KeySym.Q, mod=Modifier.CTRL))
    assert app.quit_confirm is None


def test_game_over_enter_returns_to_menu_via_app(app: App) -> None:
    from tests.test_digestion import _advance_digestion_modal, _engulf_player_on_wolf, _press

    _start_play(app)
    assert app.engine is not None
    _engulf_player_on_wolf(app.engine, player_hp=0)
    for _ in range(3):
        _press(app.engine, KeySym.PERIOD)
    _advance_digestion_modal(app.engine)
    app.handle_event(_key(KeySym.RETURN))
    assert app.phase is AppPhase.MENU
    assert app.engine is None


def test_engine_recap_dismiss_result() -> None:
    from tests.test_digestion import _advance_digestion_modal, _engulf_player_on_wolf, _press

    engine = GameEngine()
    _engulf_player_on_wolf(engine, player_hp=0)
    for _ in range(3):
        _press(engine, KeySym.PERIOD)
    _advance_digestion_modal(engine)
    assert _press(engine, KeySym.RETURN) is EngineEventResult.RECAP_DISMISSED


def test_engine_ctrl_q_no_longer_exits() -> None:
    engine = GameEngine()
    assert (
        engine.handle_event(_key(KeySym.Q, mod=Modifier.CTRL))
        is EngineEventResult.CONTINUE
    )


def test_load_game_requires_save_file(app: App) -> None:
    assert "Load Game" not in app.menu.options


def test_past_runs_screen_escape_back(app: App) -> None:
    while app.menu.highlighted_option != "Past Runs":
        app.menu.move_down()
    app.handle_event(_key(KeySym.RETURN))
    assert app.phase is AppPhase.PAST_RUNS
    assert handle_past_runs_event(
        app.past_runs_screen,
        _key(KeySym.ESCAPE),
        line_count=3,
        viewport_lines=10,
    ) is PastRunsAction.BACK
    app.handle_event(_key(KeySym.ESCAPE))
    assert app.phase is AppPhase.MENU