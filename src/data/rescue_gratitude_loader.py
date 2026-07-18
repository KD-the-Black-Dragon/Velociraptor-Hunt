from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.constants import DATA_DIR
from src.data.rescue_gratitude_registry import RescueGratitudeRegistry

RESCUE_GRATITUDE_PATH = DATA_DIR / "rescue_gratitude.json"
RESCUE_GRATITUDE_SCHEMA_VERSION = 1

_rescue_gratitude_registry: RescueGratitudeRegistry | None = None


class RescueGratitudeLoadError(ValueError):
    pass


def load_rescue_gratitude_registry(
    path: Path | None = None,
    *,
    mods_root: Path | None = None,
    report_mod_errors: bool = True,
) -> RescueGratitudeRegistry:
    """Load rescue lines; default path layers whole-file mod replaces."""
    if path is not None:
        if mods_root is not None:
            raise TypeError("mods_root is only valid when path is None (layered load)")
        with path.open(encoding="utf-8") as handle:
            raw = json.load(handle)
        return parse_rescue_gratitude_registry(raw)

    from src.mods.pipeline import load_rescue_gratitude_layered

    registry, _issues = load_rescue_gratitude_layered(
        mods_root=mods_root,
        report=report_mod_errors,
    )
    return registry


def parse_rescue_gratitude_registry(raw: dict[str, Any]) -> RescueGratitudeRegistry:
    schema_version = _require_int(raw, "schema_version", context="rescue_gratitude file")
    if schema_version != RESCUE_GRATITUDE_SCHEMA_VERSION:
        raise RescueGratitudeLoadError(
            f"rescue_gratitude file: unsupported schema_version {schema_version}"
        )

    lines_raw = raw.get("lines")
    if not isinstance(lines_raw, list) or not lines_raw:
        raise RescueGratitudeLoadError(
            "rescue_gratitude file: 'lines' must be a non-empty string array"
        )
    if not all(isinstance(line, str) and line for line in lines_raw):
        raise RescueGratitudeLoadError(
            "rescue_gratitude file: 'lines' must contain non-empty strings"
        )

    for key in raw:
        if key in {"schema_version", "lines"}:
            continue
        raise RescueGratitudeLoadError(
            f"rescue_gratitude file: unknown top-level field '{key}'"
        )

    return RescueGratitudeRegistry(
        schema_version=schema_version,
        lines=tuple(lines_raw),
    )


def get_rescue_gratitude_registry() -> RescueGratitudeRegistry:
    global _rescue_gratitude_registry
    if _rescue_gratitude_registry is None:
        _rescue_gratitude_registry = load_rescue_gratitude_registry()
    return _rescue_gratitude_registry


def reset_rescue_gratitude_registry() -> None:
    """Clear cached registry (tests or hot-reload)."""
    global _rescue_gratitude_registry
    _rescue_gratitude_registry = None


def _require_int(raw: dict[str, Any], key: str, *, context: str) -> int:
    value = raw.get(key)
    if not isinstance(value, int):
        raise RescueGratitudeLoadError(f"{context}: '{key}' must be an integer")
    return value