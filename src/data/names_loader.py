from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.constants import DATA_DIR
from src.data.names_registry import NamesRegistry

NAMES_PATH = DATA_DIR / "names.json"
NAMES_SCHEMA_VERSION = 1

_names_registry: NamesRegistry | None = None


class NamesLoadError(ValueError):
    pass


def load_names_registry(
    path: Path | None = None,
    *,
    mods_root: Path | None = None,
    report_mod_errors: bool = True,
) -> NamesRegistry:
    """Load name pools; default path layers enabled mods (later entity id wins)."""
    if path is not None:
        if mods_root is not None:
            raise TypeError("mods_root is only valid when path is None (layered load)")
        with path.open(encoding="utf-8") as handle:
            raw = json.load(handle)
        return parse_names_registry(raw)

    from src.mods.pipeline import load_names_layered

    registry, _issues = load_names_layered(
        mods_root=mods_root,
        report=report_mod_errors,
    )
    return registry


def parse_names_registry(raw: dict[str, Any]) -> NamesRegistry:
    schema_version = _require_int(raw, "schema_version", context="names file")
    if schema_version != NAMES_SCHEMA_VERSION:
        raise NamesLoadError(f"names file: unsupported schema_version {schema_version}")

    names_raw = raw.get("names")
    if not isinstance(names_raw, dict):
        raise NamesLoadError("names file: 'names' must be an object")

    parsed: dict[str, tuple[str, ...]] = {}
    for entity_id, pool in names_raw.items():
        if not isinstance(entity_id, str) or not entity_id:
            raise NamesLoadError("names file: entity id keys must be non-empty strings")
        if not isinstance(pool, list) or not pool:
            raise NamesLoadError(
                f"names file: names['{entity_id}'] must be a non-empty string array"
            )
        if not all(isinstance(name, str) and name for name in pool):
            raise NamesLoadError(
                f"names file: names['{entity_id}'] must contain non-empty strings"
            )
        parsed[entity_id] = tuple(pool)

    for key in raw:
        if key in {"schema_version", "names"}:
            continue
        raise NamesLoadError(f"names file: unknown top-level field '{key}'")

    return NamesRegistry(schema_version=schema_version, names=parsed)


def get_names_registry() -> NamesRegistry:
    """Cached names registry (core + enabled mods)."""
    global _names_registry
    if _names_registry is None:
        _names_registry = load_names_registry()
    return _names_registry


def reset_names_registry() -> None:
    """Clear cached registry (tests or hot-reload)."""
    global _names_registry
    _names_registry = None


def _require_int(raw: dict[str, Any], key: str, *, context: str) -> int:
    value = raw.get(key)
    if not isinstance(value, int):
        raise NamesLoadError(f"{context}: '{key}' must be an integer")
    return value