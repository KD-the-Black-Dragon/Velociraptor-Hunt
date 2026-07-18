"""Match recovery bank + second wind (JSON-driven)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import attrs

from src.constants import DATA_DIR

MATCH_RECOVERY_PATH = DATA_DIR / "match_recovery.json"


@attrs.define(frozen=True)
class SecondWindConfig:
    enabled: bool = True
    id: str = "second_wind"
    name: str = "Second Wind"
    letter: str = "s"
    uses_per_match: int = 1
    ap_cost: float = 0.0
    aut_cost: float = 1.0
    hp_restore: int = 8
    balance_delta: int = 1
    debuff_aut: float = 8.0
    debuff_accuracy_mult: float = 0.9
    debuff_evade_mult: float = 0.9
    description: str = ""


@attrs.define(frozen=True)
class RecoveryConfig:
    crawl_step_aut_mult: float = 3.0
    recovery_bar_fill_per_aut: float = 0.2
    recovery_bar_full: float = 1.0
    recover_to_hp: int = 5
    second_wind: SecondWindConfig = attrs.field(factory=SecondWindConfig)


@lru_cache(maxsize=1)
def load_recovery_config(path: Path | None = None) -> RecoveryConfig:
    p = path if path is not None else MATCH_RECOVERY_PATH
    if not p.is_file():
        return RecoveryConfig()
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return RecoveryConfig()
    sw_raw = raw.get("second_wind") if isinstance(raw.get("second_wind"), dict) else {}
    sw = SecondWindConfig(
        enabled=bool(sw_raw.get("enabled", True)),
        id=str(sw_raw.get("id", "second_wind")),
        name=str(sw_raw.get("name", "Second Wind")),
        letter=str(sw_raw.get("letter", "s"))[:1].lower(),
        uses_per_match=int(sw_raw.get("uses_per_match", 1)),
        ap_cost=float(sw_raw.get("ap_cost", 0)),
        aut_cost=float(sw_raw.get("aut_cost", 1.0)),
        hp_restore=int(sw_raw.get("hp_restore", 8)),
        balance_delta=int(sw_raw.get("balance_delta", 1)),
        debuff_aut=float(sw_raw.get("debuff_aut", 8.0)),
        debuff_accuracy_mult=float(sw_raw.get("debuff_accuracy_mult", 0.9)),
        debuff_evade_mult=float(sw_raw.get("debuff_evade_mult", 0.9)),
        description=str(sw_raw.get("description", "")),
    )
    return RecoveryConfig(
        crawl_step_aut_mult=float(raw.get("crawl_step_aut_mult", 3.0)),
        recovery_bar_fill_per_aut=float(raw.get("recovery_bar_fill_per_aut", 0.2)),
        recovery_bar_full=float(raw.get("recovery_bar_full", 1.0)),
        recover_to_hp=int(raw.get("recover_to_hp", 5)),
        second_wind=sw,
    )


def reset_recovery_config_cache() -> None:
    load_recovery_config.cache_clear()
