"""Load and parse ``data/global_tuning.json`` (player / regen / vore / loot knobs)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.constants import DATA_DIR
from src.data.global_tuning_config import (
    GlobalTuning,
    LootTuning,
    PlayerTuning,
    RegenTuning,
    VoreTuning,
)

GLOBAL_TUNING_PATH = DATA_DIR / "global_tuning.json"
GLOBAL_TUNING_SCHEMA_VERSION = 1
GLOBAL_TUNING_FILENAME = "global_tuning.json"


class GlobalTuningLoadError(ValueError):
    pass


def load_global_tuning(
    path: Path | None = None,
    *,
    mods_root: Path | None = None,
    report_mod_errors: bool = True,
) -> GlobalTuning:
    """Load global tuning; default path layers whole-file mod replaces."""
    if path is not None:
        if mods_root is not None:
            raise TypeError("mods_root is only valid when path is None (layered load)")
        with path.open(encoding="utf-8") as handle:
            raw = json.load(handle)
        if not isinstance(raw, dict):
            raise GlobalTuningLoadError("global_tuning file must be a JSON object")
        return parse_global_tuning(raw)

    from src.mods.pipeline import load_global_tuning_layered

    config, _issues = load_global_tuning_layered(
        mods_root=mods_root,
        report=report_mod_errors,
    )
    return config


@lru_cache(maxsize=1)
def default_global_tuning() -> GlobalTuning:
    return load_global_tuning()


def reset_global_tuning_cache() -> None:
    default_global_tuning.cache_clear()


def parse_global_tuning(raw: dict[str, Any]) -> GlobalTuning:
    schema_version = _require_int(raw, "schema_version", context="global_tuning file")
    if schema_version != GLOBAL_TUNING_SCHEMA_VERSION:
        raise GlobalTuningLoadError(
            f"global_tuning file: unsupported schema_version {schema_version}"
        )

    player = _parse_player(raw.get("player"), context="player")
    regen = _parse_regen(raw.get("regen"), context="regen")
    vore = _parse_vore(raw.get("vore"), context="vore")
    loot = _parse_loot(raw.get("loot"), context="loot")

    known = {"schema_version", "player", "regen", "vore", "loot"}
    for key in raw:
        if key not in known:
            raise GlobalTuningLoadError(
                f"global_tuning file: unknown top-level field '{key}'"
            )

    if player.min_damage > player.max_damage:
        raise GlobalTuningLoadError(
            "global_tuning file: player.min_damage must be <= player.max_damage"
        )
    if vore.hit_min > vore.hit_max:
        raise GlobalTuningLoadError(
            "global_tuning file: vore.hit_min must be <= vore.hit_max"
        )
    if not (0.0 < vore.hp_threshold <= 1.0):
        raise GlobalTuningLoadError(
            "global_tuning file: vore.hp_threshold must be in (0, 1]"
        )

    return GlobalTuning(
        schema_version=schema_version,
        player=player,
        regen=regen,
        vore=vore,
        loot=loot,
    )


def _parse_player(raw: Any, *, context: str) -> PlayerTuning:
    if not isinstance(raw, dict):
        raise GlobalTuningLoadError(f"global_tuning file: '{context}' must be an object")
    max_hp = _require_int(raw, "max_hp", context=context)
    evade = _require_number(raw, "evade", context=context)
    ac = _require_int(raw, "ac", context=context)
    min_damage = _require_int(raw, "min_damage", context=context)
    max_damage = _require_int(raw, "max_damage", context=context)
    accuracy = _require_number(raw, "accuracy", context=context)
    if max_hp < 1:
        raise GlobalTuningLoadError(f"{context}: max_hp must be >= 1")
    if min_damage < 0 or max_damage < 0:
        raise GlobalTuningLoadError(f"{context}: damage values must be >= 0")
    if evade < 0 or ac < 0:
        raise GlobalTuningLoadError(f"{context}: evade and ac must be >= 0")
    if accuracy < 0:
        raise GlobalTuningLoadError(f"{context}: accuracy must be >= 0")
    _reject_unknown(
        raw,
        {"max_hp", "accuracy", "evade", "ac", "min_damage", "max_damage"},
        context=context,
    )
    return PlayerTuning(
        max_hp=max_hp,
        accuracy=float(accuracy),
        evade=float(evade),
        ac=ac,
        min_damage=min_damage,
        max_damage=max_damage,
    )


def _parse_regen(raw: Any, *, context: str) -> RegenTuning:
    if not isinstance(raw, dict):
        raise GlobalTuningLoadError(f"global_tuning file: '{context}' must be an object")
    hp = _require_int(raw, "hp", context=context)
    every_n = _require_int(raw, "every_n_player_turns", context=context)
    evil_every_n = _require_int(raw, "evil_every_n_player_turns", context=context)
    if hp < 0:
        raise GlobalTuningLoadError(f"{context}: hp must be >= 0")
    if every_n < 1 or evil_every_n < 1:
        raise GlobalTuningLoadError(
            f"{context}: every_n_player_turns values must be >= 1"
        )
    _reject_unknown(
        raw,
        {"hp", "every_n_player_turns", "evil_every_n_player_turns"},
        context=context,
    )
    return RegenTuning(
        hp=hp,
        every_n_player_turns=every_n,
        evil_every_n_player_turns=evil_every_n,
    )


def _parse_vore(raw: Any, *, context: str) -> VoreTuning:
    if not isinstance(raw, dict):
        raise GlobalTuningLoadError(f"global_tuning file: '{context}' must be an object")
    hp_threshold = _require_number(raw, "hp_threshold", context=context)
    hit_min = _require_number(raw, "hit_min", context=context)
    hit_max = _require_number(raw, "hit_max", context=context)
    escape_base = _require_number(raw, "escape_base", context=context)
    escape_per_fail = _require_number(raw, "escape_per_fail", context=context)
    struggle_damage = _require_int(raw, "struggle_damage", context=context)
    if hit_min < 0 or hit_max < 0:
        raise GlobalTuningLoadError(f"{context}: hit_min/hit_max must be >= 0")
    if escape_base < 0 or escape_per_fail < 0:
        raise GlobalTuningLoadError(f"{context}: escape values must be >= 0")
    if struggle_damage < 0:
        raise GlobalTuningLoadError(f"{context}: struggle_damage must be >= 0")
    _reject_unknown(
        raw,
        {
            "hp_threshold",
            "hit_min",
            "hit_max",
            "escape_base",
            "escape_per_fail",
            "struggle_damage",
        },
        context=context,
    )
    return VoreTuning(
        hp_threshold=float(hp_threshold),
        hit_min=float(hit_min),
        hit_max=float(hit_max),
        escape_base=float(escape_base),
        escape_per_fail=float(escape_per_fail),
        struggle_damage=struggle_damage,
    )


def _parse_loot(raw: Any, *, context: str) -> LootTuning:
    if not isinstance(raw, dict):
        raise GlobalTuningLoadError(f"global_tuning file: '{context}' must be an object")
    max_items = _require_int(raw, "max_floor_item_placements", context=context)
    min_potions = _require_int(raw, "min_floor_potions", context=context)
    if max_items < 0 or min_potions < 0:
        raise GlobalTuningLoadError(
            f"{context}: max_floor_item_placements and min_floor_potions must be >= 0"
        )
    _reject_unknown(
        raw,
        {"max_floor_item_placements", "min_floor_potions"},
        context=context,
    )
    return LootTuning(
        max_floor_item_placements=max_items,
        min_floor_potions=min_potions,
    )


def _require_int(raw: dict[str, Any], key: str, *, context: str) -> int:
    value = raw.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise GlobalTuningLoadError(f"{context}: '{key}' must be an integer")
    return value


def _require_number(raw: dict[str, Any], key: str, *, context: str) -> float:
    value = raw.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise GlobalTuningLoadError(f"{context}: '{key}' must be a number")
    return float(value)


def _reject_unknown(raw: dict[str, Any], known: set[str], *, context: str) -> None:
    for key in raw:
        if key not in known:
            raise GlobalTuningLoadError(f"{context}: unknown field '{key}'")
