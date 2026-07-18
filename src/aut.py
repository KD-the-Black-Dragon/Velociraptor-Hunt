"""Arbitrary Unit of Time (AUT) scheduling — DCSS-style action cooldowns."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import attrs

from src.constants import DATA_DIR

AUT_COSTS_PATH = DATA_DIR / "aut_costs.json"


@attrs.define(frozen=True)
class AutCosts:
    step: float = 0.45
    wait: float = 1.0
    jab_attack: float = 1.0
    standard_attack: float = 1.2


def _parse_costs(data: dict[str, Any]) -> AutCosts:
    return AutCosts(
        step=float(data.get("step", 0.45)),
        wait=float(data.get("wait", 1.0)),
        jab_attack=float(data.get("jab_attack", 1.0)),
        standard_attack=float(data.get("standard_attack", 1.2)),
    )


@lru_cache(maxsize=1)
def load_aut_costs(path: Path | None = None) -> AutCosts:
    p = path if path is not None else AUT_COSTS_PATH
    if not p.is_file():
        return AutCosts()
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return AutCosts()
    return _parse_costs(raw)


def reset_aut_costs_cache() -> None:
    load_aut_costs.cache_clear()


@attrs.define
class AutScheduler:
    """Tracks world time and per-actor ready times.

    *Cooldown time* is when the actor may issue their next action.
    Cooldown never means 'cannot defend' — only next-command recovery.
    **Player always wins ties** when multiple actors share the same ready time.
    """

    world_aut: float = 0.0
    _ready_at: dict[object, float] = attrs.field(factory=dict)

    def register(self, actor: object, *, ready_at: float | None = None) -> None:
        self._ready_at[actor] = self.world_aut if ready_at is None else float(ready_at)

    def unregister(self, actor: object) -> None:
        self._ready_at.pop(actor, None)

    def ready_at(self, actor: object) -> float:
        return float(self._ready_at.get(actor, self.world_aut))

    def is_ready(self, actor: object) -> bool:
        return self.ready_at(actor) <= self.world_aut + 1e-9

    def commit_action(self, actor: object, cost: float) -> None:
        """Resolve action now; actor becomes ready after ``cost`` AUT."""
        base = max(self.world_aut, self.ready_at(actor))
        self._ready_at[actor] = base + max(0.0, float(cost))

    def next_actor(
        self,
        actors: list[object],
        *,
        player: object | None = None,
    ) -> object | None:
        """Advance world_aut to the next ready actor; player wins ties."""
        living = [a for a in actors if a in self._ready_at]
        if not living:
            return None
        min_t = min(self.ready_at(a) for a in living)
        self.world_aut = min_t
        ready = [a for a in living if abs(self.ready_at(a) - min_t) < 1e-9]
        if player is not None and player in ready:
            return player
        return ready[0]
