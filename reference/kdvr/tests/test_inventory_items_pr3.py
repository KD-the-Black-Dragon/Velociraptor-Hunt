"""PR 3: wield/wear, effective combat stats, durability, digestion armor."""

from __future__ import annotations

import random
from unittest.mock import patch

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src import messages
from src.components import (
    DigestionStats,
    EquipState,
    Fighter,
    Inventory,
    ItemCategory,
    Position,
)
from src.constants import (
    MAP_HEIGHT,
    PLAYER_AC,
    PLAYER_ACCURACY,
    PLAYER_MAX_DAMAGE,
    PLAYER_MIN_DAMAGE,
    SCREEN_WIDTH,
)
from src.engine import GameEngine
from src.message_log import ALERT_MESSAGE_FG
from src.systems.combat import resolve_attack, try_action
from src.systems.digestion import apply_player_digestion_tick
from src.systems.inventory import (
    STARTER_ARMOR_SLOT,
    STARTER_ROCK_STACK_COUNT,
    STARTER_THROWABLE_SLOT,
    STARTER_WEAPON_SLOT,
    apply_starter_loadout,
    effective_fighter,
    make_armor_instance,
    make_weapon_instance,
    reset_item_registry_cache,
)
from src.systems.item_modals import (
    InventoryModalMode,
    drop_item_from_slot,
    inspect_list_modal_text,
    wield_list_modal_text,
)

from tests.fight_helpers import fighter_inert
from tests.item_test_helpers import (
    _armor_entry,
    _weapon_entry,
    install_item_registry,
    load_fixture_registry,
    write_item_fixtures,
)
from tests.map_test_helpers import carve_east_of, first_wolf

import pytest
import tcod.console
from src.constants import SCREEN_HEIGHT


@pytest.fixture(autouse=True)
def _clear_item_registry_cache() -> None:
    reset_item_registry_cache()
    yield
    reset_item_registry_cache()


def _key(sym: KeySym, *, mod: Modifier = Modifier.NONE) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=mod)


class _FixedRollRng:
    def __init__(self, value: int | float) -> None:
        self._value = value

    def randint(self, _a: int, _b: int) -> int:
        return int(self._value)

    def uniform(self, _a: float, _b: float) -> float:
        return float(self._value)


def test_effective_fighter_wielded_weapon_changes_damage(tmp_path) -> None:
    write_item_fixtures(
        tmp_path,
        weapons=[_weapon_entry("strong_weapon", min_damage=7, max_damage=11, accuracy_bonus=0.2)],
    )
    registry = load_fixture_registry(tmp_path)
    install_item_registry(registry)
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Inventory].slots["a"] = make_weapon_instance("strong_weapon")
    player.components[EquipState].wielded_slot = "a"

    fighter = effective_fighter(player)
    assert fighter.min_damage == 7
    assert fighter.max_damage == 11
    assert fighter.accuracy > PLAYER_ACCURACY


def test_effective_fighter_worn_armor_changes_ac(tmp_path) -> None:
    write_item_fixtures(
        tmp_path,
        armor=[_armor_entry("tough_armor", ac_bonus=4)],
    )
    registry = load_fixture_registry(tmp_path)
    install_item_registry(registry)
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Inventory].slots["b"] = make_armor_instance("tough_armor")
    player.components[EquipState].worn_slot = "b"

    fighter = effective_fighter(player)
    assert fighter.ac == PLAYER_AC + 4


def test_wield_weapon_consumes_turn() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Inventory].slots["c"] = make_weapon_instance(item_id="club")
    turns_before = engine.player_turn_count

    engine.handle_event(_key(KeySym.w))
    assert engine.inventory_modal.mode == InventoryModalMode.WIELD
    engine.handle_event(_key(KeySym.c))

    assert messages.wield_item("club") in engine.message_log.lines()
    assert player.components[EquipState].wielded_slot == "c"
    assert not engine.inventory_modal.active
    assert engine.player_turn_count == turns_before + 1


