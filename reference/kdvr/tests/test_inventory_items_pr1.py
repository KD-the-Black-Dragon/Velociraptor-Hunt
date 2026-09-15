"""PR 1: item registries, instances, floor spawn, pickup."""

from __future__ import annotations

import random
import string

import pytest
import tcod.event
from tcod.ecs import Registry
from tcod.event import KeySym

from src import messages
from src.components import Inventory, InventoryItemInstance, Item, Player, Position
from src.constants import MAX_FLOOR_ITEM_PLACEMENTS
from src.data.item_loader import ItemLoadError, load_item_registry
from src.data.item_registry import ItemCategory
from src.engine import GameEngine
from src.map_gen import generate_dungeon
from src.spawn import _build_item_weighted_pool, spawn_item_entity, spawn_items
from src.systems.inventory import (
    GroundPickupModalState,
    begin_manual_pickup,
    first_empty_slot,
    floor_items_at,
    make_potion_instance,
    pickup_all_items_at,
    reset_item_registry_cache,
    try_pickup_floor_entity,
)
from tests.item_test_helpers import (
    _armor_entry,
    _potion_entry,
    _wand_entry,
    _weapon_entry,
    first_catalog_potion_display,
    first_catalog_potion_id,
    load_fixture_registry,
    write_item_fixtures,
    write_weighted_weapon_pool,
)


@pytest.fixture(autouse=True)
def _clear_item_registry_cache() -> None:
    reset_item_registry_cache()
    yield
    reset_item_registry_cache()


def test_load_item_registry_parses_stock_files() -> None:
    registry = load_item_registry()
    assert registry.schema_version == 1
    assert registry.weapons
    assert registry.armor
    assert registry.potions
    assert registry.wands
    sample = registry.weapons[0]
    assert registry.get_weapon(sample.id) is sample


def test_load_item_registry_parses_fixture_files(tmp_path) -> None:
    write_item_fixtures(
        tmp_path,
        weapons=[_weapon_entry("fixture_weapon", durability_max=55)],
        armor=[_armor_entry("fixture_armor", digestion_ac=3)],
        potions=[_potion_entry("fixture_potion", heal_amount=17, spawn_min=1)],
        wands=[],
    )
    registry = load_fixture_registry(tmp_path)
    assert registry.get_weapon("fixture_weapon").durability_max == 55
    assert registry.get_armor("fixture_armor").digestion_ac == 3
    assert registry.get_potion("fixture_potion").heal_amount == 17


def test_armor_requires_digestion_ac(tmp_path) -> None:
    armor_path = tmp_path / "armor.json"
    armor_path.write_text(
        '{"schema_version":1,"armor":[{"id":"x","display_name":"x","glyph":"[",'
        '"fg":[0,0,0],"examine":"x","ac_bonus":1,"durability_max":10,'
        '"spawn_weight":1,"spawn_min_depth":1,"spawn_max_depth":10,"abilities":[]}]}',
        encoding="utf-8",
    )
    with pytest.raises(ItemLoadError, match="digestion_ac"):
        load_item_registry(armor_path=armor_path)


def test_spawn_items_respects_depth_and_potion_minimum(tmp_path) -> None:
    write_item_fixtures(
        tmp_path,
        weapons=[_weapon_entry("shallow_weapon", spawn_min_depth=1, spawn_max_depth=2)],
        potions=[_potion_entry("guaranteed_potion", spawn_min=1)],
        wands=[_wand_entry("deep_wand", spawn_min_depth=3)],
    )
    registry = load_fixture_registry(tmp_path)
    world = Registry()
    game_map = generate_dungeon(40, 30, max_rooms=8, room_min_size=5, room_max_size=8, seed=42)
    spawned = spawn_items(
        world,
        game_map,
        5,
        5,
        floor_depth=1,
        rng=random.Random(0),
        registry=registry,
    )
    assert len(spawned) >= 1
    potions = [
        e for e in spawned if e.components[Item].item_id == "guaranteed_potion"
    ]
    assert len(potions) >= 1
    shallow_pool = _build_item_weighted_pool(registry, floor_depth=1)
    deep_pool = _build_item_weighted_pool(registry, floor_depth=3)
    assert any(item_id == "shallow_weapon" for _, item_id in shallow_pool)
    assert not any(item_id == "shallow_weapon" for _, item_id in deep_pool)
    assert any(category == ItemCategory.WAND for category, _ in deep_pool)


def test_spawn_items_caps_weighted_placements(tmp_path) -> None:
    registry = write_weighted_weapon_pool(tmp_path, count=12)
    world = Registry()
    game_map = generate_dungeon(60, 40, seed=99)
    pool = _build_item_weighted_pool(registry, floor_depth=1)
    assert len(pool) > MAX_FLOOR_ITEM_PLACEMENTS

    spawned = spawn_items(
        world,
        game_map,
        game_map.enter_xy[0],
        game_map.enter_xy[1],
        floor_depth=1,
        rng=random.Random(42),
        registry=registry,
    )
    assert len(spawned) <= MAX_FLOOR_ITEM_PLACEMENTS + 1
    weighted_weapons = [
        entity
        for entity in spawned
        if entity.components[Item].category == ItemCategory.WEAPON
    ]
    assert len(weighted_weapons) <= MAX_FLOOR_ITEM_PLACEMENTS


def test_floor_weapon_carries_durability(tmp_path) -> None:
    write_item_fixtures(
        tmp_path,
        weapons=[_weapon_entry("durability_weapon", durability_max=55)],
    )
    registry = load_fixture_registry(tmp_path)
    world = Registry()
    entity = spawn_item_entity(
        world,
        ItemCategory.WEAPON,
        "durability_weapon",
        3,
        4,
        registry=registry,
    )
    item = entity.components[Item]
    assert item.durability == 55
    assert item.charges is None


