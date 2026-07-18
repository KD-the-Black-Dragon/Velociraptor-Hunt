"""PR5: throwables data, registry, stacking, spawn pool, starter rocks."""

from __future__ import annotations

from pathlib import Path

import pytest
from tcod.ecs import Registry

from src.components import Inventory, Item, ItemCategory, Player
from src.data.item_loader import ItemLoadError, load_item_registry
from src.engine import GameEngine
from src.message_log import MessageLog
from src.spawn import spawn_item_entity, spawn_items
from src.systems.inventory import (
    STARTER_ROCK_STACK_COUNT,
    STARTER_THROWABLE_SLOT,
    apply_starter_loadout,
    find_throwable_stack_slot,
    inventory_has_room_for,
    item_registry,
    make_throwable_instance,
    reset_item_registry_cache,
    try_pickup_floor_entity,
)
from tests.item_test_helpers import (
    STARTER_THROWABLE_ID,
    _throwable_entry,
    clear_item_registry,
    install_test_item_registry,
    write_item_fixtures,
)


@pytest.fixture(autouse=True)
def _restore_item_registry() -> None:
    yield
    clear_item_registry()


def test_throwables_json_loads_rock() -> None:
    registry = load_item_registry()
    rock = registry.get_throwable("rock")
    assert rock.display_name == "rock"
    assert rock.min_damage == 1
    assert rock.max_damage == 2
    assert rock.fg == (190, 150, 90)


def test_throwable_min_damage_validation(tmp_path: Path) -> None:
    write_item_fixtures(
        tmp_path,
        throwables=[
            _throwable_entry("bad_rock", min_damage=5, max_damage=2),
        ],
        include_starter_defaults=False,
    )
    with pytest.raises(ItemLoadError, match="min_damage"):
        load_item_registry(
            weapons_path=tmp_path / "weapons.json",
            armor_path=tmp_path / "armor.json",
            potions_path=tmp_path / "potions.json",
            wands_path=tmp_path / "wands.json",
            throwables_path=tmp_path / "throwables.json",
        )


def test_starter_loadout_includes_five_rocks() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    stack = player.components[Inventory].slots[STARTER_THROWABLE_SLOT]
    assert stack is not None
    assert stack.item_id == STARTER_THROWABLE_ID
    assert stack.category == ItemCategory.THROWABLE
    assert stack.stack_count == STARTER_ROCK_STACK_COUNT


def test_apply_starter_loadout_idempotent_preserves_rock_stack() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    apply_starter_loadout(player)
    stack = player.components[Inventory].slots[STARTER_THROWABLE_SLOT]
    assert stack is not None
    assert stack.stack_count == STARTER_ROCK_STACK_COUNT


def test_throwable_pickup_stacks_in_inventory(tmp_path: Path) -> None:
    install_test_item_registry(tmp_path)
    world = Registry()
    player = world.new_entity()
    player.tags.add(Player)
    player.components[Inventory] = Inventory()
    apply_starter_loadout(player)

    first = spawn_item_entity(world, ItemCategory.THROWABLE, STARTER_THROWABLE_ID, 1, 1)
    second = spawn_item_entity(world, ItemCategory.THROWABLE, STARTER_THROWABLE_ID, 1, 1)
    log = MessageLog()
    assert try_pickup_floor_entity(world, player, first, log)
    assert try_pickup_floor_entity(world, player, second, log)

    slot = find_throwable_stack_slot(player.components[Inventory], STARTER_THROWABLE_ID)
    assert slot == STARTER_THROWABLE_SLOT
    stack = player.components[Inventory].slots[slot]
    assert stack is not None
    assert stack.stack_count == STARTER_ROCK_STACK_COUNT + 2


def test_inventory_has_room_for_matching_throwable_stack(tmp_path: Path) -> None:
    install_test_item_registry(tmp_path)
    inventory = Inventory()
    inventory.slots["a"] = make_throwable_instance("rock", stack_count=3)
    assert inventory_has_room_for(
        inventory,
        item_id="rock",
        category=ItemCategory.THROWABLE,
    )


def test_spawn_items_includes_throwables_on_depth_one(tmp_path: Path) -> None:
    install_test_item_registry(tmp_path)
    from src.map_gen import GameMap, Tile

    world = Registry()
    game_map = GameMap(20, 20)
    for y in range(20):
        for x in range(20):
            game_map.tiles[y, x] = Tile.FLOOR
    spawned = spawn_items(world, game_map, 10, 10, floor_depth=1, registry=item_registry())
    throwables = [
        entity
        for entity in spawned
        if entity.components[Item].category == ItemCategory.THROWABLE
    ]
    assert throwables