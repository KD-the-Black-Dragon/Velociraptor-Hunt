"""Loader for depth-jump start tuning (`data/depth_jump_start.json`)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import attrs

from src.constants import DATA_DIR

DEPTH_JUMP_START_PATH = DATA_DIR / "depth_jump_start.json"


class DepthJumpStartLoadError(ValueError):
    """Invalid depth-jump start configuration."""


@attrs.define(frozen=True)
class DepthJumpStartConfig:
    schema_version: int
    max_target_depth: int
    throwable_stack_count: int
    potion_count: int
    wand_count: int
    simulated_runes_min_numerator: int
    simulated_runes_min_denominator: int


def _require_int(raw: dict[str, Any], key: str, *, context: str) -> int:
    value = raw.get(key)
    if not isinstance(value, int):
        raise DepthJumpStartLoadError(f"{context}: '{key}' must be an integer")
    return value


def parse_depth_jump_start_config(raw: dict[str, Any]) -> DepthJumpStartConfig:
    schema_version = _require_int(raw, "schema_version", context="depth_jump_start file")
    if schema_version != 1:
        raise DepthJumpStartLoadError(
            f"depth_jump_start file: unsupported schema_version {schema_version}"
        )

    max_target_depth = _require_int(raw, "max_target_depth", context="depth_jump_start file")
    if max_target_depth < 1:
        raise DepthJumpStartLoadError(
            "depth_jump_start file: 'max_target_depth' must be >= 1"
        )

    throwable_stack_count = _require_int(
        raw, "throwable_stack_count", context="depth_jump_start file"
    )
    potion_count = _require_int(raw, "potion_count", context="depth_jump_start file")
    wand_count = _require_int(raw, "wand_count", context="depth_jump_start file")
    for label, value in (
        ("throwable_stack_count", throwable_stack_count),
        ("potion_count", potion_count),
        ("wand_count", wand_count),
    ):
        if value < 0:
            raise DepthJumpStartLoadError(
                f"depth_jump_start file: '{label}' must be >= 0"
            )

    numerator = _require_int(
        raw, "simulated_runes_min_numerator", context="depth_jump_start file"
    )
    denominator = _require_int(
        raw, "simulated_runes_min_denominator", context="depth_jump_start file"
    )
    if numerator < 0:
        raise DepthJumpStartLoadError(
            "depth_jump_start file: 'simulated_runes_min_numerator' must be >= 0"
        )
    if denominator < 1:
        raise DepthJumpStartLoadError(
            "depth_jump_start file: 'simulated_runes_min_denominator' must be >= 1"
        )

    known = {
        "schema_version",
        "max_target_depth",
        "throwable_stack_count",
        "potion_count",
        "wand_count",
        "simulated_runes_min_numerator",
        "simulated_runes_min_denominator",
    }
    for key in raw:
        if key not in known:
            raise DepthJumpStartLoadError(
                f"depth_jump_start file: unknown top-level field '{key}'"
            )

    return DepthJumpStartConfig(
        schema_version=schema_version,
        max_target_depth=max_target_depth,
        throwable_stack_count=throwable_stack_count,
        potion_count=potion_count,
        wand_count=wand_count,
        simulated_runes_min_numerator=numerator,
        simulated_runes_min_denominator=denominator,
    )


def load_depth_jump_start_config(
    path: Path | None = None,
) -> DepthJumpStartConfig:
    config_path = path if path is not None else DEPTH_JUMP_START_PATH
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise DepthJumpStartLoadError(f"could not read {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise DepthJumpStartLoadError(f"invalid JSON in {config_path}") from exc
    if not isinstance(raw, dict):
        raise DepthJumpStartLoadError("depth_jump_start file: root must be an object")
    return parse_depth_jump_start_config(raw)


@lru_cache(maxsize=1)
def default_depth_jump_start_config() -> DepthJumpStartConfig:
    return load_depth_jump_start_config()


def reset_depth_jump_start_config_cache() -> None:
    default_depth_jump_start_config.cache_clear()