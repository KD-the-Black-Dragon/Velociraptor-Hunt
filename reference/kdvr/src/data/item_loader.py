from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.constants import DATA_DIR
from src.data.item_loaders import (
    ARMOR_PATH,
    POTIONS_PATH,
    THROWABLES_PATH,
    WANDS_PATH,
    WEAPONS_PATH,
    ItemLoadError,
    load_item_stub_file,
)
from src.data.item_registry import (
    ArmorDefinition,
    ItemRegistry,
    ItemSpawnConfig,
    PotionDefinition,
    ThrowableDefinition,
    WandDefinition,
    WeaponDefinition,
)
ITEMS_SCHEMA_VERSION = 1


def _parse_fg(raw: object, *, context: str) -> tuple[int, int, int]:
    if not isinstance(raw, list) or len(raw) != 3:
        raise ItemLoadError(f"{context}: fg must be [r, g, b]")
    try:
        return (int(raw[0]), int(raw[1]), int(raw[2]))
    except (TypeError, ValueError) as exc:
        raise ItemLoadError(f"{context}: fg values must be integers") from exc


def _parse_spawn(
    raw: object,
    *,
    context: str,
    default_spawn_min: int = 0,
) -> ItemSpawnConfig:
    if not isinstance(raw, dict):
        raise ItemLoadError(f"{context}: spawn fields required at top level")
    weight = raw.get("spawn_weight")
    min_depth = raw.get("spawn_min_depth")
    max_depth = raw.get("spawn_max_depth")
    spawn_min = raw.get("spawn_min", default_spawn_min)
    if not isinstance(weight, (int, float)):
        raise ItemLoadError(f"{context}: spawn_weight must be a number")
    # 0 = deprecated / never spawn (definition kept for old saves).
    if float(weight) < 0:
        raise ItemLoadError(f"{context}: spawn_weight must be >= 0 (0 means never spawn)")
    if not isinstance(min_depth, int) or not isinstance(max_depth, int):
        raise ItemLoadError(f"{context}: spawn_min_depth and spawn_max_depth must be integers")
    if not isinstance(spawn_min, int):
        raise ItemLoadError(f"{context}: spawn_min must be an integer")
    return ItemSpawnConfig(
        weight=float(weight),
        min_depth=min_depth,
        max_depth=max_depth,
        spawn_min=spawn_min,
    )


