"""Arena-career difficulty tiers (JSON)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import attrs

from src.constants import DATA_DIR

DIFFICULTIES_PATH = DATA_DIR / "difficulties.json"


@attrs.define(frozen=True)
class DifficultyDef:
    difficulty_id: str
    label: str
    payout_mult: float = 1.0
    enemy_hp_mult: float = 1.0
    enemy_damage_mult: float = 1.0
    grab_chance_mult: float = 1.0
    extra_green_rounds: bool = False


@attrs.define(frozen=True)
class DifficultiesConfig:
    default_id: str = "normal"
    by_id: dict[str, DifficultyDef] = attrs.field(factory=dict)

    def get(self, difficulty_id: str | None) -> DifficultyDef:
        if difficulty_id and difficulty_id in self.by_id:
            return self.by_id[difficulty_id]
        if self.default_id in self.by_id:
            return self.by_id[self.default_id]
        return DifficultyDef("normal", "Normal")


@lru_cache(maxsize=1)
def load_difficulties(path: Path | None = None) -> DifficultiesConfig:
    p = path if path is not None else DIFFICULTIES_PATH
    if not p.is_file():
        return _fallback()
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return _fallback()
    return _parse(raw)


def reset_difficulties_cache() -> None:
    load_difficulties.cache_clear()


def _fallback() -> DifficultiesConfig:
    defs = {
        "easier": DifficultyDef("easier", "Easier", 0.9, 0.85, 0.85, 0.8, True),
        "normal": DifficultyDef("normal", "Normal"),
        "hard": DifficultyDef("hard", "Hard", 1.15, 1.15, 1.1, 1.15, False),
        "nightmare": DifficultyDef(
            "nightmare", "Nightmare", 1.35, 1.35, 1.25, 1.3, False
        ),
    }
    return DifficultiesConfig(default_id="normal", by_id=defs)


def _parse(raw: dict[str, Any]) -> DifficultiesConfig:
    by_id: dict[str, DifficultyDef] = {}
    for item in raw.get("difficulties") or []:
        if not isinstance(item, dict):
            continue
        did = str(item.get("id") or "")
        if not did:
            continue
        by_id[did] = DifficultyDef(
            difficulty_id=did,
            label=str(item.get("label") or did),
            payout_mult=float(item.get("payout_mult", 1.0)),
            enemy_hp_mult=float(item.get("enemy_hp_mult", 1.0)),
            enemy_damage_mult=float(item.get("enemy_damage_mult", 1.0)),
            grab_chance_mult=float(item.get("grab_chance_mult", 1.0)),
            extra_green_rounds=bool(item.get("extra_green_rounds", False)),
        )
    if not by_id:
        return _fallback()
    default_id = str(raw.get("default") or "normal")
    if default_id not in by_id:
        default_id = next(iter(by_id))
    return DifficultiesConfig(default_id=default_id, by_id=by_id)


def resolve_difficulty(difficulty_id: str | None) -> DifficultyDef:
    return load_difficulties().get(difficulty_id)
