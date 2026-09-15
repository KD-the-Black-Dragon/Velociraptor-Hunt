"""PR4: layered id catalogs — items, floor runes, macguffins, names."""

from __future__ import annotations

import json
from pathlib import Path

from src.data.floor_rune_loader import load_floor_rune_registry
from src.data.item_loader import load_item_registry
from src.data.macguffin_loader import load_macguffin_registry
from src.data.names_loader import load_names_registry, reset_names_registry
from src.mods.pipeline import (
    load_floor_runes_layered,
    load_items_layered,
    load_macguffins_layered,
    load_names_layered,
)
from src.mods.state import write_mod_state
from src.systems.inventory import reset_item_registry_cache


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _mod(root: Path, name: str, *, order: int = 1) -> Path:
    folder = root / name
    folder.mkdir(parents=True, exist_ok=True)
    write_mod_state(folder, enabled=True, order=order)
    return folder


def _minimal_weapon(**overrides: object) -> dict:
    base: dict = {
        "id": "test_blade",
        "display_name": "test blade",
        "glyph": ")",
        "fg": [200, 200, 200],
        "examine": "A test weapon.",
        "min_damage": 1,
        "max_damage": 2,
        "accuracy_bonus": 0.0,
        "durability_max": 10,
        "spawn_weight": 1,
        "spawn_min_depth": 1,
        "spawn_max_depth": 99,
        "abilities": [],
    }
    base.update(overrides)
    return base


def _minimal_armor(**overrides: object) -> dict:
    base: dict = {
        "id": "test_armor",
        "display_name": "test armor",
        "glyph": "[",
        "fg": [180, 180, 180],
        "examine": "Test armor.",
        "ac_bonus": 1,
        "digestion_ac": 0,
        "durability_max": 10,
        "spawn_weight": 1,
        "spawn_min_depth": 1,
        "spawn_max_depth": 99,
        "abilities": [],
    }
    base.update(overrides)
    return base


def _minimal_potion(**overrides: object) -> dict:
    base: dict = {
        "id": "test_potion",
        "display_name": "test potion",
        "glyph": "!",
        "fg": [220, 80, 80],
        "examine": "Test potion.",
        "effect": "heal",
        "heal_amount": 5,
        "spawn_weight": 1,
        "spawn_min": 0,
        "spawn_min_depth": 1,
        "spawn_max_depth": 99,
        "abilities": [],
    }
    base.update(overrides)
    return base


def _minimal_wand(**overrides: object) -> dict:
    base: dict = {
        "id": "test_wand",
        "display_name": "test wand",
        "glyph": "/",
        "fg": [120, 160, 220],
        "examine": "Test wand.",
        "effect": "magic_missile",
        "charges_max": 5,
        "charges_start": 5,
        "range": 5,
        "min_damage": 1,
        "max_damage": 3,
        "accuracy": 1.0,
        "spawn_weight": 1,
        "spawn_min_depth": 1,
        "spawn_max_depth": 99,
        "abilities": [],
    }
    base.update(overrides)
    return base


def _minimal_rune(**overrides: object) -> dict:
    base: dict = {
        "id": "test_rune",
        "display_name": "test rune",
        "glyph": "0",
        "fg": [80, 220, 120],
        "examine": "A test rune.",
        "weight": 1,
        "min_depth": 1,
        "max_depth": 100,
        "effect": {"type": "max_hp", "amount": 1},
    }
    base.update(overrides)
    return base


def _minimal_macguffin(**overrides: object) -> dict:
    base: dict = {
        "id": "test_macguffin",
        "display_name": "test macguffin",
        "glyph": "*",
        "fg": [255, 215, 0],
        "examine": "A test macguffin.",
        "min_depth": 1,
        "max_depth": 100,
        "score": 10,
    }
    base.update(overrides)
    return base


