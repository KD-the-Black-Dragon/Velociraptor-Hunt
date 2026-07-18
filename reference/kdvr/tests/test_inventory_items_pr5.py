"""PR 5: wand evoke two-step modal, targeting, charges."""

from __future__ import annotations

from unittest.mock import patch

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src import messages
from src.components import Alignment, Fighter, Inventory, ItemCategory, Position
from src.message_log import ALERT_MESSAGE_FG
from src.spawn import spawn_item_entity
from src.engine import GameEngine
from src.systems.ai import spawn_test_npc
from src.systems.fov import update_fov
from src.systems.inventory import make_wand_instance, reset_item_registry_cache
from tests.item_test_helpers import (
    TEST_POTION_ID,
    TEST_WAND_DISPLAY,
    TEST_WAND_ID,
    install_test_item_registry,
)
from src.systems.item_modals import InventoryModalMode
from src.systems.wand_evoke import (
    build_evoke_targets,
    default_evoke_target_index,
    slots_for_wands_with_charges,
)

import pytest
from tests.map_test_helpers import carve_east_of, isolate_other_ais


@pytest.fixture(autouse=True)
def _isolated_item_registry(tmp_path) -> None:
    install_test_item_registry(tmp_path)
    yield
    reset_item_registry_cache()


def _test_wand(*, charges: int | None = None):
    return make_wand_instance(TEST_WAND_ID, charges=charges)


def _key(sym: KeySym, *, mod: Modifier = Modifier.NONE) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=mod)


def _place_evil_adjacent(engine: GameEngine):
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    carve_east_of(engine, pos, 2)
    wolf = spawn_test_npc(
        engine.world,
        x=pos.x + 1,
        y=pos.y,
        species="wolf",
        alignment=Alignment.EVIL,
        hp=50,
        evade=0,
        ac=0,
    )
    update_fov(engine.game_map, pos.x, pos.y)
    return wolf


def test_no_wands_message() -> None:
    engine = GameEngine()
    engine.handle_event(_key(KeySym.v))
    assert messages.no_wands() in engine.message_log.lines()
    assert not engine.inventory_modal.active


def test_wands_with_zero_charges_excluded_from_list() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    inventory = player.components[Inventory]
    inventory.slots["a"] = _test_wand(charges=0)
    assert not slots_for_wands_with_charges(inventory)


def test_default_evoke_target_is_nearest_evil() -> None:
    engine = GameEngine()
    engine.new_game(seed=12)
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    carve_east_of(engine, pos, 3)
    wolf = spawn_test_npc(
        engine.world,
        x=pos.x + 1,
        y=pos.y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    spawn_test_npc(
        engine.world,
        x=pos.x + 2,
        y=pos.y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    update_fov(engine.game_map, pos.x, pos.y)
    targets = build_evoke_targets(engine.world, engine.game_map, player, wand_range=5)
    index = default_evoke_target_index(targets, player)
    assert targets[index] is wolf


def test_evoke_target_step_has_no_modal_text() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Inventory].slots["a"] = _test_wand()
    _place_evil_adjacent(engine)

    engine.handle_event(_key(KeySym.v))
    engine.handle_event(_key(KeySym.a))

    from src.systems.item_modals import inventory_modal_text

    assert inventory_modal_text(engine.inventory_modal, player.components[Inventory]) == ""


def test_evoke_pick_opens_target_step() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Inventory].slots["a"] = _test_wand()
    _place_evil_adjacent(engine)

    engine.handle_event(_key(KeySym.v))
    engine.handle_event(_key(KeySym.a))

    assert engine.inventory_modal.mode == InventoryModalMode.EVOKE_TARGET
    assert engine.inventory_modal.evoke_wand_slot == "a"
    assert engine.inventory_modal.evoke_targets


def test_evoke_decrements_charges_and_consumes_turn() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    isolate_other_ais(engine)
    instance = _test_wand(charges=2)
    player.components[Inventory].slots["a"] = instance
    wolf = _place_evil_adjacent(engine)
    hp_before = wolf.components[Fighter].hp
    turns_before = engine.player_turn_count

    def _biased_randint(low: int, high: int) -> int:
        if high > low:
            return high
        return low

    with patch.object(engine.rng, "randint", side_effect=_biased_randint):
        engine.handle_event(_key(KeySym.v))
        engine.handle_event(_key(KeySym.a))
        engine.handle_event(_key(KeySym.RETURN))

    assert instance.charges == 1
    assert player.components[Inventory].slots["a"] is instance
    assert engine.player_turn_count == turns_before + 1
    assert not engine.inventory_modal.active
    fighter = wolf.components.get(Fighter)
    assert fighter is None or fighter.hp < hp_before


