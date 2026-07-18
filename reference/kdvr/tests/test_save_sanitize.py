"""Soft-drop unknown items/entities on load; spawn.weight 0 deprecates content."""

from __future__ import annotations

from src.components import (
    EquipState,
    Inventory,
    InventoryItemInstance,
    Item,
    ItemCategory,
    Player,
    Position,
    SpeciesId,
)
from src.data.entity_loader import load_entity_registry
from src.data.item_loader import load_item_registry
from src.engine import GameEngine
from src.save.sanitize import sanitize_loaded_world
from src.save.snapshot import apply_run_snapshot, build_run_snapshot
from tests.map_test_helpers import isolate_other_ais


def test_entity_spawn_weight_zero_loads() -> None:
    """weight 0 is valid (never spawn); negative still invalid."""
    import json
    from pathlib import Path

    from src.data.entity_loader import load_entity_registry
    import tempfile

    raw = {
        "schema_version": 1,
        "entities": [
            {
                "id": "deprecated_blob",
                "display_name": "blob",
                "glyph": "b",
                "fg": [100, 100, 100],
                "alignment": "neutral",
                "mobility": "ground",
                "max_hp": 1,
                "accuracy": 0.5,
                "evade": 5,
                "ac": 0,
                "min_damage": 1,
                "max_damage": 1,
                "examine": "A retired blob.",
                "spawn": {"weight": 0, "min_depth": 1, "max_depth": 1, "terrain": "land"},
            }
        ],
    }
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "entities.json"
        path.write_text(json.dumps(raw), encoding="utf-8")
        reg = load_entity_registry(path)
        assert reg.get("deprecated_blob").spawn.weight == 0


def test_sanitize_drops_unknown_inventory_item() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.new_game(seed=7)
    player = engine.player
    assert player is not None
    inv = player.components[Inventory]
    inv.slots["c"] = InventoryItemInstance(
        item_id="longsword_that_never_existed",
        category=ItemCategory.WEAPON,
        durability=10,
    )
    equip = player.components.setdefault(EquipState, EquipState())
    equip.wielded_slot = "c"

    report = sanitize_loaded_world(engine.world)
    assert "longsword_that_never_existed" in report.dropped_item_ids
    assert inv.slots["c"] is None
    assert equip.wielded_slot is None


def test_sanitize_drops_unknown_species_npc() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.new_game(seed=8)
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    ghost = engine.world.new_entity()
    ghost.components[Position] = Position(pos.x + 1, pos.y)
    ghost.components[SpeciesId] = SpeciesId(id="totally_fake_species")

    report = sanitize_loaded_world(engine.world)
    assert "totally_fake_species" in report.dropped_entity_ids
    assert SpeciesId not in ghost.components or not list(
        engine.world.Q.all_of(components=[SpeciesId])
    ) or all(
        e.components[SpeciesId].id != "totally_fake_species"
        or Player in e.tags
        for e in engine.world.Q.all_of(components=[SpeciesId])
    )


def test_snapshot_roundtrip_still_works() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.new_game(seed=9)
    snap = build_run_snapshot(engine)
    engine2 = GameEngine(skip_new_game=True)
    apply_run_snapshot(engine2, snap)
    assert engine2.player is not None
