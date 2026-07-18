"""PR-evade: armor evade_bonus, natural_evade runes, effective_fighter."""

from __future__ import annotations

from tcod.ecs import Registry

from src.components import (
    EquipState,
    Fighter,
    Inventory,
    InventoryItemInstance,
    ItemCategory,
    Player,
    PlayerProgression,
)
from src.data.floor_rune_loader import parse_floor_rune_registry
from src.data.floor_rune_registry import RuneEffect
from src.data.item_loader import ItemLoadError, _parse_armor
from src.data.item_registry import ArmorDefinition, ItemRegistry, ItemSpawnConfig
from src.systems.floor_runes import apply_rune_effect
from src.systems.inventory import effective_fighter
from src.systems import inventory as inv_mod
from src.ui.status_corner import progression_extra_rows


def _parse_armor_fixture(**overrides: object) -> ArmorDefinition:
    raw: dict = {
        "id": "test_leather",
        "display_name": "test leather",
        "glyph": "[",
        "fg": [1, 2, 3],
        "examine": "test",
        "ac_bonus": 2,
        "digestion_ac": 1,
        "durability_max": 10,
        "spawn_weight": 1,
        "spawn_min_depth": 1,
        "spawn_max_depth": 10,
    }
    raw.update(overrides)
    return _parse_armor(raw, context="test armor")


def test_armor_evade_bonus_defaults_zero() -> None:
    armor = _parse_armor_fixture()
    assert armor.evade_bonus == 0


def test_armor_evade_bonus_parsed() -> None:
    armor = _parse_armor_fixture(evade_bonus=2)
    assert armor.evade_bonus == 2.0


def test_armor_evade_bonus_accepts_float() -> None:
    armor = _parse_armor_fixture(evade_bonus=0.5)
    assert armor.evade_bonus == 0.5


def test_armor_evade_bonus_rejects_negative() -> None:
    try:
        _parse_armor_fixture(evade_bonus=-1)
    except ItemLoadError as exc:
        assert "evade_bonus" in str(exc)
    else:
        raise AssertionError("expected ItemLoadError")


def test_natural_evade_pieces_then_bonus() -> None:
    world = Registry()
    player = world[object()]
    player.tags.add(Player)
    player.components[Fighter] = Fighter(
        hp=30, max_hp=30, accuracy=1.5, evade=1, ac=1, min_damage=1, max_damage=2
    )
    player.components[PlayerProgression] = PlayerProgression()
    effect = RuneEffect(
        type="natural_evade", amount=1, pieces_per_bonus=2, pieces_granted=1
    )
    text = apply_rune_effect(player, effect)
    prog = player.components[PlayerProgression]
    assert prog.bonus_evade == 0
    assert prog.pieces_evade == 1
    assert "1/2" in text or "Evade" in text
    text = apply_rune_effect(player, effect)
    assert prog.bonus_evade == 1
    assert prog.pieces_evade == 0
    assert "+1 evade" in text or "complete" in text


def test_natural_evade_half_point_bonus() -> None:
    """Stock continuous evade: completed bank grants +0.5, not +1."""
    world = Registry()
    player = world[object()]
    player.tags.add(Player)
    player.components[Fighter] = Fighter(
        hp=30, max_hp=30, accuracy=1.5, evade=1.0, ac=1, min_damage=1, max_damage=2
    )
    player.components[PlayerProgression] = PlayerProgression()
    effect = RuneEffect(
        type="natural_evade", amount=0.5, pieces_per_bonus=2, pieces_granted=1
    )
    apply_rune_effect(player, effect)
    apply_rune_effect(player, effect)
    prog = player.components[PlayerProgression]
    assert prog.bonus_evade == 0.5
    assert prog.pieces_evade == 0


def test_natural_evade_parses_in_registry_document() -> None:
    raw = {
        "schema_version": 1,
        "runes_per_floor": 3,
        "runes": [
            {
                "id": "test_evasion",
                "display_name": "test evasion",
                "glyph": "0",
                "fg": [1, 2, 3],
                "examine": "x",
                "weight": 1,
                "min_depth": 1,
                "max_depth": 10,
                "effect": {
                    "type": "natural_evade",
                    "amount": 1,
                    "pieces_per_bonus": 2,
                    "pieces_granted": 1,
                },
            }
        ],
    }
    reg = parse_floor_rune_registry(raw)
    assert reg.get("test_evasion").effect.type == "natural_evade"


def test_effective_fighter_stacks_base_armor_and_prog_evade() -> None:
    world = Registry()
    player = world[object()]
    player.tags.add(Player)
    player.components[Fighter] = Fighter(
        hp=30, max_hp=30, accuracy=1.5, evade=1, ac=1, min_damage=1, max_damage=2
    )
    inv = Inventory()
    inv.slots["a"] = InventoryItemInstance(
        category=ItemCategory.ARMOR,
        item_id="fixture_plate",
        durability=10,
    )
    player.components[Inventory] = inv
    player.components[EquipState] = EquipState(worn_slot="a")
    player.components[PlayerProgression] = PlayerProgression(bonus_evade=1)

    spawn = ItemSpawnConfig(weight=1, min_depth=1, max_depth=1)
    armor = ArmorDefinition(
        id="fixture_plate",
        display_name="fixture plate",
        glyph="[",
        fg=(1, 1, 1),
        examine="x",
        ac_bonus=3,
        digestion_ac=1,
        durability_max=10,
        spawn=spawn,
        evade_bonus=4,
    )
    fake_reg = ItemRegistry(
        schema_version=1,
        weapons=(),
        armor=(armor,),
        potions=(),
        wands=(),
        throwables=(),
    )

    old = inv_mod._ITEM_REGISTRY
    inv_mod._ITEM_REGISTRY = fake_reg
    try:
        ef = effective_fighter(player)
        assert ef.evade == 6  # base 1 + armor 4 + prog 1
    finally:
        inv_mod._ITEM_REGISTRY = old


def test_status_corner_shows_evade_progress() -> None:
    prog = PlayerProgression(
        bonus_evade=1, pieces_evade=1, pieces_need_evade=2, pieces_evade_need_frozen=True
    )
    rows = progression_extra_rows(prog, max_width=12)
    texts = " ".join(r.text for r in rows)
    assert "Ev" in texts
    assert "+1" in texts
