"""Run-fatigue stacks: vision and accuracy. Values are playtest tunables."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import attrs

from src.constants import DATA_DIR

HUNT_FATIGUE_PATH = DATA_DIR / "hunt_fatigue.json"


@attrs.define(frozen=True)
class HuntFatigueConfig:
    per_run_step: int = 1
    max_stack: int = 4
    vision_per_stack: int = 1
    accuracy_per_stack: int = 10
    recovery_turns: int = 3


@lru_cache(maxsize=1)
def load_hunt_fatigue(path: Path | None = None) -> HuntFatigueConfig:
    p = path if path is not None else HUNT_FATIGUE_PATH
    if not p.is_file():
        return HuntFatigueConfig()
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return HuntFatigueConfig()
    return HuntFatigueConfig(
        per_run_step=int(raw.get("per_run_step", 1)),
        max_stack=int(raw.get("max_stack", 4)),
        vision_per_stack=int(raw.get("vision_per_stack", 1)),
        accuracy_per_stack=int(raw.get("accuracy_per_stack", 10)),
        recovery_turns=int(raw.get("recovery_turns", 3)),
    )


def reset_hunt_fatigue_cache() -> None:
    load_hunt_fatigue.cache_clear()


def vision_penalty(stack: int, cfg: HuntFatigueConfig | None = None) -> int:
    cfg = cfg if cfg is not None else load_hunt_fatigue()
    return max(0, int(stack)) * cfg.vision_per_stack


def accuracy_penalty(stack: int, cfg: HuntFatigueConfig | None = None) -> int:
    cfg = cfg if cfg is not None else load_hunt_fatigue()
    return max(0, int(stack)) * cfg.accuracy_per_stack
