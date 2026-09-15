"""Ground examine: no false (wielded); multi-item listing; stack as one entry."""

from __future__ import annotations

from tcod.ecs import Registry

from src.components import Item, ItemCategory
from src.messages import examine_items_on_floor_header
from src.spawn import spawn_item_entity
from src.systems.examine import description_for_tile
from src.systems.item_modals import format_floor_item_detail_text
from src.systems.inventory import item_registry, reset_item_registry_cache


def test_floor_item_detail_never_says_wielded() -> None:
    reset_item_registry_cache()
    reg = item_registry()
    potion = next(p for p in reg.potions if p.id == "potion_of_blinking")
    text = format_floor_item_detail_text(
        Item(item_id=potion.id, category=ItemCategory.POTION, stack_count=1)
    )
    assert "(wielded)" not in text
    assert potion.display_name in text


def test_single_floor_stack_shows_quantity_not_wielded() -> None:
    reset_item_registry_cache()
    text = format_floor_item_detail_text(
        Item(item_id="healing_potion", category=ItemCategory.POTION, stack_count=3)
    )
    assert "(wielded)" not in text
    assert "Quantity: 3" in text


def test_multiple_floor_items_list_all_names() -> None:
    reset_item_registry_cache()
    world = Registry()
    spawn_item_entity(
        world, ItemCategory.POTION, "healing_potion", 5, 5, stack_count=2
    )
    spawn_item_entity(world, ItemCategory.WEAPON, "dagger", 5, 5)
    spawn_item_entity(
        world, ItemCategory.POTION, "potion_of_blinking", 5, 5, stack_count=1
    )
    text = description_for_tile(world, 5, 5)
    assert text.startswith(examine_items_on_floor_header())
    assert "2 healing potions" in text
    assert "dagger" in text
    assert "potion of blinking" in text
    assert "(wielded)" not in text
    # Multi-item mode is a name list, not full stat dump for each.
    assert "Damage:" not in text


def test_single_floor_item_keeps_detail_panel() -> None:
    reset_item_registry_cache()
    world = Registry()
    spawn_item_entity(world, ItemCategory.WEAPON, "dagger", 3, 3)
    text = description_for_tile(world, 3, 3)
    assert "dagger" in text
    assert "Damage:" in text
    assert "(wielded)" not in text
