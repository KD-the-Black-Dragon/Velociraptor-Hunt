"""Crowd favor stub — thin meter, recap mood, optional gold crumb."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import attrs

from src.constants import DATA_DIR

MATCH_CROWD_PATH = DATA_DIR / "match_crowd.json"


@attrs.define(frozen=True)
class CrowdConfig:
    start_favor: int = 50
    min_favor: int = 0
    max_favor: int = 100
    on_player_hit: int = 3
    on_player_miss: int = -1
    on_enemy_hit_player: int = -2
    on_win: int = 12
    on_loss: int = -10
    on_surrender: int = -5
    on_digest: int = -20
    on_patron_hit: int = 5
    high_threshold: int = 75
    low_threshold: int = 25
    high_bonus_gold: int = 8
    low_bonus_gold: int = 0
    mood_high: str = "The crowd is roaring for you."
    mood_mid: str = "The crowd watches with mixed interest."
    mood_low: str = "The crowd is restless and unimpressed."


@attrs.define
class CrowdState:
    favor: int = 50

    def clamp(self, cfg: CrowdConfig) -> None:
        self.favor = max(cfg.min_favor, min(cfg.max_favor, self.favor))

    def shift(self, delta: int, cfg: CrowdConfig) -> None:
        self.favor += int(delta)
        self.clamp(cfg)


@lru_cache(maxsize=1)
def load_crowd_config(path: Path | None = None) -> CrowdConfig:
    p = path if path is not None else MATCH_CROWD_PATH
    if not p.is_file():
        return CrowdConfig()
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return CrowdConfig()
    moods = raw.get("moods") if isinstance(raw.get("moods"), dict) else {}
    return CrowdConfig(
        start_favor=int(raw.get("start_favor", 50)),
        min_favor=int(raw.get("min_favor", 0)),
        max_favor=int(raw.get("max_favor", 100)),
        on_player_hit=int(raw.get("on_player_hit", 3)),
        on_player_miss=int(raw.get("on_player_miss", -1)),
        on_enemy_hit_player=int(raw.get("on_enemy_hit_player", -2)),
        on_win=int(raw.get("on_win", 12)),
        on_loss=int(raw.get("on_loss", -10)),
        on_surrender=int(raw.get("on_surrender", -5)),
        on_digest=int(raw.get("on_digest", -20)),
        on_patron_hit=int(raw.get("on_patron_hit", 5)),
        high_threshold=int(raw.get("high_threshold", 75)),
        low_threshold=int(raw.get("low_threshold", 25)),
        high_bonus_gold=int(raw.get("high_bonus_gold", 8)),
        low_bonus_gold=int(raw.get("low_bonus_gold", 0)),
        mood_high=str(moods.get("high") or CrowdConfig.mood_high),
        mood_mid=str(moods.get("mid") or CrowdConfig.mood_mid),
        mood_low=str(moods.get("low") or CrowdConfig.mood_low),
    )


def reset_crowd_config_cache() -> None:
    load_crowd_config.cache_clear()


def mood_for_favor(favor: int, cfg: CrowdConfig) -> str:
    if favor >= cfg.high_threshold:
        return cfg.mood_high
    if favor <= cfg.low_threshold:
        return cfg.mood_low
    return cfg.mood_mid


def settle_crowd_gold(favor: int, cfg: CrowdConfig) -> tuple[int, str]:
    """End-of-match crumb. High crowd: bonus; low: nothing (no fine in stub)."""
    mood = mood_for_favor(favor, cfg)
    if favor >= cfg.high_threshold:
        return max(0, cfg.high_bonus_gold), mood
    if favor <= cfg.low_threshold:
        return max(0, cfg.low_bonus_gold), mood
    return 0, mood
