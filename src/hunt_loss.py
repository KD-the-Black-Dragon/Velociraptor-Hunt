"""Swallow angle, spectacle lines, and belly/digest timing."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import attrs

from src.constants import DATA_DIR
from src.hunt_facing import facing_toward

HUNT_LOSS_PATH = DATA_DIR / "hunt_loss.json"


@attrs.define(frozen=True)
class HuntLossConfig:
    belly_turns: int
    belly_step_chance: float
    swallow_front: tuple[str, ...]
    swallow_side: tuple[str, ...]
    swallow_behind: tuple[str, ...]
    digest: tuple[str, ...]


def attack_angle(
    hunter_x: int,
    hunter_y: int,
    hunter_facing: int,
    raptor_x: int,
    raptor_y: int,
) -> str:
    """front / side / behind relative to the hunter's facing."""
    toward = facing_toward(hunter_x, hunter_y, raptor_x, raptor_y)
    diff = min((toward - hunter_facing) % 8, (hunter_facing - toward) % 8)
    if diff == 0:
        return "front"
    if diff >= 3:
        return "behind"
    return "side"


@lru_cache(maxsize=1)
def load_hunt_loss(path: Path | None = None) -> HuntLossConfig:
    p = path if path is not None else HUNT_LOSS_PATH
    raw = json.loads(p.read_text(encoding="utf-8"))
    return HuntLossConfig(
        belly_turns=int(raw.get("belly_turns", 6)),
        belly_step_chance=float(raw.get("belly_step_chance", 0.5)),
        swallow_front=tuple(raw.get("swallow_front", ("You are swallowed whole.",))),
        swallow_side=tuple(raw.get("swallow_side", ("You are swallowed whole.",))),
        swallow_behind=tuple(raw.get("swallow_behind", ("You are swallowed whole.",))),
        digest=tuple(raw.get("digest", ("You are being digested.",))),
    )


def swallow_lines(angle: str, cfg: HuntLossConfig | None = None) -> tuple[str, ...]:
    cfg = cfg if cfg is not None else load_hunt_loss()
    if angle == "front":
        return cfg.swallow_front
    if angle == "behind":
        return cfg.swallow_behind
    return cfg.swallow_side
