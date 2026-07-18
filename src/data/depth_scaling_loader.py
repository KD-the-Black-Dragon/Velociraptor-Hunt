"""Load and parse ``data/depth_scaling.json`` (difficulty profiles + dual-int schedules)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.components import Alignment
from src.constants import DATA_DIR
from src.data.depth_scaling_config import (
    ALL_STAT_KEYS,
    ALIGNMENT_BY_NAME,
    DepthScalingConfig,
    DifficultyProfile,
    FLOAT_STAT_KEYS,
    PrefixSpawnConfig,
    SpawnAiFreezeConfig,
    StatSchedule,
)

DEPTH_SCALING_PATH = DATA_DIR / "depth_scaling.json"
DEPTH_SCALING_SCHEMA_VERSION = 1
DEPTH_SCALING_FILENAME = "depth_scaling.json"

_ZERO_SCHEDULE = StatSchedule()


class DepthScalingLoadError(ValueError):
    pass


def load_depth_scaling_config(
    path: Path | None = None,
    *,
    mods_root: Path | None = None,
    report_mod_errors: bool = True,
) -> DepthScalingConfig:
    """Load depth scaling; default path layers whole-file mod replaces."""
    if path is not None:
        if mods_root is not None:
            raise TypeError("mods_root is only valid when path is None (layered load)")
        with path.open(encoding="utf-8") as handle:
            raw = json.load(handle)
        if not isinstance(raw, dict):
            raise DepthScalingLoadError("depth_scaling file must be a JSON object")
        return parse_depth_scaling_config(raw)

    from src.mods.pipeline import load_depth_scaling_layered

    config, _issues = load_depth_scaling_layered(
        mods_root=mods_root,
        report=report_mod_errors,
    )
    return config


@lru_cache(maxsize=1)
def default_depth_scaling_config() -> DepthScalingConfig:
    return load_depth_scaling_config()


def reset_depth_scaling_cache() -> None:
    default_depth_scaling_config.cache_clear()


def parse_depth_scaling_config(raw: dict[str, Any]) -> DepthScalingConfig:
    schema_version = _require_int(raw, "schema_version", context="depth_scaling file")
    if schema_version != DEPTH_SCALING_SCHEMA_VERSION:
        raise DepthScalingLoadError(
            f"depth_scaling file: unsupported schema_version {schema_version}"
        )

    default_id = raw.get("default_difficulty_id")
    if not isinstance(default_id, str) or not default_id:
        raise DepthScalingLoadError(
            "depth_scaling file: 'default_difficulty_id' must be a non-empty string"
        )

    difficulties_raw = raw.get("difficulties")
    if not isinstance(difficulties_raw, dict) or not difficulties_raw:
        raise DepthScalingLoadError(
            "depth_scaling file: 'difficulties' must be a non-empty object"
        )

    difficulties: dict[str, DifficultyProfile] = {}
    for difficulty_id, entry in difficulties_raw.items():
        if not isinstance(difficulty_id, str) or not difficulty_id:
            raise DepthScalingLoadError(
                "depth_scaling file: difficulty ids must be non-empty strings"
            )
        if not isinstance(entry, dict):
            raise DepthScalingLoadError(
                f"difficulties.{difficulty_id}: must be an object"
            )
        difficulties[difficulty_id] = _parse_difficulty_profile(
            difficulty_id, entry
        )

    if default_id not in difficulties:
        raise DepthScalingLoadError(
            f"depth_scaling file: default_difficulty_id '{default_id}' "
            "is not present in difficulties"
        )

    for key in raw:
        if key in {"schema_version", "default_difficulty_id", "difficulties"}:
            continue
        raise DepthScalingLoadError(
            f"depth_scaling file: unknown top-level field '{key}'"
        )

    return DepthScalingConfig(
        schema_version=schema_version,
        default_difficulty_id=default_id,
        difficulties=difficulties,
    )


def _parse_difficulty_profile(
    difficulty_id: str, entry: dict[str, Any]
) -> DifficultyProfile:
    context = f"difficulties.{difficulty_id}"
    display_name = entry.get("display_name")
    if not isinstance(display_name, str) or not display_name:
        raise DepthScalingLoadError(
            f"{context}: 'display_name' must be a non-empty string"
        )

    alignments_raw = entry.get("apply_to_alignments")
    if not isinstance(alignments_raw, list) or not alignments_raw:
        raise DepthScalingLoadError(
            f"{context}: 'apply_to_alignments' must be a non-empty array"
        )
    alignments: set[Alignment] = set()
    for index, name in enumerate(alignments_raw):
        if not isinstance(name, str):
            raise DepthScalingLoadError(
                f"{context}: apply_to_alignments[{index}] must be a string"
            )
        alignment = ALIGNMENT_BY_NAME.get(name.lower())
        if alignment is None:
            raise DepthScalingLoadError(
                f"{context}: unknown alignment '{name}' "
                f"(expected one of {sorted(ALIGNMENT_BY_NAME)})"
            )
        alignments.add(alignment)

    stats_raw = entry.get("stats", {})
    if stats_raw is None:
        stats_raw = {}
    if not isinstance(stats_raw, dict):
        raise DepthScalingLoadError(f"{context}: 'stats' must be an object")

    stats: dict[str, StatSchedule] = {}
    for stat_key, schedule_raw in stats_raw.items():
        if stat_key not in ALL_STAT_KEYS:
            raise DepthScalingLoadError(
                f"{context}.stats: unknown stat '{stat_key}' "
                f"(allowed: {sorted(ALL_STAT_KEYS)})"
            )
        if not isinstance(schedule_raw, dict):
            raise DepthScalingLoadError(
                f"{context}.stats.{stat_key}: must be an object"
            )
        stats[stat_key] = _parse_stat_schedule(
            schedule_raw,
            context=f"{context}.stats.{stat_key}",
            is_float_stat=stat_key in FLOAT_STAT_KEYS,
            default_unit=0.01 if stat_key == "accuracy" else 1.0,
        )

    # Allowed extra keys reserved for later PRs (parsed lightly or rejected).
    # PR1: reject unknown so typos fail fast; PR1b may expand whitelist.
    allowed = {
        "display_name",
        "apply_to_alignments",
        "stats",
        "density_multiplier",
        "runes_per_floor_override",
        "rune_pieces_multiplier",
        "prefix_spawn",
        "spawn_ai_freeze",
    }
    for key in entry:
        if key not in allowed:
            raise DepthScalingLoadError(f"{context}: unknown field '{key}'")

    density_multiplier = 1.0
    if "density_multiplier" in entry:
        dens = entry["density_multiplier"]
        if not isinstance(dens, (int, float)) or isinstance(dens, bool) or dens < 0:
            raise DepthScalingLoadError(
                f"{context}: 'density_multiplier' must be a number >= 0"
            )
        density_multiplier = float(dens)

    runes_override: int | None = None
    if "runes_per_floor_override" in entry:
        rpf = entry["runes_per_floor_override"]
        if rpf is not None and (
            isinstance(rpf, bool) or not isinstance(rpf, int) or rpf < 0
        ):
            raise DepthScalingLoadError(
                f"{context}: 'runes_per_floor_override' must be int >= 0 or null"
            )
        runes_override = rpf

    pieces_mult = 1
    if "rune_pieces_multiplier" in entry:
        rpm = entry["rune_pieces_multiplier"]
        if not isinstance(rpm, int) or isinstance(rpm, bool) or rpm < 1:
            raise DepthScalingLoadError(
                f"{context}: 'rune_pieces_multiplier' must be an integer >= 1"
            )
        pieces_mult = rpm

    prefix_spawn = PrefixSpawnConfig()
    if "prefix_spawn" in entry and entry["prefix_spawn"] is not None:
        if not isinstance(entry["prefix_spawn"], dict):
            raise DepthScalingLoadError(f"{context}: 'prefix_spawn' must be an object")
        prefix_spawn = _parse_prefix_spawn(
            entry["prefix_spawn"], context=f"{context}.prefix_spawn"
        )

    spawn_ai_freeze = SpawnAiFreezeConfig()
    if "spawn_ai_freeze" in entry and entry["spawn_ai_freeze"] is not None:
        if not isinstance(entry["spawn_ai_freeze"], dict):
            raise DepthScalingLoadError(f"{context}: 'spawn_ai_freeze' must be an object")
        spawn_ai_freeze = _parse_spawn_ai_freeze(
            entry["spawn_ai_freeze"], context=f"{context}.spawn_ai_freeze"
        )

    return DifficultyProfile(
        id=difficulty_id,
        display_name=display_name,
        apply_to_alignments=frozenset(alignments),
        stats=stats,
        density_multiplier=density_multiplier,
        runes_per_floor_override=runes_override,
        rune_pieces_multiplier=pieces_mult,
        prefix_spawn=prefix_spawn,
        spawn_ai_freeze=spawn_ai_freeze,
    )


def _parse_spawn_ai_freeze(raw: dict[str, Any], *, context: str) -> SpawnAiFreezeConfig:
    enabled = raw.get("enabled", True)
    if not isinstance(enabled, bool):
        raise DepthScalingLoadError(f"{context}: 'enabled' must be a boolean")
    turns_per = _optional_int(raw, "turns_per_chebyshev", context=context, default=2)
    offset = _optional_int(raw, "distance_offset", context=context, default=6)
    max_turns = _optional_int(raw, "max_turns", context=context, default=48)
    proximity = _optional_int(raw, "proximity_unfreeze", context=context, default=8)
    if turns_per < 0 or offset < 0 or max_turns < 0 or proximity < 0:
        raise DepthScalingLoadError(f"{context}: numeric fields must be >= 0")
    for key in raw:
        if key in {
            "enabled",
            "turns_per_chebyshev",
            "distance_offset",
            "max_turns",
            "proximity_unfreeze",
        }:
            continue
        raise DepthScalingLoadError(f"{context}: unknown field '{key}'")
    return SpawnAiFreezeConfig(
        enabled=enabled,
        turns_per_chebyshev=turns_per,
        distance_offset=offset,
        max_turns=max_turns,
        proximity_unfreeze=proximity,
    )


def _parse_prefix_spawn(raw: dict[str, Any], *, context: str) -> PrefixSpawnConfig:
    base = _optional_int(raw, "base_chance_pct", context=context, default=0)
    per_step = _optional_int(
        raw, "chance_pct_per_depth_step", context=context, default=0
    )
    max_pct = _optional_int(raw, "max_chance_pct", context=context, default=100)
    start = _optional_int(raw, "start_depth", context=context, default=1)
    if base < 0 or per_step < 0:
        raise DepthScalingLoadError(
            f"{context}: chance fields must be >= 0"
        )
    if max_pct < 0:
        raise DepthScalingLoadError(f"{context}: 'max_chance_pct' must be >= 0")
    if start < 1:
        raise DepthScalingLoadError(f"{context}: 'start_depth' must be >= 1")
    for key in raw:
        if key in {
            "base_chance_pct",
            "chance_pct_per_depth_step",
            "max_chance_pct",
            "start_depth",
        }:
            continue
        raise DepthScalingLoadError(f"{context}: unknown field '{key}'")
    return PrefixSpawnConfig(
        base_chance_pct=base,
        chance_pct_per_depth_step=per_step,
        max_chance_pct=max_pct,
        start_depth=start,
    )


def _parse_stat_schedule(
    raw: dict[str, Any],
    *,
    context: str,
    is_float_stat: bool,
    default_unit: float = 1.0,
) -> StatSchedule:
    per_floor = _optional_int(raw, "per_floor", context=context, default=0)
    every_n = _optional_int(raw, "every_n_floors", context=context, default=0)
    bank_amount = _optional_int(raw, "bank_amount", context=context, default=1)
    start_depth = _optional_int(raw, "start_depth", context=context, default=1)

    if every_n < 0:
        raise DepthScalingLoadError(f"{context}: 'every_n_floors' must be >= 0")
    if start_depth < 1:
        raise DepthScalingLoadError(f"{context}: 'start_depth' must be >= 1")

    unit = 1.0
    if is_float_stat:
        unit_raw = raw.get("unit", default_unit)
        if not isinstance(unit_raw, (int, float)) or isinstance(unit_raw, bool):
            raise DepthScalingLoadError(f"{context}: 'unit' must be a number")
        unit = float(unit_raw)
    elif "unit" in raw:
        raise DepthScalingLoadError(
            f"{context}: 'unit' is only valid for float stat schedules "
            f"(accuracy, evade)"
        )

    for key in raw:
        if key in {
            "per_floor",
            "every_n_floors",
            "bank_amount",
            "start_depth",
            "unit",
        }:
            continue
        raise DepthScalingLoadError(f"{context}: unknown field '{key}'")

    return StatSchedule(
        per_floor=per_floor,
        every_n_floors=every_n,
        bank_amount=bank_amount,
        start_depth=start_depth,
        unit=unit,
    )


def _optional_int(
    raw: dict[str, Any],
    key: str,
    *,
    context: str,
    default: int,
) -> int:
    if key not in raw:
        return default
    value = raw[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise DepthScalingLoadError(f"{context}: '{key}' must be an integer")
    return value


def _require_int(raw: dict[str, Any], key: str, *, context: str) -> int:
    value = raw.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise DepthScalingLoadError(f"{context}: '{key}' must be an integer")
    return value
