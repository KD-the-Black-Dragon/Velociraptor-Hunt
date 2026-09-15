"""Hunt AUT costs — tenths only, data-driven."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import attrs

from src.constants import DATA_DIR

HUNT_AUT_PATH = DATA_DIR / "hunt_aut.json"


def tenths(value: float) -> float:
    """Quantize to one decimal place. AUT is never an integer type."""
    return round(float(value) * 10.0) / 10.0


def format_aut(value: float) -> str:
    return f"{tenths(value):.1f}"


@attrs.define(frozen=True)
class HuntAutCosts:
    wait: float = 0.8
    step: float = 0.8
    walk: float = 0.8
    quick: float = 0.7
    run: float = 0.4
    sneak: float = 1.6
    rotate_45: float = 0.8
    rotate_90: float = 0.8
    sidestep: float = 0.8
    gait: float = 0.0
    aim: float = 0.8
    stand_down: float = 0.8
    fire: float = 0.8

    def step_for(self, gait: str) -> float:
        key = (gait or "walk").lower()
        if key == "run":
            return self.run
        if key == "quick":
            return self.quick
        if key == "sneak":
            return self.sneak
        return self.walk


def _parse(data: dict) -> HuntAutCosts:
    walk = tenths(data.get("walk", data.get("step", 0.8)))
    return HuntAutCosts(
        wait=tenths(data.get("wait", walk)),
        step=tenths(data.get("step", walk)),
        walk=walk,
        quick=tenths(data.get("quick", 0.7)),
        run=tenths(data.get("run", 0.4)),
        sneak=tenths(data.get("sneak", walk * 2.0)),
        rotate_45=tenths(data.get("rotate_45", walk)),
        rotate_90=tenths(data.get("rotate_90", walk)),
        sidestep=tenths(data.get("sidestep", walk)),
        gait=tenths(data.get("gait", 0.0)),
        aim=tenths(data.get("aim", walk)),
        stand_down=tenths(data.get("stand_down", walk)),
        fire=tenths(data.get("fire", walk)),
    )


@lru_cache(maxsize=1)
def load_hunt_aut_costs(path: Path | None = None) -> HuntAutCosts:
    p = path if path is not None else HUNT_AUT_PATH
    if not p.is_file():
        return HuntAutCosts()
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return HuntAutCosts()
    return _parse(raw)


def reset_hunt_aut_costs_cache() -> None:
    load_hunt_aut_costs.cache_clear()
