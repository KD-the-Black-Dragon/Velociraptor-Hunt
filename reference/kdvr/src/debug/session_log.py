"""Milestone session logging on a background worker thread."""

from __future__ import annotations

import threading
import time
from pathlib import Path

from src.debug import paths as debug_paths

_skip_quit_milestone = False
_skip_quit_reason: str | None = None


def skip_quit_milestone(*, reason: str) -> None:
    """Suppress the process-exit ``Quit`` milestone (validation failure or crash)."""
    global _skip_quit_milestone, _skip_quit_reason
    _skip_quit_milestone = True
    _skip_quit_reason = reason


def should_log_quit_milestone() -> bool:
    """True unless ``skip_quit_milestone()`` was called this process lifetime."""
    return not _skip_quit_milestone


def reset_quit_milestone_state() -> None:
    """Clear skip flag between test cases."""
    global _skip_quit_milestone, _skip_quit_reason
    _skip_quit_milestone = False
    _skip_quit_reason = None


class SessionLogCoordinator:
    """Enqueue plain-text milestone lines on the main thread; write on a daemon worker."""

    def __init__(self) -> None:
        self._condition = threading.Condition()
        self._pending_lines: list[str] = []
        self._stop = False
        self._in_flight = False
        self._session_path: Path | None = None
        self._worker_started = False
        self._worker = threading.Thread(
            target=self._worker_loop,
            name="session-log",
            daemon=True,
        )

    @property
    def session_path(self) -> Path | None:
        """Current session log path, or None before ``start_session()``."""
        return self._session_path

    def start_session(self) -> None:
        """Create ``logs/`` and reserve a session file; start the worker once. Idempotent."""
        if self._session_path is not None:
            return
        try:
            debug_paths.LOGS_DIR.mkdir(parents=True, exist_ok=True)
            path = debug_paths.session_log_path()
            path.touch(exist_ok=True)
            self._session_path = path
        except OSError:
            self._session_path = None
            return
        if not self._worker_started:
            self._worker.start()
            self._worker_started = True

    def log(self, line: str) -> None:
        """Enqueue one milestone line; no-op if session not started. Never raises."""
        if self._session_path is None:
            return
        cleaned = line.replace("\n", " ").strip()
        if not cleaned:
            return
        with self._condition:
            self._pending_lines.append(cleaned)
            self._condition.notify()

    def close(self) -> None:
        """Flush pending lines and stop the worker (call from ``main()`` finally)."""
        with self._condition:
            self._stop = True
            self._condition.notify_all()
        if self._worker_started:
            self._worker.join(timeout=5.0)

    def flush(self, *, timeout: float = 2.0) -> None:
        """Wait until queued lines are written (tests)."""
        end = time.monotonic() + timeout
        with self._condition:
            while self._pending_lines or self._in_flight:
                remaining = end - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("SessionLogCoordinator.flush timed out")
                self._condition.wait(timeout=remaining)

    def _worker_loop(self) -> None:
        while True:
            with self._condition:
                while not self._pending_lines and not self._stop:
                    self._condition.wait()
                if self._stop and not self._pending_lines:
                    return
                batch = self._pending_lines
                self._pending_lines = []
                self._in_flight = True
            try:
                self._write_batch(batch)
            finally:
                with self._condition:
                    self._in_flight = False
                    self._condition.notify_all()

    def _write_batch(self, lines: list[str]) -> None:
        if not lines or self._session_path is None:
            return
        try:
            with self._session_path.open("a", encoding="utf-8") as handle:
                for line in lines:
                    handle.write(f"{line}\n")
        except OSError:
            pass


session_log = SessionLogCoordinator()