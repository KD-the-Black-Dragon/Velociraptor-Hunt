from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.constants import DATA_DIR
from src.data.macguffin_registry import MacguffinDefinition, MacguffinRegistry

MACGUFFINS_PATH = DATA_DIR / "macguffins.json"
MACGUFFINS_SCHEMA_VERSION = 1
_FORBIDDEN_GLYPHS = frozenset({"#"})


class MacguffinLoadError(ValueError):
    pass


def load_macguffin_registry(
    path: Path | None = None,
    *,
    mods_root: Path | None = None,
    report_mod_errors: bool = True,
) -> MacguffinRegistry:
    """Load macguffins; default path layers enabled mods (later id wins)."""
    if path is not None:
        if mods_root is not None:
            raise TypeError("mods_root is only valid when path is None (layered load)")
        with path.open(encoding="utf-8") as handle:
            raw = json.load(handle)
        return parse_macguffin_registry(raw)

    from src.mods.pipeline import load_macguffins_layered

    registry, _issues = load_macguffins_layered(
        mods_root=mods_root,
        report=report_mod_errors,
    )
    return registry


def parse_macguffin_registry(raw: dict[str, Any]) -> MacguffinRegistry:
    schema_version = _require_int(raw, "schema_version", context="macguffins file")
    if schema_version != MACGUFFINS_SCHEMA_VERSION:
        raise MacguffinLoadError(
            f"macguffins file: unsupported schema_version {schema_version}"
        )

    macguffins_raw = raw.get("macguffins")
    if not isinstance(macguffins_raw, list):
        raise MacguffinLoadError("macguffins file: 'macguffins' must be an array")

    macguffins: list[MacguffinDefinition] = []
    seen_ids: set[str] = set()
    for index, entry in enumerate(macguffins_raw):
        if not isinstance(entry, dict):
            raise MacguffinLoadError(f"macguffins[{index}] must be an object")
        macguffin = _parse_macguffin(entry, index=index)
        if macguffin.id in seen_ids:
            raise MacguffinLoadError(f"duplicate macguffin id '{macguffin.id}'")
        seen_ids.add(macguffin.id)
        macguffins.append(macguffin)

    for key in raw:
        if key in {"schema_version", "macguffins"}:
            continue
        raise MacguffinLoadError(f"macguffins file: unknown top-level field '{key}'")

    return MacguffinRegistry(schema_version=schema_version, macguffins=tuple(macguffins))


def _parse_macguffin(entry: dict[str, Any], *, index: int) -> MacguffinDefinition:
    context = f"macguffins[{index}]"
    macguffin_id = _require_str(entry, "id", context=context)
    glyph = _require_str(entry, "glyph", context=context)
    if len(glyph) != 1:
        raise MacguffinLoadError(f"{context}: 'glyph' must be exactly one character")
    if glyph in _FORBIDDEN_GLYPHS:
        raise MacguffinLoadError(f"{context}: glyph '{glyph}' is reserved for walls")

    min_depth = _require_int(entry, "min_depth", context=context)
    max_depth = _require_int(entry, "max_depth", context=context)
    if min_depth > max_depth:
        raise MacguffinLoadError(f"{context}: min_depth must be <= max_depth")

    score = entry.get("score")
    if not isinstance(score, int) or score < 0:
        raise MacguffinLoadError(f"{context}: 'score' must be a non-negative integer")

    return MacguffinDefinition(
        id=macguffin_id,
        display_name=_require_str(entry, "display_name", context=context),
        glyph=glyph,
        fg=_parse_fg(entry.get("fg"), context=context),
        examine=_require_str(entry, "examine", context=context),
        min_depth=min_depth,
        max_depth=max_depth,
        score=score,
    )


def _parse_fg(raw: object, *, context: str) -> tuple[int, int, int]:
    if not isinstance(raw, list) or len(raw) != 3:
        raise MacguffinLoadError(f"{context}: 'fg' must be [r, g, b]")
    try:
        return (int(raw[0]), int(raw[1]), int(raw[2]))
    except (TypeError, ValueError) as exc:
        raise MacguffinLoadError(f"{context}: 'fg' values must be integers") from exc


def _require_str(raw: dict[str, Any], key: str, *, context: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise MacguffinLoadError(f"{context}: '{key}' must be a non-empty string")
    return value


def _require_int(raw: dict[str, Any], key: str, *, context: str) -> int:
    value = raw.get(key)
    if not isinstance(value, int):
        raise MacguffinLoadError(f"{context}: '{key}' must be an integer")
    return value