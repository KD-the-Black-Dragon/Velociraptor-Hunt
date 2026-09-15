"""PR 2: inventory modals, drop, inspect, floor examine full reveal."""

from __future__ import annotations

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src import messages
from src.components import (
    AI,
    Engulfed,
    Fighter,
    Inventory,
    InventoryItemInstance,
    Item,
    ItemCategory,
    Position,
)
from src.engine import GameEngine
from src.spawn import spawn_item_entity
from src.systems.examine import description_for_tile
from src.systems.inventory import item_registry, make_potion_instance, reset_item_registry_cache
from src.systems.item_modals import (
    InventoryModalMode,
    _plural_display_name,
    drop_item_from_slot,
    inspect_list_modal_text,
)
from src.systems.render import _modal_lines_from_text, _modal_rows_with_alignment
from src.systems.vore import engulf_player
from tests.map_test_helpers import carve_east_of


def _key(sym: KeySym) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=Modifier.NONE)


def test_plural_display_name_for_stacked_potions() -> None:
    assert _plural_display_name("healing potion", 3) == "healing potions"
    assert _plural_display_name("healing potion", 1) == "healing potion"
    assert _plural_display_name("potion of blinking", 2) == "potions of blinking"
    assert _plural_display_name("throwing knife", 4) == "throwing knives"
    assert _plural_display_name("rock", 3) == "rocks"


def test_modal_list_rows_are_left_justified() -> None:
    engine = GameEngine()
    engine.new_game(seed=20)
    player = engine.player
    assert player is not None
    player.components[Inventory].slots["a"] = make_potion_instance(stack_count=3)
    text = inspect_list_modal_text(player.components[Inventory])
    rows = _modal_rows_with_alignment(text, max_inner=40)
    assert rows[0] == ("Inventory", "center")
    item_row = next(row for row in rows if row[0].startswith("a)"))
    assert item_row[1] == "left"
    assert rows[-1] == ("Esc: close", "center")


def test_inspect_list_modal_layout_and_plural() -> None:
    engine = GameEngine()
    engine.new_game(seed=20)
    player = engine.player
    assert player is not None
    instance = make_potion_instance(stack_count=3)
    display = item_registry().get_potion(instance.item_id).display_name
    player.components[Inventory].slots["a"] = instance
    text = inspect_list_modal_text(player.components[Inventory])
    assert f"a) 3 {_plural_display_name(display, 3)}" in text
    assert "\n\n" in text
    lines = _modal_lines_from_text(text, max_inner=40)
    assert lines[0] == "Inventory"
    assert lines[1] == ""
    assert f"a) 3 {_plural_display_name(display, 3)}" in lines
    assert lines[-1] == "Esc: close"


def test_item_detail_modal_compact_rows() -> None:
    engine = GameEngine()
    engine.new_game(seed=21)
    player = engine.player
    assert player is not None
    instance = make_potion_instance(stack_count=2)
    potion = item_registry().get_potion(instance.item_id)
    player.components[Inventory].slots["a"] = instance
    engine.handle_event(_key(KeySym.i))
    engine.handle_event(_key(KeySym.a))
    from src.systems.item_modals import inventory_modal_text

    text = inventory_modal_text(engine.inventory_modal, player.components[Inventory])
    assert "Quantity: 2" in text
    assert f"Heals {potion.heal_amount} HP" in text
    assert text.index(potion.display_name) < text.index("Quantity: 2") < text.index("Esc: back")
    # Stat rows are single-spaced; only section break before Esc: back is blank.
    body, _, footer = text.rpartition("\n\n")
    assert footer.startswith("Esc:")
    assert "\n\n" not in body
    lines = _modal_lines_from_text(text, max_inner=50)
    assert "" in lines  # blank before footer


def test_inspect_empty_inventory_message() -> None:
    engine = GameEngine()
    engine.new_game(seed=1)
    player = engine.player
    assert player is not None
    for letter in player.components[Inventory].slots:
        player.components[Inventory].slots[letter] = None
    engine.handle_event(_key(KeySym.i))
    assert messages.inventory_empty() in engine.message_log.lines()
    assert not engine.inventory_modal.active