def test_weapons_mod_adds_and_overrides(tmp_path: Path) -> None:
    core = tmp_path / "weapons.json"
    _write_json(
        core,
        {
            "schema_version": 1,
            "weapons": [_minimal_weapon(id="dagger", display_name="core dagger")],
        },
    )
    empty = {
        "schema_version": 1,
        "armor": [],
        "potions": [],
        "wands": [],
    }
    # Provide empty sibling cores for other item files
    armor = tmp_path / "armor.json"
    potions = tmp_path / "potions.json"
    wands = tmp_path / "wands.json"
    _write_json(armor, {"schema_version": 1, "armor": []})
    _write_json(potions, {"schema_version": 1, "potions": []})
    _write_json(wands, {"schema_version": 1, "wands": []})

    mods = tmp_path / "mods"
    folder = _mod(mods, "WeaponPack")
    _write_json(
        folder / "weapons.json",
        {
            "schema_version": 1,
            "weapons": [
                _minimal_weapon(id="dagger", display_name="mod dagger", min_damage=9, max_damage=9),
                _minimal_weapon(id="laser", display_name="laser sword"),
            ],
        },
    )

    reg, issues = load_items_layered(
        weapons_path=core,
        armor_path=armor,
        potions_path=potions,
        wands_path=wands,
        mods_root=mods,
        report=False,
    )
    assert issues == ()
    by_id = {w.id: w for w in reg.weapons}
    assert by_id["dagger"].display_name == "mod dagger"
    assert by_id["dagger"].min_damage == 9
    assert "laser" in by_id


def test_bad_weapons_mod_skipped(tmp_path: Path) -> None:
    core = tmp_path / "weapons.json"
    _write_json(
        core,
        {"schema_version": 1, "weapons": [_minimal_weapon(id="dagger", display_name="core")]},
    )
    armor = tmp_path / "armor.json"
    potions = tmp_path / "potions.json"
    wands = tmp_path / "wands.json"
    _write_json(armor, {"schema_version": 1, "armor": []})
    _write_json(potions, {"schema_version": 1, "potions": []})
    _write_json(wands, {"schema_version": 1, "wands": []})

    mods = tmp_path / "mods"
    folder = _mod(mods, "BrokenWeapons")
    (folder / "weapons.json").write_text("{ not json", encoding="utf-8")

    reg, issues = load_items_layered(
        weapons_path=core,
        armor_path=armor,
        potions_path=potions,
        wands_path=wands,
        mods_root=mods,
        report=False,
    )
    assert len(issues) == 1
    assert issues[0].mod_name == "BrokenWeapons"
    assert issues[0].filename == "weapons.json"
    assert {w.id: w.display_name for w in reg.weapons}["dagger"] == "core"


def test_floor_runes_override_and_add(tmp_path: Path) -> None:
    core = tmp_path / "floor_runes.json"
    _write_json(
        core,
        {
            "schema_version": 1,
            "runes": [_minimal_rune(id="vitality_rune", display_name="core vitality")],
        },
    )
    mods = tmp_path / "mods"
    folder = _mod(mods, "RunePack")
    _write_json(
        folder / "floor_runes.json",
        {
            "schema_version": 1,
            "runes": [
                _minimal_rune(id="vitality_rune", display_name="mod vitality"),
                _minimal_rune(id="cool_rune", display_name="cool rune"),
            ],
        },
    )
    reg, issues = load_floor_runes_layered(core_path=core, mods_root=mods, report=False)
    assert issues == ()
    by_id = {r.id: r for r in reg.runes}
    assert by_id["vitality_rune"].display_name == "mod vitality"
    assert "cool_rune" in by_id


def test_macguffins_override(tmp_path: Path) -> None:
    core = tmp_path / "macguffins.json"
    _write_json(
        core,
        {
            "schema_version": 1,
            "macguffins": [_minimal_macguffin(id="sword", display_name="core sword", score=1)],
        },
    )
    mods = tmp_path / "mods"
    folder = _mod(mods, "MacPack")
    _write_json(
        folder / "macguffins.json",
        {
            "schema_version": 1,
            "macguffins": [
                _minimal_macguffin(id="sword", display_name="mod sword", score=99),
            ],
        },
    )
    reg, issues = load_macguffins_layered(core_path=core, mods_root=mods, report=False)
    assert issues == ()
    assert reg.macguffins[0].display_name == "mod sword"
    assert reg.macguffins[0].score == 99


