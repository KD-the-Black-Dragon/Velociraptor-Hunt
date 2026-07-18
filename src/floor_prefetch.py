"""No-op floor prefetch stub (dungeon prefetch lives under reference/kdvr)."""

from __future__ import annotations

from typing import Any


def menu_prefetch_params(*, seed: int | None = None) -> Any:
    return None


class FloorPrefetch:
    def cancel(self) -> None:
        return None

    def schedule(self, params: Any = None) -> None:
        return None