def test_already_wielding_closes_modal_without_turn() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Inventory].slots["a"] = make_weapon_instance()
    player.components[EquipState].wielded_slot = "a"
    turns_before = engine.player_turn_count

    engine.handle_event(_key(KeySym.w))
    engine.handle_event(_key(KeySym.a))

    assert messages.already_wielding() in engine.message_log.lines()
    assert not engine.inventory_modal.active
    assert engine.player_turn_count == turns_before


def test_wear_armor_consumes_turn() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Inventory].slots["c"] = make_armor_instance()
    turns_before = engine.player_turn_count

    engine.handle_event(_key(KeySym.w, mod=Modifier.SHIFT))
    engine.handle_event(_key(KeySym.c))

    assert messages.wear_item("leather armor") in engine.message_log.lines()
    assert player.components[EquipState].worn_slot == "c"
    assert engine.player_turn_count == turns_before + 1


def test_no_weapons_message() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    inventory = player.components[Inventory]
    equip = player.components[EquipState]
    inventory.slots["a"] = None
    equip.wielded_slot = None
    engine.handle_event(_key(KeySym.w))
    assert messages.no_weapons() in engine.message_log.lines()
    assert not engine.inventory_modal.active


def test_no_armor_message() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    inventory = player.components[Inventory]
    equip = player.components[EquipState]
    inventory.slots["b"] = None
    equip.worn_slot = None
    engine.handle_event(_key(KeySym.w, mod=Modifier.SHIFT))
    assert messages.no_armor() in engine.message_log.lines()
    assert not engine.inventory_modal.active


def test_weapon_durability_degrades_on_successful_hit() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    wolf = first_wolf(engine)
    pos = player.components[Position]
    carve_east_of(engine, pos, 2)
    wolf.components[Position] = Position(pos.x + 1, pos.y)

    instance = make_weapon_instance(durability=5)
    player.components[Inventory].slots["a"] = instance
    player.components[EquipState].wielded_slot = "a"

    with patch("src.systems.combat.random.Random", return_value=_FixedRollRng(0)):
        try_action(engine.world, engine.game_map, player, (1, 0), engine.message_log)

    assert instance.durability == 4


def test_weapon_destroyed_at_zero_durability_red_log() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    wolf = first_wolf(engine)
    pos = player.components[Position]
    carve_east_of(engine, pos, 2)
    wolf.components[Position] = Position(pos.x + 1, pos.y)

    instance = make_weapon_instance(durability=1)
    player.components[Inventory].slots["a"] = instance
    player.components[EquipState].wielded_slot = "a"

    with patch("src.systems.combat.random.Random", return_value=_FixedRollRng(0)):
        try_action(engine.world, engine.game_map, player, (1, 0), engine.message_log)

    assert player.components[Inventory].slots["a"] is None
    assert player.components[EquipState].wielded_slot is None
    assert messages.item_destroyed("dagger") in engine.message_log.lines()
    alert_entries = [
        entry for entry in engine.message_log.entries() if entry.fg == ALERT_MESSAGE_FG
    ]
    assert any(messages.item_destroyed("dagger") in entry.text for entry in alert_entries)


def test_worn_armor_mitigates_digestion_and_degrades(tmp_path) -> None:
    write_item_fixtures(
        tmp_path,
        armor=[_armor_entry("digest_armor", digestion_ac=2)],
    )
    registry = load_fixture_registry(tmp_path)
    install_item_registry(registry)
    engine = GameEngine()
    player = engine.player
    assert player is not None
    wolf = first_wolf(engine)
    pos = player.components[Position]
    carve_east_of(engine, pos, 2)
    wolf.components[Position] = Position(pos.x + 1, pos.y)

    instance = make_armor_instance("digest_armor", durability=10)
    player.components[Inventory].slots["b"] = instance
    player.components[EquipState].worn_slot = "b"
    player.components[Fighter].hp = 10

    apply_player_digestion_tick(player, wolf, engine.message_log)

    raw_tick = wolf.components[DigestionStats].damage_per_tick
    mitigated = min(raw_tick, 2)
    assert player.components[Fighter].hp == 10 - (raw_tick - mitigated)
    assert instance.durability == 10 - mitigated


