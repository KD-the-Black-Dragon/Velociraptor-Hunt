from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.constants import DATA_DIR
from src.data.dungeon_spawn_config import (
    DensityDefaults,
    DepthBand,
    DungeonSpawnConfig,
)

DUNGEON_SPAWN_PATH = DATA_DIR / "dungeon_spawn.json"
DUNGEON_SPAWN_SCHEMA_VERSION = 1

_DENSITY_FIELDS = frozenset({"density_pct", "density_variance", "min_npcs", "max_npcs"})


class DungeonSpawnLoadError(ValueError):
    pass


def load_dungeon_spawn_config(
    path: Path | None = None,
    *,
    mods_root: Path | None = None,
    report_mod_errors: bool = True,
) -> DungeonSpawnConfig:
    """Load dungeon density config; default path layers whole-file mod replaces."""
    if path is not None:
        if mods_root is not None:
            raise TypeError("mods_root is only valid when path is None (layered load)")
        with path.open(encoding="utf-8") as handle:
            raw = json.load(handle)
        return parse_dungeon_spawn_config(raw)

    from src.mods.pipeline import load_dungeon_spawn_layered

    config, _issues = load_dungeon_spawn_layered(
        mods_root=mods_root,
        report=report_mod_errors,
    )
    return config


def parse_dungeon_spawn_config(raw: dict[str, Any]) -> DungeonSpawnConfig:
    schema_version = _require_int(raw, "schema_version", context="dungeon_spawn file")
    if schema_version != DUNGEON_SPAWN_SCHEMA_VERSION:
        raise DungeonSpawnLoadError(
            f"dungeon_spawn file: unsupported schema_version {schema_version}"
        )

    defaults_raw = raw.get("defaults")
    if not isinstance(defaults_raw, dict):
        raise DungeonSpawnLoadError("dungeon_spawn file: 'defaults' must be an object")
    defaults = _parse_density_fields(defaults_raw, context="defaults")

    bands_raw = raw.get("depth_bands")
    if not isinstance(bands_raw, list):
        raise DungeonSpawnLoadError("dungeon_spawn file: 'depth_bands' must be an array")

    depth_bands: list[DepthBand] = []
    for index, entry in enumerate(bands_raw):
        if not isinstance(entry, dict):
            raise DungeonSpawnLoadError(f"depth_bands[{index}] must be an object")
        depth_bands.append(_parse_depth_band(entry, defaults=defaults, index=index))

    _validate_non_overlapping_bands(depth_bands)

    for key in raw:
        if key in {"schema_version", "defaults", "depth_bands"}:
            continue
        raise DungeonSpawnLoadError(f"dungeon_spawn file: unknown top-level field '{key}'")

    return DungeonSpawnConfig(
        schema_version=schema_version,
        defaults=defaults,
        depth_bands=tuple(depth_bands),
    )


def _parse_depth_band(
    entry: dict[str, Any],
    *,
    defaults: DensityDefaults,
    index: int,
) -> DepthBand:
    context = f"depth_bands[{index}]"
    min_depth = _require_int(entry, "min_depth", context=context)
    max_depth = _require_int(entry, "max_depth", context=context)
    if min_depth > max_depth:
        raise DungeonSpawnLoadError(f"{context}: min_depth must be <= max_depth")

    merged = {
        "density_pct": defaults.density_pct,
        "density_variance": defaults.density_variance,
        "min_npcs": defaults.min_npcs,
        "max_npcs": defaults.max_npcs,
    }
    for field in _DENSITY_FIELDS:
        if field in entry:
            merged[field] = entry[field]

    density = _parse_density_fields(merged, context=context)
    return DepthBand(
        min_depth=min_depth,
        max_depth=max_depth,
        density_pct=density.density_pct,
        density_variance=density.density_variance,
        min_npcs=density.min_npcs,
        max_npcs=density.max_npcs,
    )


def _parse_density_fields(
    raw: dict[str, Any],
    *,
    context: str,
) -> DensityDefaults:
    density_pct = raw.get("density_pct")
    density_variance = raw.get("density_variance")
    min_npcs = raw.get("min_npcs")
    max_npcs = raw.get("max_npcs", ...)

    if density_pct is None:
        raise DungeonSpawnLoadError(f"{context}: 'density_pct' is required")
    if not isinstance(density_pct, (int, float)):
        raise DungeonSpawnLoadError(f"{context}: 'density_pct' must be a number")
    if density_pct < 0:
        raise DungeonSpawnLoadError(f"{context}: 'density_pct' must be >= 0")

    if density_variance is None:
        raise DungeonSpawnLoadError(f"{context}: 'density_variance' is required")
    if not isinstance(density_variance, (int, float)):
        raise DungeonSpawnLoadError(f"{context}: 'density_variance' must be a number")
    if not 0 <= density_variance < 1:
        raise DungeonSpawnLoadError(f"{context}: 'density_variance' must be in [0, 1)")

    if min_npcs is None:
        raise DungeonSpawnLoadError(f"{context}: 'min_npcs' is required")
    if not isinstance(min_npcs, int):
        raise DungeonSpawnLoadError(f"{context}: 'min_npcs' must be an integer")
    if min_npcs < 0:
        raise DungeonSpawnLoadError(f"{context}: 'min_npcs' must be >= 0")

    parsed_max: int | None
    if max_npcs is ...:
        parsed_max = None
    elif max_npcs is None:
        parsed_max = None
    elif not isinstance(max_npcs, int):
        raise DungeonSpawnLoadError(f"{context}: 'max_npcs' must be an integer or null")
    else:
        parsed_max = max_npcs

    if parsed_max is not None and parsed_max < min_npcs:
        raise DungeonSpawnLoadError(f"{context}: 'max_npcs' must be >= min_npcs")

    return DensityDefaults(
        density_pct=float(density_pct),
        density_variance=float(density_variance),
        min_npcs=min_npcs,
        max_npcs=parsed_max,
    )


def _validate_non_overlapping_bands(bands: list[DepthBand]) -> None:
    for left_index, left in enumerate(bands):
        for right in bands[left_index + 1 :]:
            if left.min_depth <= right.max_depth and right.min_depth <= left.max_depth:
                raise DungeonSpawnLoadError(
                    "depth_bands: bands "
                    f"[{left.min_depth},{left.max_depth}] and "
                    f"[{right.min_depth},{right.max_depth}] overlap"
                )


def _require_int(raw: dict[str, Any], key: str, *, context: str) -> int:
    value = raw.get(key)
    if not isinstance(value, int):
        raise DungeonSpawnLoadError(f"{context}: '{key}' must be an integer")
    return value