def test_pickup_assigns_earliest_letter() -> None:
    from tcod.ecs import Registry

    from src.message_log import MessageLog

    world = Registry()
    player = world.new_entity()
    player.tags.add(Player)
    player.components[Inventory] = Inventory()
    player.components[Position] = Position(1, 1)

    potion_id = first_catalog_potion_id()
    item = spawn_item_entity(world, ItemCategory.POTION, potion_id, 1, 1)
    log = MessageLog()
    assert try_pickup_floor_entity(world, player, item, log)
    assert player.components[Inventory].slots["a"] is not None
    assert player.components[Inventory].slots["a"].item_id == potion_id
    assert messages.item_pickup(first_catalog_potion_display(), "a") in log.lines()


def test_potion_stacking_reuses_slot() -> None:
    from tcod.ecs import Registry

    from src.message_log import MessageLog

    world = Registry()
    player = world.new_entity()
    player.tags.add(Player)
    player.components[Inventory] = Inventory()
    player.components[Position] = Position(2, 2)

    potion_id = first_catalog_potion_id()
    first = spawn_item_entity(world, ItemCategory.POTION, potion_id, 2, 2)
    second = spawn_item_entity(world, ItemCategory.POTION, potion_id, 2, 2)
    log = MessageLog()
    assert try_pickup_floor_entity(world, player, first, log)
    assert try_pickup_floor_entity(world, player, second, log)
    assert first not in list(world.Q.all_of(components=[Item]))
    assert second not in list(world.Q.all_of(components=[Item]))
    stack = player.components[Inventory].slots["a"]
    assert stack is not None
    assert stack.stack_count == 2
    assert first_empty_slot(player.components[Inventory]) == "b"


def test_first_empty_slot_tolerates_sparse_slot_map() -> None:
    """Depth-jump once cleared slots; missing letters must not KeyError on pickup."""
    inventory = Inventory(slots={"a": None, "b": None})
    assert first_empty_slot(inventory) == "a"
    inventory.slots["a"] = InventoryItemInstance(
        item_id="dagger",
        category=ItemCategory.WEAPON,
        durability=100,
    )
    # Missing 'c'..'z' still count as empty via .get
    assert first_empty_slot(inventory) == "b"
    inventory.slots["b"] = InventoryItemInstance(
        item_id="dagger",
        category=ItemCategory.WEAPON,
        durability=100,
    )
    assert first_empty_slot(inventory) == "c"


def test_auto_pickup_all_until_full_single_message() -> None:
    from tcod.ecs import Registry

    from src.components import InventoryItemInstance
    from src.message_log import MessageLog

    world = Registry()
    player = world.new_entity()
    player.tags.add(Player)
    inventory = Inventory()
    for letter in string.ascii_lowercase:
        inventory.slots[letter] = InventoryItemInstance(
            item_id="dagger",
            category=ItemCategory.WEAPON,
            durability=100,
        )
    player.components[Inventory] = inventory
    player.components[Position] = Position(0, 0)

    for _ in range(3):
        spawn_item_entity(world, ItemCategory.WEAPON, "dagger", 0, 0)

    log = MessageLog()
    pickup_all_items_at(world, player, 0, 0, log)
    assert log.lines().count(messages.inventory_full()) == 1
    assert len(floor_items_at(world, 0, 0)) == 3


def test_manual_pickup_single_item_no_modal() -> None:
    from tcod.ecs import Registry

    from src.message_log import MessageLog

    world = Registry()
    player = world.new_entity()
    player.tags.add(Player)
    player.components[Inventory] = Inventory()
    player.components[Position] = Position(4, 4)
    item = spawn_item_entity(world, ItemCategory.POTION, first_catalog_potion_id(), 4, 4)
    modal = GroundPickupModalState()
    log = MessageLog()
    opened = begin_manual_pickup(world, player, log, modal)
    assert not opened
    assert not modal.active
    assert item not in list(world.Q.all_of(components=[Item]))


def test_manual_pickup_multiple_opens_modal() -> None:
    from tcod.ecs import Registry

    from src.message_log import MessageLog

    world = Registry()
    player = world.new_entity()
    player.tags.add(Player)
    player.components[Inventory] = Inventory()
    player.components[Position] = Position(5, 5)
    from src.systems.inventory import item_registry

    reg = item_registry()
    spawn_item_entity(world, ItemCategory.POTION, reg.potions[0].id, 5, 5)
    spawn_item_entity(world, ItemCategory.WEAPON, reg.weapons[0].id, 5, 5)
    modal = GroundPickupModalState()
    log = MessageLog()
    assert begin_manual_pickup(world, player, log, modal)
    assert modal.active
    assert len(modal.item_entities) == 2


def test_engine_comma_manual_pickup() -> None:
    engine = GameEngine()
    engine.new_game(seed=99)
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    spawn_item_entity(
        engine.world,
        ItemCategory.WEAPON,
        "dagger",
        pos.x,
        pos.y,
        registry=load_item_registry(),
    )
    from tcod.event import Modifier, Scancode

    engine.handle_event(
        tcod.event.KeyDown(sym=KeySym.COMMA, scancode=Scancode.UNKNOWN, mod=Modifier.NONE),
    )
    assert player.components[Inventory].slots["d"] is not None
    assert player.components[Inventory].slots["d"].item_id == "dagger"