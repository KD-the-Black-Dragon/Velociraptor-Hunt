"""Unhandled-exception crash reports and brief player-facing crash UX."""

from __future__ import annotations

import sys
import time
import traceback
from types import TracebackType
from typing import TYPE_CHECKING

import tcod.console
import tcod.context

from src.debug import paths as debug_paths
from src.debug.context import CrashContext, build_crash_context
from src.debug.session_log import skip_quit_milestone
from src.debug_log import debug_print

if TYPE_CHECKING:
    from src.app import App

def _crash_message() -> str:
    return f"A crash was logged to {debug_paths.crash_log_path()}"
_CRASH_OVERLAY_SLEEP_SECONDS = 1.0

_app_ref: App | None = None
_console_ref: tcod.console.Console | None = None
_context_ref: tcod.context.Context | None = None
_original_excepthook = sys.excepthook


def format_crash_report(ctx: CrashContext) -> str:
    """Render the full crash log body."""
    lines = [
        "=== Crash Report ===",
        f"Timestamp: {ctx.timestamp_utc}",
        f"Game version: {ctx.game_version}",
        f"Python: {ctx.python_version}",
        f"Platform: {ctx.platform_string}",
        f"OS: {ctx.os_string}",
        "",
        "--- Exception ---",
        f"{ctx.exc_type_name}: {ctx.exc_message}",
        "",
        "--- Stack trace ---",
        ctx.traceback_text,
        "",
        "--- Game state ---",
    ]

    if ctx.app_phase is not None:
        lines.append(f"App phase: {ctx.app_phase}")
    modal = ctx.active_modal if ctx.active_modal is not None else "(none)"
    lines.append(f"Active modal: {modal}")

    if ctx.floor is not None:
        lines.append(f"Floor: {ctx.floor}")
    if ctx.turn is not None:
        lines.append(f"Turn: {ctx.turn}")
    if ctx.run_seed is not None:
        lines.append(f"RNG seed: {ctx.run_seed}")
    elif ctx.rng_state is not None:
        lines.append("RNG seed: (unknown)")
    if ctx.rng_state is not None:
        lines.append(f"RNG state: {ctx.rng_state}")
    if ctx.player_position is not None:
        lines.append(f"Player position: {ctx.player_position}")
    if ctx.player_hp is not None:
        lines.append(f"Player HP: {ctx.player_hp}")
    if ctx.macguffin_discovered is not None:
        lines.append(f"Macguffin discovered: {ctx.macguffin_discovered}")

    lines.append(f"Loaded mods: {ctx.loaded_mods}")
    lines.extend(
        [
            "",
            "--- Session ---",
            f"Session log: {ctx.session_log_path or '(none)'}",
        ]
    )
    return "\n".join(lines) + "\n"


def write_crash_report(ctx: CrashContext) -> None:
    """Overwrite ``logs/crash.log`` synchronously."""
    try:
        debug_paths.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        debug_paths.crash_log_path().write_text(
            format_crash_report(ctx),
            encoding="utf-8",
        )
    except OSError as err:
        debug_print(f"crash report write failed: {err}")


def _present_crash_overlay(console: tcod.console.Console) -> None:
    message = _crash_message()
    width = console.width
    height = console.height
    text_x = max(0, (width - len(message)) // 2)
    text_y = max(0, height // 2)
    console.clear()
    console.print(text_x, text_y, message, fg=(255, 80, 80))


def _show_crash_message() -> None:
    console = _console_ref
    context = _context_ref
    if console is not None and context is not None:
        try:
            _present_crash_overlay(console)
            context.present(console)
            time.sleep(_CRASH_OVERLAY_SLEEP_SECONDS)
            return
        except Exception as err:
            debug_print(f"crash overlay failed: {err}")
    print(_crash_message(), file=sys.stderr)


def _handle_unhandled_exception(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_tb: TracebackType | None,
) -> None:
    ctx = build_crash_context(
        _app_ref,
        exc_value,
        exc_type=exc_type,
        exc_tb=exc_tb,
    )
    write_crash_report(ctx)
    _show_crash_message()
    skip_quit_milestone(reason="crash")
    sys.exit(1)


def _crash_excepthook(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_tb: TracebackType | None,
) -> None:
    if exc_type in (SystemExit, KeyboardInterrupt):
        _original_excepthook(exc_type, exc_value, exc_tb)
        return
    try:
        _handle_unhandled_exception(exc_type, exc_value, exc_tb)
    except Exception:
        traceback.print_exception(exc_type, exc_value, exc_tb)
        skip_quit_milestone(reason="crash")
        sys.exit(1)


def install_crash_handler() -> None:
    """Install ``sys.excepthook`` early; safe before ``App`` exists."""
    sys.excepthook = _crash_excepthook


def register_app(app: App | None) -> None:
    """Update the crash context source after ``App`` construction."""
    global _app_ref
    _app_ref = app


def register_ui(
    console: tcod.console.Console,
    context: tcod.context.Context,
) -> None:
    """Enable the in-window crash overlay while the tcod context is active."""
    global _console_ref, _context_ref
    _console_ref = console
    _context_ref = context


def unregister_ui() -> None:
    """Clear UI refs when the tcod context exits."""
    global _console_ref, _context_ref
    _console_ref = None
    _context_ref = None