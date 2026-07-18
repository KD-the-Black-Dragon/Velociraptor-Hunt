"""Isolated item JSON fixtures for mechanics tests — not assertions against data/."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import src.systems.inventory as inventory_module
from src.data.item_loader import load_item_registry
from src.data.item_registry import ItemRegistry

STARTER_WEAPON_ID = "dagger"
STARTER_ARMOR_ID = "robes"
STARTER_THROWABLE_ID = "rock"
TEST_WAND_ID = "test_wand"
TEST_WAND_DISPLAY = "test wand"
TEST_POTION_ID = "test_potion"


def default_test_wand_entry() -> dict[str, Any]:
    """Low, stable combat stats for evoke/damage mechanics tests."""
    return _wand_entry(
        TEST_WAND_ID,
        display_name=TEST_WAND_DISPLAY,
        min_damage=2,
        max_damage=6,
    )


def install_test_item_registry(tmp_path: Path) -> ItemRegistry:
    """Pin item mechanics tests to fixture JSON — not live data/ balance."""
    write_item_fixtures(
        tmp_path,
        potions=[_potion_entry(TEST_POTION_ID, display_name="test potion")],
        wands=[default_test_wand_entry()],
    )
    registry = load_fixture_registry(tmp_path)
    install_item_registry(registry)
    return registry


def install_item_registry(registry: ItemRegistry) -> None:
    inventory_module._ITEM_REGISTRY = registry


def clear_item_registry() -> None:
    inventory_module.reset_item_registry_cache()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _weapon_entry(
    item_id: str,
    *,
    display_name: str | None = None,
    min_damage: int = 5,
    max_damage: int = 8,
    accuracy_bonus: float = 0.1,
    durability_max: int = 100,
    spawn_min_depth: int = 1,
    spawn_max_depth: int = 1000,
    spawn_weight: int = 1,
) -> dict[str, Any]:
    return {
        "id": item_id,
        "display_name": display_name or item_id.replace("_", " "),
        "glyph": ")",
        "fg": [200, 200, 200],
        "examine": f"Test weapon {item_id}.",
        "min_damage": min_damage,
        "max_damage": max_damage,
        "accuracy_bonus": accuracy_bonus,
        "durability_max": durability_max,
        "spawn_weight": spawn_weight,
        "spawn_min_depth": spawn_min_depth,
        "spawn_max_depth": spawn_max_depth,
        "abilities": [],
    }


def _armor_entry(
    item_id: str,
    *,
    display_name: str | None = None,
    ac_bonus: int = 2,
    digestion_ac: int = 2,
    durability_max: int = 20,
    spawn_min_depth: int = 1,
    spawn_max_depth: int = 1000,
    spawn_weight: int = 1,
) -> dict[str, Any]:
    return {
        "id": item_id,
        "display_name": display_name or item_id.replace("_", " "),
        "glyph": "[",
        "fg": [139, 90, 43],
        "examine": f"Test armor {item_id}.",
        "ac_bonus": ac_bonus,
        "digestion_ac": digestion_ac,
        "durability_max": durability_max,
        "spawn_weight": spawn_weight,
        "spawn_min_depth": spawn_min_depth,
        "spawn_max_depth": spawn_max_depth,
        "abilities": [],
    }


def _potion_entry(
    item_id: str,
    *,
    display_name: str | None = None,
    heal_amount: int = 15,
    spawn_min: int = 0,
    spawn_min_depth: int = 1,
    spawn_max_depth: int = 1000,
    spawn_weight: int = 1,
) -> dict[str, Any]:
    return {
        "id": item_id,
        "display_name": display_name or item_id.replace("_", " "),
        "glyph": "!",
        "fg": [220, 60, 220],
        "examine": f"Test potion {item_id}.",
        "effect": "heal",
        "heal_amount": heal_amount,
        "spawn_weight": spawn_weight,
        "spawn_min": spawn_min,
        "spawn_min_depth": spawn_min_depth,
        "spawn_max_depth": spawn_max_depth,
        "abilities": [],
    }


def _wand_entry(
    item_id: str,
    *,
    display_name: str | None = None,
    range_: int = 5,
    min_damage: int = 2,
    max_damage: int = 6,
    spawn_min_depth: int = 1,
    spawn_max_depth: int = 1000,
    spawn_weight: int = 1,
) -> dict[str, Any]:
    return {
        "id": item_id,
        "display_name": display_name or item_id.replace("_", " "),
        "glyph": "/",
        "fg": [180, 120, 255],
        "examine": f"Test wand {item_id}.",
        "effect": "magic_missile",
        "charges_max": 5,
        "charges_start": 3,
        "range": range_,
        "min_damage": min_damage,
        "max_damage": max_damage,
        "accuracy": 1.0,
        "spawn_weight": spawn_weight,
        "spawn_min_depth": spawn_min_depth,
        "spawn_max_depth": spawn_max_depth,
        "abilities": [],
    }


def _throwable_entry(
    item_id: str,
    *,
    display_name: str | None = None,
    min_damage: int = 1,
    max_damage: int = 2,
    accuracy_bonus: float = 0.0,
    spawn_min_depth: int = 1,
    spawn_max_depth: int = 1000,
    spawn_weight: int = 1,
) -> dict[str, Any]:
    return {
        "id": item_id,
        "display_name": display_name or item_id.replace("_", " "),
        "glyph": ".",
        "fg": [190, 150, 90],
        "examine": f"Test throwable {item_id}.",
        "min_damage": min_damage,
        "max_damage": max_damage,
        "accuracy_bonus": accuracy_bonus,
        "spawn_weight": spawn_weight,
        "spawn_min_depth": spawn_min_depth,
        "spawn_max_depth": spawn_max_depth,
        "abilities": [],
    }


def _ensure_starter_entries(
    weapons: list[dict[str, Any]],
    armor: list[dict[str, Any]],
    throwables: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """GameEngine starter loadout requires dagger, robes, and rock ids in the registry."""
    if not any(entry["id"] == STARTER_WEAPON_ID for entry in weapons):
        weapons = [_weapon_entry(STARTER_WEAPON_ID)] + weapons
    if not any(entry["id"] == STARTER_ARMOR_ID for entry in armor):
        armor = [_armor_entry(STARTER_ARMOR_ID, ac_bonus=1, digestion_ac=1)] + armor
    if not any(entry["id"] == STARTER_THROWABLE_ID for entry in throwables):
        throwables = [_throwable_entry(STARTER_THROWABLE_ID)] + throwables
    return weapons, armor, throwables


def write_item_fixtures(
    tmp_path: Path,
    *,
    weapons: list[dict[str, Any]] | None = None,
    armor: list[dict[str, Any]] | None = None,
    potions: list[dict[str, Any]] | None = None,
    wands: list[dict[str, Any]] | None = None,
    throwables: list[dict[str, Any]] | None = None,
    include_starter_defaults: bool = True,
) -> None:
    weapon_entries = list(weapons or [])
    armor_entries = list(armor or [])
    throwable_entries = list(throwables or [])
    if include_starter_defaults:
        weapon_entries, armor_entries, throwable_entries = _ensure_starter_entries(
            weapon_entries,
            armor_entries,
            throwable_entries,
        )
    _write_json(tmp_path / "weapons.json", {"schema_version": 1, "weapons": weapon_entries})
    _write_json(tmp_path / "armor.json", {"schema_version": 1, "armor": armor_entries})
    _write_json(tmp_path / "potions.json", {"schema_version": 1, "potions": potions or []})
    _write_json(tmp_path / "wands.json", {"schema_version": 1, "wands": wands or []})
    _write_json(
        tmp_path / "throwables.json",
        {"schema_version": 1, "throwables": throwable_entries},
    )


def load_fixture_registry(tmp_path: Path) -> ItemRegistry:
    return load_item_registry(
        weapons_path=tmp_path / "weapons.json",
        armor_path=tmp_path / "armor.json",
        potions_path=tmp_path / "potions.json",
        wands_path=tmp_path / "wands.json",
        throwables_path=tmp_path / "throwables.json",
    )


def first_catalog_potion_id(registry: ItemRegistry | None = None) -> str:
    reg = registry if registry is not None else load_item_registry()
    return reg.potions[0].id


def first_catalog_potion_display(registry: ItemRegistry | None = None) -> str:
    reg = registry if registry is not None else load_item_registry()
    return reg.potions[0].display_name


def write_weighted_weapon_pool(tmp_path: Path, count: int) -> ItemRegistry:
    weapons = [
        _weapon_entry(f"pool_weapon_{index}", spawn_weight=1)
        for index in range(count)
    ]
    write_item_fixtures(
        tmp_path,
        weapons=weapons,
        potions=[_potion_entry("guaranteed_potion", spawn_min=1)],
    )
    return load_fixture_registry(tmp_path)