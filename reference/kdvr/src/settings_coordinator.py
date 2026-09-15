"""Background persistence for settings.json (window geometry on resize)."""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any

from src.settings_store import SettingsStore


class SettingsCoordinator:
    """Coalesce settings snapshots and write them on a daemon worker thread."""

    def __init__(self) -> None:
        self._condition = threading.Condition()
        self._pending: dict[str, Any] | None = None
        self._pending_path: Path | None = None
        self._stop = False
        self._in_flight = False
        self._worker = threading.Thread(
            target=self._worker_loop,
            name="settings-coordinator",
            daemon=True,
        )
        self._worker.start()

    def enqueue(self, settings: SettingsStore) -> None:
        """Queue the latest settings snapshot for async write. Never raises."""
        try:
            snapshot = settings.to_dict()
            path = settings.path
        except Exception:
            return
        with self._condition:
            self._pending = snapshot
            self._pending_path = path
            self._condition.notify()

    def close(self) -> None:
        """Flush pending work and stop the worker."""
        with self._condition:
            self._stop = True
            self._condition.notify_all()
        self._worker.join(timeout=5.0)

    def flush(self, *, timeout: float = 5.0) -> None:
        """Wait until queued work finishes (tests)."""
        deadline = time.monotonic() + timeout
        with self._condition:
            while self._pending is not None or self._in_flight:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("SettingsCoordinator.flush timed out")
                self._condition.wait(timeout=remaining)

    def _worker_loop(self) -> None:
        while True:
            with self._condition:
                while self._pending is None and not self._stop:
                    self._condition.wait()
                if self._stop and self._pending is None:
                    return
                snapshot = self._pending
                path = self._pending_path
                self._pending = None
                self._pending_path = None
                self._in_flight = True
            try:
                self._write_snapshot(snapshot, path)
            finally:
                with self._condition:
                    self._in_flight = False
                    self._condition.notify_all()

    def _write_snapshot(self, snapshot: dict[str, Any] | None, path: Path | None) -> None:
        if snapshot is None or path is None:
            return
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(snapshot, indent=2) + "\n",
                encoding="utf-8",
            )
        except OSError:
            return


settings_coordinator = SettingsCoordinator()