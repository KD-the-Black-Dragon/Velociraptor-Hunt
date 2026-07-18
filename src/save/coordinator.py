"""Autosave coordinator stub for career product.

Dungeon run-snapshot autosave lives under ``reference/kdvr/src/save/``.
Career meta uses ``career_store`` instead.
"""

from __future__ import annotations

from typing import Any

from src.save.store import SaveStore

AUTOSAVE_TURN_INTERVAL = 15
AUTOSAVE_TIME_INTERVAL_SECONDS = 30.0


class SaveCoordinator:
    """No-op coordinator so App/settings keep a store probe API."""

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
