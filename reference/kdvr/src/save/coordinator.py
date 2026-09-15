"""Background autosave coordinator with coalescing and stable-state gating."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from src.components import Engulfed
from src.debug_log import debug_print
from src.save.snapshot import build_run_snapshot
from src.save.store import SaveStore, SaveStoreError

if TYPE_CHECKING:
    from src.engine import GameEngine

AUTOSAVE_TURN_INTERVAL = 15
AUTOSAVE_TIME_INTERVAL_SECONDS = 30.0


class SaveCoordinator:
    """Queue immutable run snapshots on a background worker with coalescing."""

    def __init__(
        self,
        store: SaveStore | None = None,
        *,
        turn_interval: int = AUTOSAVE_TURN_INTERVAL,
        time_interval_seconds: float = AUTOSAVE_TIME_INTERVAL_SECONDS,
        time_fn: Callable[[], float] | None = None,
    ) -> None:
        self.store = store if store is not None else SaveStore()
        self.turn_interval = turn_interval
        self.time_interval_seconds = time_interval_seconds
        self._time_fn = time_fn if time_fn is not None else time.monotonic
        self._condition = threading.Condition()
        self._pending: dict[str, Any] | None = None
        self._in_flight = False
        self._stop = False
        self._last_save_monotonic = 0.0
        self._last_saved_turn = 0
        self._save_failure_pending = False
        self._worker = threading.Thread(
            target=self._worker_loop,
            name="save-coordinator",
            daemon=True,
        )
        self._worker.start()

    def close(self) -> None:
        """Stop the worker thread (tests and shutdown)."""
        with self._condition:
            self._stop = True
            self._condition.notify_all()
        self._worker.join(timeout=5.0)

    def flush(self, *, timeout: float = 5.0) -> None:
        """Wait until queued work finishes (tests)."""
        deadline = self._time_fn() + timeout
        with self._condition:
            while self._pending is not None or self._in_flight:
                remaining = deadline - self._time_fn()
                if remaining <= 0:
                    raise TimeoutError("SaveCoordinator.flush timed out")
                self._condition.wait(timeout=remaining)

    def on_play_enter(self, engine: GameEngine) -> None:
        """Initial autosave when entering PLAY (new game or load)."""
        if engine.arena_mode or not engine.can_issue_idle_command():
            return
        self._enqueue(build_run_snapshot(engine))

    def on_player_turn_end(self, engine: GameEngine) -> None:
        """Periodic autosave after a player turn when the idle gate passes."""
        if engine.arena_mode or not engine.can_issue_idle_command():
            return
        if not self._should_autosave(engine):
            return
        self._enqueue(build_run_snapshot(engine))

    def on_descend_floor(self, engine: GameEngine) -> None:
        """Autosave after a successful floor descent."""
        if engine.arena_mode or not engine.can_issue_idle_command():
            return
        self._enqueue(build_run_snapshot(engine))

    def prepare_for_game_over_wipe(self) -> None:
        """Drop queued snapshots and wait for in-flight write before permadeath wipe."""
        with self._condition:
            self._pending = None
        self.flush()

    def queue_background_save(self, engine: GameEngine) -> None:
        """Queue a background save (Ctrl+Q hook in PR4)."""
        if engine.arena_mode or not engine.can_issue_idle_command():
            return
        self._enqueue(build_run_snapshot(engine))

    def save_now(self, engine: GameEngine) -> bool:
        """Synchronous main-thread save (Ctrl+S hook in PR4)."""
        if engine.arena_mode:
            return True
        if not engine.can_issue_idle_command():
            return False
        self.flush()
        snapshot = build_run_snapshot(engine)
        try:
            self.store.save_run(snapshot)
        except (SaveStoreError, OSError) as exc:
            debug_print(f"[autosave] sync save failed: {exc}", flush=True)
            self._mark_save_failure()
            return False
        self._record_success(snapshot)
        return True

    def poll_save_failure(self, engine: GameEngine) -> None:
        """Post a danger log line when a background save failed since the last poll."""
        from src.log_categories import MessageCategory
        from src import messages

        with self._condition:
            pending = self._save_failure_pending
            self._save_failure_pending = False
        if pending:
            engine.message_log.add(
                messages.save_failed(),
                category=MessageCategory.DANGER,
            )

    def _should_autosave(self, engine: GameEngine) -> bool:
        if engine.player is not None and Engulfed in engine.player.tags:
            return True
        turn = engine.player_turn_count
        if turn - self._last_saved_turn >= self.turn_interval:
            return True
        if self._time_fn() - self._last_save_monotonic >= self.time_interval_seconds:
            return True
        return False

    def _enqueue(self, snapshot: dict[str, Any]) -> None:
        with self._condition:
            self._pending = snapshot
            debug_print("[autosave] enqueue", flush=True)
            self._condition.notify()

    def _record_success(self, snapshot: dict[str, Any]) -> None:
        with self._condition:
            self._last_save_monotonic = self._time_fn()
            self._last_saved_turn = int(snapshot.get("player_turn_count", 0))

    def _mark_save_failure(self) -> None:
        with self._condition:
            self._save_failure_pending = True

    def _worker_loop(self) -> None:
        debug_print("[autosave] worker started", flush=True)
        while True:
            with self._condition:
                while self._pending is None and not self._stop:
                    self._condition.wait()
                if self._stop and self._pending is None:
                    return
                snapshot = self._pending
                self._pending = None
                self._in_flight = True
            try:
                self.store.save_run(snapshot)
                self._record_success(snapshot)
            except (SaveStoreError, OSError) as exc:
                debug_print(f"[autosave] background save failed: {exc}", flush=True)
                self._mark_save_failure()
            finally:
                with self._condition:
                    self._in_flight = False
                    self._condition.notify_all()