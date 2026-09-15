from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.constants import DATA_DIR
from src.data.warnings import LoadWarnings

WEAPONS_PATH = DATA_DIR / "weapons.json"
ARMOR_PATH = DATA_DIR / "armor.json"
POTIONS_PATH = DATA_DIR / "potions.json"
WANDS_PATH = DATA_DIR / "wands.json"
THROWABLES_PATH = DATA_DIR / "throwables.json"

_ITEM_FILE_KEYS = {
    "weapons": frozenset(
        {
            "id",
            "display_name",
            "glyph",
            "fg",
            "examine",
            "min_damage",
            "max_damage",
            "accuracy_bonus",
            "durability_max",
            "spawn_weight",
            "spawn_min_depth",
            "spawn_max_depth",
            "abilities",
            "attack_delay",
            "measure",
            "swappable",
        }
    ),
    "armor": frozenset(
        {
            "id",
            "display_name",
            "glyph",
            "fg",
            "examine",
            "ac_bonus",
            "evade_bonus",
            "digestion_ac",
            "durability_max",
            "spawn_weight",
            "spawn_min_depth",
            "spawn_max_depth",
            "abilities",
        }
    ),
    "potions": frozenset(
        {
            "id",
            "display_name",
            "glyph",
            "fg",
            "examine",
            "effect",
            "heal_amount",
            "duration_turns",
            "accuracy_bonus",
            "min_damage_bonus",
            "max_damage_bonus",
            "delay_min_turns",
            "delay_max_turns",
            "spawn_weight",
            "spawn_min",
            "spawn_min_depth",
            "spawn_max_depth",
            "abilities",
        }
    ),
    "wands": frozenset(
        {
            "id",
            "display_name",
            "glyph",
            "fg",
            "examine",
            "effect",
            "charges_max",
            "charges_start",
            "range",
            "min_damage",
            "max_damage",
            "accuracy",
            "spawn_weight",
            "spawn_min_depth",
            "spawn_max_depth",
            "abilities",
        }
    ),
    "throwables": frozenset(
        {
            "id",
            "display_name",
            "glyph",
            "fg",
            "examine",
            "min_damage",
            "max_damage",
            "accuracy_bonus",
            "spawn_weight",
            "spawn_min_depth",
            "spawn_max_depth",
            "spawn_stack_min",
            "spawn_stack_max",
            "abilities",
        }
    ),
}


class ItemLoadError(ValueError):
    pass


def load_item_stub_file(
    path: Path,
    *,
    collection_key: str,
    known_traits: frozenset[str],
) -> tuple[int, tuple[dict[str, Any], ...], tuple[str, ...]]:
    """Parse an item JSON stub; returns schema version, entries, and warnings."""
    with path.open(encoding="utf-8") as handle:
        raw = json.load(handle)
    warnings = LoadWarnings()
    schema_version = raw.get("schema_version")
    if not isinstance(schema_version, int):
        raise ItemLoadError(f"{path.name}: schema_version must be an integer")

    entries_raw = raw.get(collection_key)
    if not isinstance(entries_raw, list):
        raise ItemLoadError(f"{path.name}: missing '{collection_key}' array")

    entries: list[dict[str, Any]] = []
    for index, entry in enumerate(entries_raw):
        if not isinstance(entry, dict):
            raise ItemLoadError(f"{path.name}: {collection_key}[{index}] must be an object")
        item_id = entry.get("id", f"{collection_key}[{index}]")
        if not isinstance(item_id, str):
            item_id = str(index)
        for key in entry:
            if key not in known_traits:
                warnings.warn_unknown_trait(key, item_id)
        entries.append(entry)

    return schema_version, tuple(entries), warnings.messages


def load_weapons_stub(path: Path | None = None) -> tuple[int, tuple[dict[str, Any], ...], tuple[str, ...]]:
    return load_item_stub_file(
        path or WEAPONS_PATH,
        collection_key="weapons",
        known_traits=_ITEM_FILE_KEYS["weapons"],
    )


def load_armor_stub(path: Path | None = None) -> tuple[int, tuple[dict[str, Any], ...], tuple[str, ...]]:
    return load_item_stub_file(
        path or ARMOR_PATH,
        collection_key="armor",
        known_traits=_ITEM_FILE_KEYS["armor"],
    )


def load_potions_stub(path: Path | None = None) -> tuple[int, tuple[dict[str, Any], ...], tuple[str, ...]]:
    return load_item_stub_file(
        path or POTIONS_PATH,
        collection_key="potions",
        known_traits=_ITEM_FILE_KEYS["potions"],
    )


def load_wands_stub(path: Path | None = None) -> tuple[int, tuple[dict[str, Any], ...], tuple[str, ...]]:
    return load_item_stub_file(
        path or WANDS_PATH,
        collection_key="wands",
        known_traits=_ITEM_FILE_KEYS["wands"],
    )


def load_throwables_stub(
    path: Path | None = None,
) -> tuple[int, tuple[dict[str, Any], ...], tuple[str, ...]]:
    return load_item_stub_file(
        path or THROWABLES_PATH,
        collection_key="throwables",
        known_traits=_ITEM_FILE_KEYS["throwables"],
    )