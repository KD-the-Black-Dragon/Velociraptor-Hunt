"""Autosave coordinator: hunt runs use the KDVR rotating slot (sync writes)."""

from __future__ import annotations

from typing import Any

from src.save.store import SaveStore, SaveStoreError

AUTOSAVE_TURN_INTERVAL = 15
AUTOSAVE_TIME_INTERVAL_SECONDS = 30.0


class SaveCoordinator:
    """Hunt autosave via ``SaveStore`` rotate chain; dungeon engine hooks are no-ops."""

    def __init__(self, store: SaveStore | None = None, **_kwargs: Any) -> None:
        self.store = store if store is not None else SaveStore()

    def close(self) -> None:
        return None

    def flush(self, *, timeout: float = 5.0) -> None:
        return None

    def on_play_enter(self, engine: Any) -> None:
        return None

    def on_player_turn_end(self, engine: Any) -> None:
        return None

    def request_sync_save(self, engine: Any) -> None:
        return None

    def consume_save_failure(self) -> bool:
        return False

    def save_hunt(self, session: Any) -> bool:
        from src.hunt_save import snapshot_hunt

        try:
            self.store.save_run(snapshot_hunt(session))
            return True
        except SaveStoreError:
            return False

    def load_hunt(self) -> Any | None:
        from src.hunt_save import hunt_from_snapshot, load_hunt_snapshot

        run = load_hunt_snapshot(self.store)
        if run is None:
            return None
        return hunt_from_snapshot(run)

    def has_hunt_save(self) -> bool:
        from src.hunt_save import probe_hunt_save

        return probe_hunt_save(self.store)

    def wipe_saves(self) -> None:
        self.store.delete_all()