def test_names_pool_replace_and_add(tmp_path: Path) -> None:
    core = tmp_path / "names.json"
    _write_json(
        core,
        {"schema_version": 1, "names": {"knight": ["Sir Core"]}},
    )
    mods = tmp_path / "mods"
    folder = _mod(mods, "NamePack")
    _write_json(
        folder / "names.json",
        {
            "schema_version": 1,
            "names": {
                "knight": ["Sir Mod"],
                "dragon": ["Draco"],
            },
        },
    )
    reg, issues = load_names_layered(core_path=core, mods_root=mods, report=False)
    assert issues == ()
    assert reg.names["knight"] == ("Sir Mod",)
    assert reg.names["dragon"] == ("Draco",)


def test_bad_names_mod_skipped(tmp_path: Path) -> None:
    core = tmp_path / "names.json"
    _write_json(core, {"schema_version": 1, "names": {"knight": ["Sir Core"]}})
    mods = tmp_path / "mods"
    folder = _mod(mods, "BadNames")
    _write_json(folder / "names.json", {"schema_version": 1, "names": {"knight": []}})

    reg, issues = load_names_layered(core_path=core, mods_root=mods, report=False)
    assert len(issues) == 1
    assert issues[0].filename == "names.json"
    assert reg.names["knight"] == ("Sir Core",)


def test_default_loaders_use_mods_root(tmp_path: Path, monkeypatch) -> None:
    """Smoke: live core + temp mod adds a weapon id via default load_item_registry path."""
    mods = tmp_path / "mods"
    folder = _mod(mods, "ExtraBlade")
    _write_json(
        folder / "weapons.json",
        {
            "schema_version": 1,
            "weapons": [_minimal_weapon(id="pipeline_only_blade", display_name="Pipeline Blade")],
        },
    )
    monkeypatch.setattr("src.user_data.MODS_DIR", mods)
    reset_item_registry_cache()
    reg = load_item_registry(report_mod_errors=False)
    assert any(w.id == "pipeline_only_blade" for w in reg.weapons)


def test_explicit_item_paths_ignore_mods(tmp_path: Path) -> None:
    weapons = tmp_path / "weapons.json"
    armor = tmp_path / "armor.json"
    potions = tmp_path / "potions.json"
    wands = tmp_path / "wands.json"
    _write_json(weapons, {"schema_version": 1, "weapons": [_minimal_weapon(id="solo")]})
    _write_json(armor, {"schema_version": 1, "armor": []})
    _write_json(potions, {"schema_version": 1, "potions": []})
    _write_json(wands, {"schema_version": 1, "wands": []})

    mods = tmp_path / "mods"
    folder = _mod(mods, "Ignored")
    _write_json(
        folder / "weapons.json",
        {
            "schema_version": 1,
            "weapons": [_minimal_weapon(id="solo", display_name="should not apply")],
        },
    )

    reg = load_item_registry(
        weapons_path=weapons,
        armor_path=armor,
        potions_path=potions,
        wands_path=wands,
    )
    assert reg.weapons[0].display_name == "test blade"


def test_explicit_rune_path_ignores_mods(tmp_path: Path) -> None:
    path = tmp_path / "floor_runes.json"
    _write_json(
        path,
        {"schema_version": 1, "runes": [_minimal_rune(id="only", display_name="solo")]},
    )
    mods = tmp_path / "mods"
    folder = _mod(mods, "X")
    _write_json(
        folder / "floor_runes.json",
        {
            "schema_version": 1,
            "runes": [_minimal_rune(id="only", display_name="modded")],
        },
    )
    reg = load_floor_rune_registry(path)
    assert reg.runes[0].display_name == "solo"
