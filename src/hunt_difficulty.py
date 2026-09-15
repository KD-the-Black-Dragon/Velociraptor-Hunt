"""Hunt-only difficulty knobs. Never grants omniscience."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import attrs

from src.constants import DATA_DIR

HUNT_DIFFICULTY_PATH = DATA_DIR / "hunt_difficulty.json"


@attrs.define(frozen=True)
class HuntTuning:
    raptor_speed_mult: float = 2.0
    hunter_aut_mult: float = 1.0
    rain_cycle_aut: float = 40.0
    raptor_cone_bonus: int = 0
    los_hot_aut: float = 6.0
    stalk_watch: int = 6
    rain_lead_aut: float = 8.0


def _parse(raw: dict) -> HuntTuning:
    return HuntTuning(
        raptor_speed_mult=float(raw.get("raptor_speed_mult", 2.0)),
        hunter_aut_mult=float(raw.get("hunter_aut_mult", 1.0)),
        rain_cycle_aut=float(raw.get("rain_cycle_aut", 40.0)),
        raptor_cone_bonus=int(raw.get("raptor_cone_bonus", 0)),
        los_hot_aut=float(raw.get("los_hot_aut", 6.0)),
        stalk_watch=int(raw.get("stalk_watch", 6)),
        rain_lead_aut=float(raw.get("rain_lead_aut", 8.0)),
    )


@lru_cache(maxsize=1)
def _table() -> dict[str, HuntTuning]:
    p = HUNT_DIFFICULTY_PATH
    if not p.is_file():
        return {"normal": HuntTuning()}
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {"normal": HuntTuning()}
    out: dict[str, HuntTuning] = {}
    for key, val in raw.items():
        if isinstance(val, dict):
            out[str(key)] = _parse(val)
    if "normal" not in out:
        out["normal"] = HuntTuning()
    return out


def reset_hunt_difficulty_cache() -> None:
    _table.cache_clear()


def hunt_tuning(difficulty_id: str | None) -> HuntTuning:
    table = _table()
    if difficulty_id and difficulty_id in table:
        return table[difficulty_id]
    return table.get("normal", HuntTuning())