def _require_str(raw: dict[str, Any], key: str, *, context: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise ItemLoadError(f"{context}: '{key}' must be a non-empty string")
    return value


def _require_int(raw: dict[str, Any], key: str, *, context: str) -> int:
    value = raw.get(key)
    if not isinstance(value, int):
        raise ItemLoadError(f"{context}: '{key}' must be an integer")
    return value


def _require_number(raw: dict[str, Any], key: str, *, context: str) -> float:
    value = raw.get(key)
    if not isinstance(value, (int, float)):
        raise ItemLoadError(f"{context}: '{key}' must be a number")
    return float(value)


def _parse_weapon(entry: dict[str, Any], *, context: str) -> WeaponDefinition:
    return WeaponDefinition(
        id=_require_str(entry, "id", context=context),
        display_name=_require_str(entry, "display_name", context=context),
        glyph=_require_str(entry, "glyph", context=context),
        fg=_parse_fg(entry.get("fg"), context=context),
        examine=_require_str(entry, "examine", context=context),
        min_damage=_require_int(entry, "min_damage", context=context),
        max_damage=_require_int(entry, "max_damage", context=context),
        accuracy_bonus=_require_number(entry, "accuracy_bonus", context=context),
        durability_max=_require_int(entry, "durability_max", context=context),
        spawn=_parse_spawn(entry, context=context),
    )


def _parse_armor(entry: dict[str, Any], *, context: str) -> ArmorDefinition:
    evade_bonus = entry.get("evade_bonus", 0)
    if isinstance(evade_bonus, bool) or not isinstance(evade_bonus, (int, float)):
        raise ItemLoadError(f"{context}: evade_bonus must be a number")
    if evade_bonus < 0:
        raise ItemLoadError(f"{context}: evade_bonus must be >= 0")
    return ArmorDefinition(
        id=_require_str(entry, "id", context=context),
        display_name=_require_str(entry, "display_name", context=context),
        glyph=_require_str(entry, "glyph", context=context),
        fg=_parse_fg(entry.get("fg"), context=context),
        examine=_require_str(entry, "examine", context=context),
        ac_bonus=_require_int(entry, "ac_bonus", context=context),
        digestion_ac=_require_int(entry, "digestion_ac", context=context),
        durability_max=_require_int(entry, "durability_max", context=context),
        spawn=_parse_spawn(entry, context=context),
        evade_bonus=float(evade_bonus),
    )


# Instant/buff effects (PR2). Delayed/target/summon effects land in later PRs.
_POTION_EFFECTS_IMPLEMENTED: frozenset[str] = frozenset(
    {
        "heal",
        "magic_mapping",
        "haste",
        "might",
        "digestion_ward",
        "teleport_delay",
        "blink",
        "summon_ally",
    }
)


def _optional_int(
    raw: dict[str, Any],
    key: str,
    *,
    context: str,
    default: int = 0,
    minimum: int | None = None,
) -> int:
    if key not in raw or raw[key] is None:
        value = default
    else:
        value = raw[key]
        if not isinstance(value, int):
            raise ItemLoadError(f"{context}: '{key}' must be an integer")
    if minimum is not None and value < minimum:
        raise ItemLoadError(f"{context}: '{key}' must be >= {minimum}")
    return value


def _optional_number(
    raw: dict[str, Any],
    key: str,
    *,
    context: str,
    default: float = 0.0,
) -> float:
    if key not in raw or raw[key] is None:
        return default
    value = raw[key]
    if not isinstance(value, (int, float)):
        raise ItemLoadError(f"{context}: '{key}' must be a number")
    return float(value)


def _parse_potion(entry: dict[str, Any], *, context: str) -> PotionDefinition:
    effect = _require_str(entry, "effect", context=context)
    if effect not in _POTION_EFFECTS_IMPLEMENTED:
        raise ItemLoadError(f"{context}: unsupported potion effect '{effect}'")

    heal_amount = _optional_int(entry, "heal_amount", context=context, default=0)
    duration_turns = _optional_int(
        entry, "duration_turns", context=context, default=0, minimum=0
    )
    accuracy_bonus = _optional_number(entry, "accuracy_bonus", context=context)
    min_damage_bonus = _optional_int(
        entry, "min_damage_bonus", context=context, default=0, minimum=0
    )
    max_damage_bonus = _optional_int(
        entry, "max_damage_bonus", context=context, default=0, minimum=0
    )
    delay_min_turns = _optional_int(
        entry, "delay_min_turns", context=context, default=0, minimum=0
    )
    delay_max_turns = _optional_int(
        entry, "delay_max_turns", context=context, default=0, minimum=0
    )

    if effect == "heal" and heal_amount < 1:
        raise ItemLoadError(f"{context}: heal effect requires heal_amount >= 1")
    if effect in ("haste", "digestion_ward") and duration_turns < 1:
        raise ItemLoadError(f"{context}: {effect} requires duration_turns >= 1")
    if effect == "might":
        if duration_turns < 1:
            raise ItemLoadError(f"{context}: might requires duration_turns >= 1")
        if min_damage_bonus < 0 or max_damage_bonus < 0:
            raise ItemLoadError(f"{context}: might damage bonuses must be >= 0")
    if effect == "teleport_delay":
        if delay_min_turns < 1:
            delay_min_turns = 3
        if delay_max_turns < delay_min_turns:
            delay_max_turns = max(delay_min_turns, 5)

    return PotionDefinition(
        id=_require_str(entry, "id", context=context),
        display_name=_require_str(entry, "display_name", context=context),
        glyph=_require_str(entry, "glyph", context=context),
        fg=_parse_fg(entry.get("fg"), context=context),
        examine=_require_str(entry, "examine", context=context),
        effect=effect,
        spawn=_parse_spawn(entry, context=context, default_spawn_min=0),
        heal_amount=heal_amount,
        duration_turns=duration_turns,
        accuracy_bonus=accuracy_bonus,
        min_damage_bonus=min_damage_bonus,
        max_damage_bonus=max_damage_bonus,
        delay_min_turns=delay_min_turns,
        delay_max_turns=delay_max_turns,
    )


def _parse_throwable(entry: dict[str, Any], *, context: str) -> ThrowableDefinition:
    min_damage = _require_int(entry, "min_damage", context=context)
    max_damage = _require_int(entry, "max_damage", context=context)
    if min_damage > max_damage:
        raise ItemLoadError(
            f"{context}: min_damage ({min_damage}) cannot exceed max_damage ({max_damage})"
        )
    stack_min = entry.get("spawn_stack_min", 1)
    stack_max = entry.get("spawn_stack_max", stack_min)
    if isinstance(stack_min, bool) or not isinstance(stack_min, int) or stack_min < 1:
        raise ItemLoadError(f"{context}: spawn_stack_min must be an integer >= 1")
    if isinstance(stack_max, bool) or not isinstance(stack_max, int) or stack_max < 1:
        raise ItemLoadError(f"{context}: spawn_stack_max must be an integer >= 1")
    if stack_min > stack_max:
        raise ItemLoadError(
            f"{context}: spawn_stack_min ({stack_min}) cannot exceed "
            f"spawn_stack_max ({stack_max})"
        )
    return ThrowableDefinition(
        id=_require_str(entry, "id", context=context),
        display_name=_require_str(entry, "display_name", context=context),
        glyph=_require_str(entry, "glyph", context=context),
        fg=_parse_fg(entry.get("fg"), context=context),
        examine=_require_str(entry, "examine", context=context),
        min_damage=min_damage,
        max_damage=max_damage,
        accuracy_bonus=_require_number(entry, "accuracy_bonus", context=context),
        spawn=_parse_spawn(entry, context=context),
        spawn_stack_min=stack_min,
        spawn_stack_max=stack_max,
    )


def _parse_wand(entry: dict[str, Any], *, context: str) -> WandDefinition:
    effect = _require_str(entry, "effect", context=context)
    if effect != "magic_missile":
        raise ItemLoadError(f"{context}: unsupported wand effect '{effect}'")
    return WandDefinition(
        id=_require_str(entry, "id", context=context),
        display_name=_require_str(entry, "display_name", context=context),
        glyph=_require_str(entry, "glyph", context=context),
        fg=_parse_fg(entry.get("fg"), context=context),
        examine=_require_str(entry, "examine", context=context),
        effect=effect,
        charges_max=_require_int(entry, "charges_max", context=context),
        charges_start=_require_int(entry, "charges_start", context=context),
        range=_require_int(entry, "range", context=context),
        min_damage=_require_int(entry, "min_damage", context=context),
        max_damage=_require_int(entry, "max_damage", context=context),
        accuracy=_require_number(entry, "accuracy", context=context),
        spawn=_parse_spawn(entry, context=context),
    )


def load_item_registry(
    *,
    weapons_path: Path | None = None,
    armor_path: Path | None = None,
    potions_path: Path | None = None,
    wands_path: Path | None = None,
    throwables_path: Path | None = None,
    mods_root: Path | None = None,
    report_mod_errors: bool = True,
) -> ItemRegistry:
    """Load and validate all item JSON files into a frozen registry.

    When all explicit paths are omitted, enabled mods layer onto core catalogs
    (later id wins). Explicit paths (tests) are single-file only — no mods.
    """
    from src.data.item_loaders import _ITEM_FILE_KEYS

    explicit = any(
        p is not None
        for p in (weapons_path, armor_path, potions_path, wands_path, throwables_path)
    )
    if not explicit:
        from src.mods.pipeline import load_items_layered

        registry, _issues = load_items_layered(
            mods_root=mods_root,
            report=report_mod_errors,
        )
        return registry

    if mods_root is not None:
        raise TypeError("mods_root requires default item paths (layered load)")

    schema_version = ITEMS_SCHEMA_VERSION

    _, weapons_raw, weapon_warnings = load_item_stub_file(
        weapons_path or WEAPONS_PATH,
        collection_key="weapons",
        known_traits=_ITEM_FILE_KEYS["weapons"] | frozenset({"digestion_ac"}),
    )
    _, armor_raw, armor_warnings = load_item_stub_file(
        armor_path or ARMOR_PATH,
        collection_key="armor",
        known_traits=_ITEM_FILE_KEYS["armor"] | frozenset({"digestion_ac"}),
    )
    _, potions_raw, potion_warnings = load_item_stub_file(
        potions_path or POTIONS_PATH,
        collection_key="potions",
        known_traits=_ITEM_FILE_KEYS["potions"],
    )
    _, wands_raw, wand_warnings = load_item_stub_file(
        wands_path or WANDS_PATH,
        collection_key="wands",
        known_traits=_ITEM_FILE_KEYS["wands"],
    )
    _, throwables_raw, throwable_warnings = load_item_stub_file(
        throwables_path or THROWABLES_PATH,
        collection_key="throwables",
        known_traits=_ITEM_FILE_KEYS["throwables"],
    )
    all_warnings = (
        weapon_warnings
        + armor_warnings
        + potion_warnings
        + wand_warnings
        + throwable_warnings
    )

    weapons = tuple(
        _parse_weapon(entry, context=f"weapons[{index}]")
        for index, entry in enumerate(weapons_raw)
    )
    armor = tuple(
        _parse_armor(entry, context=f"armor[{index}]")
        for index, entry in enumerate(armor_raw)
    )
    potions = tuple(
        _parse_potion(entry, context=f"potions[{index}]")
        for index, entry in enumerate(potions_raw)
    )
    wands = tuple(
        _parse_wand(entry, context=f"wands[{index}]")
        for index, entry in enumerate(wands_raw)
    )
    throwables = tuple(
        _parse_throwable(entry, context=f"throwables[{index}]")
        for index, entry in enumerate(throwables_raw)
    )

    return ItemRegistry(
        schema_version=schema_version,
        weapons=weapons,
        armor=armor,
        potions=potions,
        wands=wands,
        throwables=throwables,
        warnings=all_warnings,
    )