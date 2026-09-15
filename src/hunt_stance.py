"""Hunter gait and aim depth."""

from __future__ import annotations

from enum import Enum


class Gait(Enum):
    WALK = "walk"
    QUICK = "quick"
    RUN = "run"
    SNEAK = "sneak"


SPEED_LABEL = {
    Gait.WALK: "walking",
    Gait.QUICK: "quick",
    Gait.RUN: "running",
    Gait.SNEAK: "sneaking",
}


AIM_NONE = 0
AIM_FOCUS = 1
AIM_DEEP = 2
AIM_MAX = AIM_DEEP


def toggle_run(gait: Gait) -> Gait:
    """R: run, or walk if already running. From sneak, R goes to run."""
    if gait is Gait.RUN:
        return Gait.WALK
    return Gait.RUN


def toggle_sneak(gait: Gait) -> Gait:
    """S: sneak, or walk if already sneaking. From run, S goes to sneak."""
    if gait is Gait.SNEAK:
        return Gait.WALK
    return Gait.SNEAK


def raise_aim(depth: int) -> int | None:
    """Next aim depth, or None if already at max (no third stack)."""
    if depth >= AIM_MAX:
        return None
    return depth + 1
