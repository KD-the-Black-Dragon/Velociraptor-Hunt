"""PR 4: quaff potions from data, player glyph over floor items."""

from __future__ import annotations

import tcod.console
import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src import messages
from src.components import Fighter, Inventory, Position, Stunned
from src.constants import MAP_HEIGHT, SCREEN_HEIGHT, SCREEN_WIDTH
from src.engine import GameEngine
from src.systems.inventory import (
    item_registry,
    make_potion_instance,
    make_weapon_instance,
    quaff_potion_from_slot,
    reset_item_registry_cache,
)
from tests.item_test_helpers import (
    _potion_entry,
    install_item_registry,
    load_fixture_registry,
    write_item_fixtures,
)
from src.systems.item_modals import drop_item_from_slot, quaff_list_modal_text

import pytest


@pytest.fixture(autouse=True)
def _clear_item_registry_cache() -> None:
    reset_item_registry_cache()
    yield
    reset_item_registry_cache()


def _key(sym: KeySym, *, mod: Modifier = Modifier.NONE) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=mod)


def test_quaff_heals_from_potion_definition(tmp_path) -> None:
    write_item_fixtures(
        tmp_path,
        potions=[_potion_entry("heal_test", display_name="heal test", heal_amount=17)],
    )
    registry = load_fixture_registry(tmp_path)
    install_item_registry(registry)
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 10
    player.components[Inventory].slots["a"] = make_potion_instance("heal_test")

    engine.handle_event(_key(KeySym.q))
    engine.handle_event(_key(KeySym.a))

    assert player.components[Fighter].hp == 27
    assert player.components[Inventory].slots["a"] is None
    assert messages.potion_heal("heal test", 17) in engine.message_log.lines()


def test_quaff_consumes_turn() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Inventory].slots["a"] = make_potion_instance()
    turns_before = engine.player_turn_count

    engine.handle_event(_key(KeySym.q))
    engine.handle_event(_key(KeySym.a))

    assert engine.player_turn_count == turns_before + 1
    assert not engine.inventory_modal.active


def test_quaff_at_full_health_still_consumes_turn() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    fighter = player.components[Fighter]
    fighter.hp = fighter.max_hp
    instance = make_potion_instance()
    potion = item_registry().get_potion(instance.item_id)
    player.components[Inventory].slots["a"] = instance
    turns_before = engine.player_turn_count

    engine.handle_event(_key(KeySym.q))
    engine.handle_event(_key(KeySym.a))

    assert messages.potion_no_effect(potion.display_name) in engine.message_log.lines()
    assert player.components[Inventory].slots["a"] is None
    assert engine.player_turn_count == turns_before + 1


def test_stunned_player_can_quaff_via_modal() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    fighter = player.components[Fighter]
    fighter.hp = 0
    player.tags.add(Stunned)
    player.components[Inventory].slots["a"] = make_potion_instance()

    engine.handle_event(_key(KeySym.q))
    engine.handle_event(_key(KeySym.a))

    assert fighter.hp > 0
    assert messages.stunned_too_tired_to_move() not in engine.message_log.lines()


def test_no_potions_message() -> None:
    engine = GameEngine()
    engine.handle_event(_key(KeySym.q))
    assert messages.no_potions() in engine.message_log.lines()
    assert not engine.inventory_modal.active


def test_quaff_modal_lists_potions_only() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    inventory = player.components[Inventory]
    potion_instance = make_potion_instance()
    weapon_instance = make_weapon_instance()
    inventory.slots["a"] = potion_instance
    inventory.slots["b"] = weapon_instance
    potion = item_registry().get_potion(potion_instance.item_id)
    weapon = item_registry().get_weapon(weapon_instance.item_id)

    text = quaff_list_modal_text(inventory)
    assert f"a) {potion.display_name}" in text
    assert weapon.display_name not in text


def test_quaff_stacked_potion_decrements_stack() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    instance = make_potion_instance(stack_count=3)
    player.components[Inventory].slots["a"] = instance

    assert quaff_potion_from_slot(player, "a", engine.message_log)
    assert instance.stack_count == 2
    assert player.components[Inventory].slots["a"] is instance


def test_player_glyph_renders_over_floor_item_on_same_tile() -> None:
    engine = GameEngine()
    engine.new_game(seed=5)
    player = engine.player
    assert player is not None
    player.components[Inventory].slots["a"] = make_potion_instance()
    drop_item_from_slot(engine.world, player, "a", engine.message_log)
    pos = player.components[Position]

    from tests.ui_test_helpers import render_engine_frame, root_char_at_world_for_engine

    console = render_engine_frame(engine)
    assert root_char_at_world_for_engine(engine, console, pos.x, pos.y) == "@"