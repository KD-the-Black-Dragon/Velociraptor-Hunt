from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.constants import DATA_DIR, RUNES_PER_FLOOR
from src.data.floor_rune_registry import FloorRuneDefinition, FloorRuneRegistry, RuneEffect

FLOOR_RUNES_PATH = DATA_DIR / "floor_runes.json"
FLOOR_RUNES_SCHEMA_VERSION = 1
_FORBIDDEN_GLYPHS = frozenset({"#"})


class FloorRuneLoadError(ValueError):
    pass


def load_floor_rune_registry(
    path: Path | None = None,
    *,
    mods_root: Path | None = None,
    report_mod_errors: bool = True,
) -> FloorRuneRegistry:
    """Load floor runes; default path layers enabled mods (later id wins)."""
    if path is not None:
        if mods_root is not None:
            raise TypeError("mods_root is only valid when path is None (layered load)")
        with path.open(encoding="utf-8") as handle:
            raw = json.load(handle)
        return parse_floor_rune_registry(raw)

    from src.mods.pipeline import load_floor_runes_layered

    registry, _issues = load_floor_runes_layered(
        mods_root=mods_root,
        report=report_mod_errors,
    )
    return registry


def parse_floor_rune_registry(raw: dict[str, Any]) -> FloorRuneRegistry:
    schema_version = _require_int(raw, "schema_version", context="floor_runes file")
    if schema_version != FLOOR_RUNES_SCHEMA_VERSION:
        raise FloorRuneLoadError(
            f"floor_runes file: unsupported schema_version {schema_version}"
        )

    runes_raw = raw.get("runes")
    if not isinstance(runes_raw, list):
        raise FloorRuneLoadError("floor_runes file: 'runes' must be an array")

    runes: list[FloorRuneDefinition] = []
    seen_ids: set[str] = set()
    for index, entry in enumerate(runes_raw):
        if not isinstance(entry, dict):
            raise FloorRuneLoadError(f"runes[{index}] must be an object")
        rune = _parse_rune(entry, index=index)
        if rune.id in seen_ids:
            raise FloorRuneLoadError(f"duplicate rune id '{rune.id}'")
        seen_ids.add(rune.id)
        runes.append(rune)

    runes_per_floor = RUNES_PER_FLOOR
    if "runes_per_floor" in raw:
        rpf = raw["runes_per_floor"]
        if isinstance(rpf, bool) or not isinstance(rpf, int) or rpf < 0:
            raise FloorRuneLoadError(
                "floor_runes file: 'runes_per_floor' must be an integer >= 0"
            )
        runes_per_floor = rpf

    for key in raw:
        if key in {"schema_version", "runes", "runes_per_floor"}:
            continue
        raise FloorRuneLoadError(f"floor_runes file: unknown top-level field '{key}'")

    return FloorRuneRegistry(
        schema_version=schema_version,
        runes=tuple(runes),
        runes_per_floor=runes_per_floor,
    )


def _parse_rune(entry: dict[str, Any], *, index: int) -> FloorRuneDefinition:
    context = f"runes[{index}]"
    rune_id = _require_str(entry, "id", context=context)
    glyph = _require_str(entry, "glyph", context=context)
    if len(glyph) != 1:
        raise FloorRuneLoadError(f"{context}: 'glyph' must be exactly one character")
    if glyph in _FORBIDDEN_GLYPHS:
        raise FloorRuneLoadError(f"{context}: glyph '{glyph}' is reserved for walls")

    min_depth = _require_int(entry, "min_depth", context=context)
    max_depth = _require_int(entry, "max_depth", context=context)
    if min_depth > max_depth:
        raise FloorRuneLoadError(f"{context}: min_depth must be <= max_depth")

    weight = entry.get("weight")
    if not isinstance(weight, int) or weight <= 0:
        raise FloorRuneLoadError(f"{context}: 'weight' must be a positive integer")

    effect_raw = entry.get("effect")
    if not isinstance(effect_raw, dict):
        raise FloorRuneLoadError(f"{context}: 'effect' must be an object")

    return FloorRuneDefinition(
        id=rune_id,
        display_name=_require_str(entry, "display_name", context=context),
        glyph=glyph,
        fg=_parse_fg(entry.get("fg"), context=context),
        examine=_require_str(entry, "examine", context=context),
        weight=weight,
        min_depth=min_depth,
        max_depth=max_depth,
        effect=_parse_effect(effect_raw, context=f"{context}.effect"),
    )


def _parse_pieces_fields(raw: dict[str, Any], *, context: str) -> tuple[int, int]:
    pieces_per = raw.get("pieces_per_bonus", 1)
    pieces_granted = raw.get("pieces_granted", 1)
    if isinstance(pieces_per, bool) or not isinstance(pieces_per, int) or pieces_per < 1:
        raise FloorRuneLoadError(
            f"{context}: 'pieces_per_bonus' must be an integer >= 1"
        )
    if (
        isinstance(pieces_granted, bool)
        or not isinstance(pieces_granted, int)
        or pieces_granted < 1
    ):
        raise FloorRuneLoadError(
            f"{context}: 'pieces_granted' must be an integer >= 1"
        )
    return pieces_per, pieces_granted


def _parse_effect(raw: dict[str, Any], *, context: str) -> RuneEffect:
    effect_type = raw.get("type")
    if not isinstance(effect_type, str) or not effect_type:
        raise FloorRuneLoadError(f"{context}: 'type' must be a non-empty string")

    pieces_per, pieces_granted = _parse_pieces_fields(raw, context=context)

    match effect_type:
        case "max_hp" | "accuracy" | "natural_ac" | "natural_evade":
            amount = raw.get("amount")
            if not isinstance(amount, (int, float)):
                raise FloorRuneLoadError(f"{context}: 'amount' must be a number")
            return RuneEffect(
                type=effect_type,
                amount=amount,
                pieces_per_bonus=pieces_per,
                pieces_granted=pieces_granted,
            )
        case "accuracy_damage":
            accuracy = raw.get("accuracy")
            min_damage = raw.get("min_damage")
            max_damage = raw.get("max_damage")
            if not isinstance(accuracy, (int, float)):
                raise FloorRuneLoadError(f"{context}: 'accuracy' must be a number")
            if not isinstance(min_damage, int) or not isinstance(max_damage, int):
                raise FloorRuneLoadError(
                    f"{context}: 'min_damage' and 'max_damage' must be integers"
                )
            return RuneEffect(
                type=effect_type,
                accuracy=float(accuracy),
                min_damage=min_damage,
                max_damage=max_damage,
                pieces_per_bonus=pieces_per,
                pieces_granted=pieces_granted,
            )
        case _:
            raise FloorRuneLoadError(f"{context}: unsupported effect type '{effect_type}'")


def _parse_fg(raw: object, *, context: str) -> tuple[int, int, int]:
    if not isinstance(raw, list) or len(raw) != 3:
        raise FloorRuneLoadError(f"{context}: 'fg' must be [r, g, b]")
    try:
        return (int(raw[0]), int(raw[1]), int(raw[2]))
    except (TypeError, ValueError) as exc:
        raise FloorRuneLoadError(f"{context}: 'fg' values must be integers") from exc


def _require_str(raw: dict[str, Any], key: str, *, context: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise FloorRuneLoadError(f"{context}: '{key}' must be a non-empty string")
    return value


def _require_int(raw: dict[str, Any], key: str, *, context: str) -> int:
    value = raw.get(key)
    if not isinstance(value, int):
        raise FloorRuneLoadError(f"{context}: '{key}' must be an integer")
    return value