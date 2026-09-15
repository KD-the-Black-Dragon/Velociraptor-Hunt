"""Hunt clock and center-weighted ring-control score."""

from __future__ import annotations

import json
import math
from enum import Enum
from functools import lru_cache
from pathlib import Path

import attrs

from src.constants import DATA_DIR
from src.hunt_aut import tenths
from src.hunt_map import HuntMap

HUNT_CLOCK_PATH = DATA_DIR / "hunt_clock.json"


class RingState(Enum):
    HUNTER_WINNING = "Hunter definitely winning"
    CLOSE = "Close"
    RAPTOR_WINNING = "Raptor definitely winning"


@attrs.define(frozen=True)
class HuntClockConfig:
    duration_aut: float = 320.0
    definitely_margin: float = 12.0
    center_plateau: float = 0.32


@lru_cache(maxsize=1)
def load_hunt_clock(path: Path | None = None) -> HuntClockConfig:
    p = path if path is not None else HUNT_CLOCK_PATH
    if not p.is_file():
        return HuntClockConfig()
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return HuntClockConfig()
    return HuntClockConfig(
        duration_aut=tenths(raw.get("duration_aut", 320.0)),
        definitely_margin=float(raw.get("definitely_margin", 12.0)),
        center_plateau=float(raw.get("center_plateau", 0.32)),
    )


def reset_hunt_clock_cache() -> None:
    load_hunt_clock.cache_clear()


def center_weight(mmap: HuntMap, x: int, y: int) -> float:
    """Full score across the inner plateau (mud + grass ring), then falloff to the rim."""
    dx = x - mmap.center_x
    dy = y - mmap.center_y
    dist = math.hypot(dx, dy)
    if mmap.radius <= 0:
        return 0.0
    plateau = max(0.0, min(0.9, load_hunt_clock().center_plateau)) * mmap.radius
    if dist <= plateau:
        return 1.0
    span = mmap.radius - plateau
    if span <= 0:
        return 0.0
    return max(0.0, 1.0 - (dist - plateau) / span)


def ring_state(hunter_ring: float, raptor_ring: float, margin: float) -> RingState:
    diff = hunter_ring - raptor_ring
    if diff >= margin:
        return RingState.HUNTER_WINNING
    if diff <= -margin:
        return RingState.RAPTOR_WINNING
    return RingState.CLOSE
