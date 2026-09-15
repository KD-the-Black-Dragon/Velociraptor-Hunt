"""PR4: crash report formatting, context, and excepthook."""

from __future__ import annotations

import sys
from pathlib import Path
from types import TracebackType
from typing import Any

import pytest
import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.app import App, AppPhase
from src.debug import paths as debug_paths
from src.debug.context import CrashContext, build_crash_context
from src.debug.crash_report import (
    _crash_excepthook,
    _handle_unhandled_exception,
    format_crash_report,
    install_crash_handler,
    register_app,
    write_crash_report,
)
from src.debug.force_crash import ForceCrashError
from src.debug.session_log import (
    SessionLogCoordinator,
    reset_quit_milestone_state,
    should_log_quit_milestone,
)
from src.engine import GameEngine

from tests.map_test_helpers import isolate_other_ais


def test_f6_debug_hotkey_raises_force_crash(monkeypatch) -> None:
    monkeypatch.setattr("src.engine_input.DEBUG_GAMEPLAY_HOTKEYS_ENABLED", True)
    engine = GameEngine()
    isolate_other_ais(engine)
    event = tcod.event.KeyDown(sym=KeySym.F6, scancode=Scancode.UNKNOWN, mod=Modifier.NONE)
    with pytest.raises(ForceCrashError, match="F6 debug force-crash"):
        engine._handle_gameplay_event(event)


@pytest.fixture(autouse=True)
def _reset_quit_skip() -> None:
    reset_quit_milestone_state()
    yield
    reset_quit_milestone_state()


@pytest.fixture
def logs_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    log_root = tmp_path / "logs"
    monkeypatch.setattr(debug_paths, "LOGS_DIR", log_root)
    return log_root


def _sample_context(**overrides: Any) -> CrashContext:
    base = dict(
        timestamp_utc="2026-07-06T14:32:01Z",
        game_version="0.1.0",
        python_version="3.14.0",
        platform_string="Windows-10",
        os_string="Windows 10",
        exc_type_name="ValueError",
        exc_message="something went wrong",
        traceback_text="Traceback (most recent call last):\n  File ...",
        app_phase="PLAY",
        active_modal="digestion_modal",
        floor=6,
        turn=142,
        run_seed=4839204,
        rng_state="[3, (...), None]",
        player_position="(34, 18)",
        player_hp="12/30",
        macguffin_discovered="yes",
        loaded_mods="(none)",
        session_log_path="logs/session_2026-07-06_14-28-15.log",
    )
    base.update(overrides)
    return CrashContext(**base)


def test_format_crash_report_includes_required_sections() -> None:
    text = format_crash_report(_sample_context())
    assert "=== Crash Report ===" in text
    assert "Game version: 0.1.0" in text
    assert "Platform: Windows-10" in text
    assert "OS: Windows 10" in text
    assert "ValueError: something went wrong" in text
    assert "Traceback (most recent call last):" in text
    assert "App phase: PLAY" in text
    assert "Active modal: digestion_modal" in text
    assert "Floor: 6" in text
    assert "Turn: 142" in text
    assert "RNG seed: 4839204" in text
    assert "RNG state: [3, (...), None]" in text
    assert "Player position: (34, 18)" in text
    assert "Player HP: 12/30" in text
    assert "Macguffin discovered: yes" in text
    assert "Loaded mods: (none)" in text
    assert "Session log: logs/session_2026-07-06_14-28-15.log" in text


def test_format_crash_report_uses_none_placeholders() -> None:
    text = format_crash_report(
        _sample_context(active_modal=None, session_log_path=None),
    )
    assert "Active modal: (none)" in text
    assert "Session log: (none)" in text


def test_build_crash_context_from_play_app(
    logs_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    coordinator = SessionLogCoordinator()
    monkeypatch.setattr("src.debug.context.session_log", coordinator)
    coordinator.start_session()
    try:
        app = App()
        app.phase = AppPhase.PLAY
        app.engine = GameEngine()
        isolate_other_ais(app.engine)
        app.engine.help_overlay.open()

        exc = RuntimeError("boom")
        ctx = build_crash_context(app, exc)

        assert ctx.exc_type_name == "RuntimeError"
        assert ctx.exc_message == "boom"
        assert ctx.app_phase == "PLAY"
        assert ctx.active_modal == "help_overlay"
        assert ctx.floor == 1
        assert ctx.turn == 0
        assert ctx.run_seed is not None
        assert ctx.rng_state is not None
        assert ctx.player_position is not None
        assert ctx.player_hp is not None
        assert ctx.macguffin_discovered == "no"
        assert ctx.session_log_path is not None
        assert "session_" in ctx.session_log_path
        assert ctx.session_log_path.endswith(".log")
    finally:
        coordinator.close()


def test_write_crash_report_overwrites_file(logs_dir: Path) -> None:
    write_crash_report(_sample_context(exc_message="first"))
    first = debug_paths.crash_log_path().read_text(encoding="utf-8")
    assert "first" in first

    write_crash_report(_sample_context(exc_message="second"))
    second = debug_paths.crash_log_path().read_text(encoding="utf-8")
    assert "second" in second
    assert "first" not in second


def test_excepthook_writes_crash_log_and_skips_quit(
    logs_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_crash_handler()
    register_app(None)
    exits: list[int] = []
    monkeypatch.setattr(sys, "exit", lambda code=0: exits.append(code))

    try:
        raise ValueError("test crash")
    except ValueError as exc:
        tb: TracebackType | None = exc.__traceback__
        _handle_unhandled_exception(type(exc), exc, tb)

    assert exits == [1]
    assert not should_log_quit_milestone()
    text = debug_paths.crash_log_path().read_text(encoding="utf-8")
    assert "ValueError: test crash" in text


def test_excepthook_ignores_system_exit(
    logs_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_crash_handler()
    called: list[tuple[type[BaseException], BaseException, TracebackType | None]] = []

    def _record(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_tb: TracebackType | None,
    ) -> None:
        called.append((exc_type, exc_value, exc_tb))

    monkeypatch.setattr(
        "src.debug.crash_report._original_excepthook",
        _record,
    )

    exc = SystemExit(0)
    _crash_excepthook(SystemExit, exc, None)

    assert called == [(SystemExit, exc, None)]
    assert not debug_paths.crash_log_path().exists()