def test_new_game_starter_loadout() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    inventory = player.components[Inventory]
    equip = player.components[EquipState]
    assert inventory.slots[STARTER_WEAPON_SLOT] is not None
    assert inventory.slots[STARTER_ARMOR_SLOT] is not None
    rocks = inventory.slots[STARTER_THROWABLE_SLOT]
    assert rocks is not None
    assert rocks.category == ItemCategory.THROWABLE
    assert rocks.item_id == "rock"
    assert rocks.stack_count == STARTER_ROCK_STACK_COUNT
    assert equip.wielded_slot == STARTER_WEAPON_SLOT
    assert equip.worn_slot == STARTER_ARMOR_SLOT


def test_starter_loadout_improves_effective_fighter() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    fighter = effective_fighter(player)
    assert (
        fighter.min_damage > PLAYER_MIN_DAMAGE
        or fighter.max_damage > PLAYER_MAX_DAMAGE
        or fighter.accuracy > PLAYER_ACCURACY
        or fighter.ac > PLAYER_AC
    )


def test_apply_starter_loadout_idempotent_on_fresh_player() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    weapon_id = player.components[Inventory].slots[STARTER_WEAPON_SLOT].item_id
    armor_id = player.components[Inventory].slots[STARTER_ARMOR_SLOT].item_id
    apply_starter_loadout(player)
    inventory = player.components[Inventory]
    assert inventory.slots[STARTER_WEAPON_SLOT].item_id == weapon_id
    assert inventory.slots[STARTER_ARMOR_SLOT].item_id == armor_id


def test_drop_clears_wielded_and_worn() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Inventory].slots["a"] = make_weapon_instance()
    player.components[Inventory].slots["b"] = make_armor_instance()
    equip = player.components[EquipState]
    equip.wielded_slot = "a"
    equip.worn_slot = "b"

    drop_item_from_slot(engine.world, player, "a", engine.message_log)
    assert equip.wielded_slot is None
    drop_item_from_slot(engine.world, player, "b", engine.message_log)
    assert equip.worn_slot is None


def test_inspect_list_marks_wielded_and_worn() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    inventory = player.components[Inventory]
    equip = player.components[EquipState]
    weapon = inventory.slots[STARTER_WEAPON_SLOT]
    armor = inventory.slots[STARTER_ARMOR_SLOT]
    assert weapon is not None
    assert armor is not None
    from src.systems.inventory import item_registry

    reg = item_registry()
    weapon_name = reg.get_weapon(weapon.item_id).display_name
    armor_name = reg.get_armor(armor.item_id).display_name
    text = inspect_list_modal_text(inventory, equip=equip)
    assert f"a) {weapon_name} (wielded)" in text
    assert f"b) {armor_name} (worn)" in text


def test_wield_modal_lists_weapons_only() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    inventory = player.components[Inventory]
    inventory.slots["a"] = make_weapon_instance()
    inventory.slots["b"] = make_armor_instance()
    inventory.slots["c"] = make_weapon_instance(item_id="dagger")

    text = wield_list_modal_text(inventory)
    assert "a) dagger" in text
    assert "c) dagger" in text
    assert "leather armor" not in text


def test_sidebar_no_inventory_summary() -> None:
    from tests.ui_test_helpers import render_engine_frame, sidebar_text

    engine = GameEngine(player_name="Alex")
    console = render_engine_frame(engine)
    assert "Items:" not in sidebar_text(console, engine.ui_layout)


def test_wielded_weapon_changes_resolve_attack_damage() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Inventory].slots["a"] = make_weapon_instance()
    player.components[EquipState].wielded_slot = "a"

    wielded = effective_fighter(player)
    player.components[EquipState].wielded_slot = None
    unarmed = effective_fighter(player)

    assert unarmed.min_damage == PLAYER_MIN_DAMAGE
    assert wielded.max_damage > PLAYER_MAX_DAMAGE
    defender = fighter_inert()
    hit, damage = resolve_attack(wielded, defender, random.Random(0))
    assert hit
    assert damage <= wielded.max_damage