def test_inspect_list_and_detail_escape_flow() -> None:
    engine = GameEngine()
    engine.new_game(seed=2)
    player = engine.player
    assert player is not None
    player.components[Inventory].slots["a"] = make_potion_instance(stack_count=2)

    engine.handle_event(_key(KeySym.i))
    assert engine.inventory_modal.active
    assert engine.inventory_modal.mode == InventoryModalMode.INSPECT_LIST

    engine.handle_event(_key(KeySym.a))
    assert engine.inventory_modal.mode == InventoryModalMode.INSPECT_DETAIL
    assert engine.inventory_modal.selected_slot == "a"

    engine.handle_event(_key(KeySym.ESCAPE))
    assert engine.inventory_modal.mode == InventoryModalMode.INSPECT_LIST

    engine.handle_event(_key(KeySym.ESCAPE))
    assert not engine.inventory_modal.active


def test_drop_item_spawns_on_floor() -> None:
    engine = GameEngine()
    engine.new_game(seed=3)
    player = engine.player
    assert player is not None
    player.components[Inventory].slots["b"] = InventoryItemInstance(
        item_id="dagger",
        category=ItemCategory.WEAPON,
        durability=50,
    )
    pos = player.components[Position]

    engine.handle_event(_key(KeySym.d))
    assert engine.inventory_modal.mode == InventoryModalMode.DROP
    engine.handle_event(_key(KeySym.b))

    assert player.components[Inventory].slots["b"] is None
    assert messages.item_dropped("dagger") in engine.message_log.lines()
    floor_items = [
        e
        for e in engine.world.Q.all_of(components=[Item])
        if e.components[Position] == pos
    ]
    assert len(floor_items) == 1
    dropped = floor_items[0].components[Item]
    assert dropped.item_id == "dagger"
    assert dropped.durability == 50


def test_drop_potion_reduces_stack() -> None:
    engine = GameEngine()
    engine.new_game(seed=4)
    player = engine.player
    assert player is not None
    player.components[Inventory].slots["c"] = make_potion_instance(stack_count=3)

    drop_item_from_slot(engine.world, player, "c", engine.message_log)
    stack = player.components[Inventory].slots["c"]
    assert stack is not None
    assert stack.stack_count == 2


def test_nothing_to_drop_when_empty() -> None:
    engine = GameEngine()
    engine.new_game(seed=5)
    player = engine.player
    assert player is not None
    for letter in player.components[Inventory].slots:
        player.components[Inventory].slots[letter] = None
    engine.handle_event(_key(KeySym.d))
    assert messages.nothing_to_drop() in engine.message_log.lines()
    assert not engine.inventory_modal.active


def test_global_letter_key_no_longer_quaffs() -> None:
    engine = GameEngine()
    engine.new_game(seed=6)
    player = engine.player
    assert player is not None
    fighter = player.components[Fighter]
    fighter.hp = 5
    player.components[Inventory].slots["a"] = make_potion_instance()
    turns_before = engine.player_turn_count
    engine.handle_event(_key(KeySym.a))
    assert fighter.hp == 5
    assert engine.player_turn_count == turns_before


def test_examine_potion_shows_full_stats(tmp_path) -> None:
    from tests.item_test_helpers import (
        _potion_entry,
        install_item_registry,
        load_fixture_registry,
        write_item_fixtures,
    )

    write_item_fixtures(
        tmp_path,
        potions=[
            _potion_entry(
                "floor_potion",
                display_name="floor potion",
                heal_amount=17,
            )
        ],
    )
    registry = load_fixture_registry(tmp_path)
    install_item_registry(registry)
    engine = GameEngine()
    engine.new_game(seed=7)
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    spawn_item_entity(
        engine.world,
        ItemCategory.POTION,
        "floor_potion",
        pos.x,
        pos.y,
        registry=registry,
    )
    text = description_for_tile(engine.world, pos.x, pos.y)
    assert "Heals 17 HP" in text
    assert "floor potion" in text


def test_pack_blocked_for_inspect_while_engulfed() -> None:
    engine = GameEngine()
    engine.new_game(seed=8)
    player = engine.player
    assert player is not None
    wolf = next(iter(engine.world.Q.all_of(components=[AI, Fighter, Position])))
    pos = player.components[Position]
    carve_east_of(engine, pos, 2)
    wolf.components[Position] = Position(pos.x + 1, pos.y)
    engulf_player(engine.world, player, wolf, engine.message_log, narrative_type="OV")
    assert Engulfed in player.tags
    engine.handle_event(_key(KeySym.i))
    assert messages.engulfed_pack_blocked() in engine.message_log.lines()
    assert not engine.inventory_modal.active