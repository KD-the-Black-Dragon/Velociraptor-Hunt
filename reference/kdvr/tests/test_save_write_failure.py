"""Save failures (e.g. locked autosave file) must not crash the game."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src import messages
from src.app import App
from src.save.coordinator import SaveCoordinator


from tests.ui_test_helpers import make_console


def _key(sym: KeySym, *, mod: Modifier = Modifier.NONE) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=mod)


class LockedStore:
    def probe(self) -> bool:
        return False

    def load_best(self) -> dict[str, Any]:
        raise __import__("src.save.store", fromlist=["SaveNotFoundError"]).SaveNotFoundError()

    def delete_all(self) -> None:
        return None

    def save_run(self, run: dict[str, Any], **kwargs: Any) -> None:
        raise PermissionError("file locked")


def test_save_now_survives_permission_error() -> None:
    coordinator = SaveCoordinator(store=LockedStore())  # type: ignore[arg-type]
    engine = __import__("src.engine", fromlist=["GameEngine"]).GameEngine(
        save_coordinator=coordinator,
    )
    assert coordinator.save_now(engine) is False


def test_ctrl_s_shows_danger_message_when_save_locked(tmp_path: Path) -> None:
    app = App(save_coordinator=SaveCoordinator(store=LockedStore()))  # type: ignore[arg-type]
    console = make_console()
    app.handle_event(_key(KeySym.RETURN), console=console)
    app.handle_event(_key(KeySym.RETURN), console=console)
    assert app.engine is not None

    app.handle_event(_key(KeySym.S, mod=Modifier.CTRL))

    assert messages.save_failed() in app.engine.message_log.lines()
    assert messages.game_saved() not in app.engine.message_log.lines()


def test_background_save_failure_surfaces_on_poll() -> None:
    coordinator = SaveCoordinator(store=LockedStore())  # type: ignore[arg-type]
    engine = __import__("src.engine", fromlist=["GameEngine"]).GameEngine(
        save_coordinator=coordinator,
    )
    coordinator.on_play_enter(engine)
    coordinator.flush()

    coordinator.poll_save_failure(engine)
    assert messages.save_failed() in engine.message_log.lines()


