"""PR5: game over wipes autosave files (permadeath)."""

from __future__ import annotations

from pathlib import Path

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.app import App, AppPhase
from src.past_runs.store import PastRunsStore
from src.save.coordinator import SaveCoordinator
from src.save.store import SaveStore

from tests.test_digestion import (
    _advance_digestion_modal,
    _engulf_player_on_wolf,
    _press,
)
from tests.test_save_menu_pr4 import _write_save
from tests.ui_test_helpers import make_console


def _key(sym: KeySym, *, mod: Modifier = Modifier.NONE) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=mod)


def test_game_over_open_deletes_all_save_files(tmp_path: Path) -> None:
    _write_save(tmp_path, player_name="Doomed")
    store = SaveStore(tmp_path)
    assert store.probe()

    from src.engine import GameEngine

    engine = GameEngine(save_coordinator=SaveCoordinator(store=store))
    _engulf_player_on_wolf(engine, player_hp=0)
    for _ in range(3):
        _press(engine, KeySym.PERIOD)
    _advance_digestion_modal(engine)

    assert engine.game_over.active
    assert not store.probe()


def test_menu_omits_load_after_game_over_recap(tmp_path: Path) -> None:
    _write_save(tmp_path, player_name="Doomed")
    store = SaveStore(tmp_path)
    app = App(
        save_coordinator=SaveCoordinator(store=store),
        past_runs_store=PastRunsStore(tmp_path / "past_runs.json"),
    )
    console = make_console()

    while app.menu.highlighted_option != "Load Game":
        app.menu.move_down()
    app.handle_event(_key(KeySym.RETURN), console=console)
    assert app.phase is AppPhase.PLAY

    _engulf_player_on_wolf(app.engine, player_hp=0)
    for _ in range(3):
        _press(app.engine, KeySym.PERIOD)
    _advance_digestion_modal(app.engine)
    app.handle_event(_key(KeySym.RETURN))

    assert app.phase is AppPhase.MENU
    assert "Load Game" not in app.menu.options
    assert not store.probe()