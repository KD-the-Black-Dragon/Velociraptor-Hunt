"""Filesystem paths for player-facing diagnostic logs."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.user_data import LOGS_DIR

__all__ = [
    "LOGS_DIR",
    "crash_log_path",
    "session_log_path",
    "startup_error_log_path",
]


def crash_log_path() -> Path:
    """Path to the latest crash report (overwritten on each crash)."""
    return LOGS_DIR / "crash.log"


def startup_error_log_path() -> Path:
    """Path to the append-only startup JSON validation error log."""
    return LOGS_DIR / "startup_error.log"


def session_log_path(*, at: datetime | None = None) -> Path:
    """Path for a new session log file; ``at`` uses local time in the filename."""
    moment = at if at is not None else datetime.now().astimezone()
    stamp = moment.strftime("%Y-%m-%d_%H-%M-%S")
    return LOGS_DIR / f"session_{stamp}.log"