def test_evoke_at_zero_charges_removes_wand_with_red_break_message() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    instance = _test_wand(charges=1)
    player.components[Inventory].slots["a"] = instance
    _place_evil_adjacent(engine)

    with patch.object(engine.rng, "randint", return_value=0):
        engine.handle_event(_key(KeySym.v))
        engine.handle_event(_key(KeySym.a))
        engine.handle_event(_key(KeySym.RETURN))

    assert player.components[Inventory].slots["a"] is None
    assert messages.wand_breaks(TEST_WAND_DISPLAY) in engine.message_log.lines()
    alert_entries = [
        entry for entry in engine.message_log.entries() if entry.fg == ALERT_MESSAGE_FG
    ]
    assert any(messages.wand_breaks(TEST_WAND_DISPLAY) in entry.text for entry in alert_entries)


def test_evoke_escape_aborts_without_turn() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Inventory].slots["a"] = _test_wand()
    _place_evil_adjacent(engine)
    turns_before = engine.player_turn_count

    engine.handle_event(_key(KeySym.v))
    engine.handle_event(_key(KeySym.a))
    engine.handle_event(_key(KeySym.ESCAPE))

    assert not engine.inventory_modal.active
    assert engine.player_turn_count == turns_before


def test_no_valid_targets_when_only_good_in_range() -> None:
    engine = GameEngine()
    engine.new_game(seed=14)
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    carve_east_of(engine, pos, 2)
    spawn_test_npc(
        engine.world,
        x=pos.x + 1,
        y=pos.y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    update_fov(engine.game_map, pos.x, pos.y)
    player.components[Inventory].slots["a"] = _test_wand()
    turns_before = engine.player_turn_count

    engine.handle_event(_key(KeySym.v))
    engine.handle_event(_key(KeySym.a))

    assert messages.no_valid_targets_in_range() in engine.message_log.lines()
    assert not engine.inventory_modal.active
    assert engine.player_turn_count == turns_before


def test_not_the_best_target_rejects_good_npc() -> None:
    engine = GameEngine()
    engine.new_game(seed=15)
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    carve_east_of(engine, pos, 3)
    wolf = spawn_test_npc(
        engine.world,
        x=pos.x + 1,
        y=pos.y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    knight = spawn_test_npc(
        engine.world,
        x=pos.x + 2,
        y=pos.y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    update_fov(engine.game_map, pos.x, pos.y)
    player.components[Inventory].slots["a"] = _test_wand()
    turns_before = engine.player_turn_count

    engine.handle_event(_key(KeySym.v))
    engine.handle_event(_key(KeySym.a))
    targets = build_evoke_targets(engine.world, engine.game_map, player, wand_range=5)
    knight_index = targets.index(knight)
    engine.inventory_modal.evoke_target_index = knight_index
    engine.handle_event(_key(KeySym.RETURN))

    assert messages.not_the_best_target() in engine.message_log.lines()
    assert not engine.inventory_modal.active
    assert engine.player_turn_count == turns_before
    assert wolf.components[Fighter].hp == wolf.components[Fighter].max_hp


def test_npc_glyph_renders_over_floor_item_on_same_tile() -> None:
    import tcod.console
    from src.constants import SCREEN_HEIGHT, SCREEN_WIDTH
    from src.systems.render import render_entities, render_map

    from src.systems.inventory import item_registry

    engine = GameEngine()
    engine.new_game(seed=6)
    pos = Position(10, 10)
    spawn_item_entity(
        engine.world,
        ItemCategory.POTION,
        TEST_POTION_ID,
        pos.x,
        pos.y,
        registry=item_registry(),
    )
    spawn_test_npc(
        engine.world,
        x=pos.x,
        y=pos.y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    engine.game_map.explored[pos.y, pos.x] = True
    engine.game_map.visible[pos.y, pos.x] = True

    console = tcod.console.Console(SCREEN_WIDTH, SCREEN_HEIGHT, order="F")
    render_map(console, engine.game_map)
    render_entities(console, engine.world, engine.game_map, player=engine.player)

    ch = int(console.rgba[pos.x, pos.y]["ch"])
    assert chr(ch) == "k"