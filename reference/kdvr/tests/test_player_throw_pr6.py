"""PR6: player throwable fire (f / F)."""

from __future__ import annotations

import random

import pytest
import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src import messages
from src.components import Alignment, Inventory, Position
from src.engine import GameEngine
from src.input_handlers import MODAL_ADVANCE_KEYS
from src.systems.inventory import STARTER_ROCK_STACK_COUNT, STARTER_THROWABLE_SLOT
from src.systems.item_modals import (
    InventoryModalMode,
    begin_quick_throw,
    begin_throw_pick,
    handle_throw_target_modal_event,
)
from src.systems.player_throw import (
    build_throw_target_tiles,
    confirm_player_throw,
    cycle_throw_target_index,
    pick_best_throwable_slot,
)
from src.systems.ai import spawn_test_npc
from tests.map_test_helpers import (
    ARENA_X,
    ARENA_Y,
    carve_horizontal_line,
    isolate_other_ais,
)


def _confirm_throw(engine: GameEngine) -> bool:
    assert engine.player is not None
    event = tcod.event.KeyDown(
        sym=next(iter(MODAL_ADVANCE_KEYS)),
        scancode=Scancode.UNKNOWN,
        mod=Modifier.NONE,
    )
    return handle_throw_target_modal_event(
        event,
        engine.player,
        engine.inventory_modal,
        engine.world,
        engine.game_map,
        engine.message_log,
        rng=random.Random(0),
        run_stats=engine.run_stats,
    )


def _keydown(sym: KeySym) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=Modifier.NONE)


def test_pick_best_throwable_prefers_earlier_slot_on_tie() -> None:
    from src.systems.inventory import make_throwable_instance

    inventory = Inventory()
    inventory.slots["a"] = make_throwable_instance("rock", stack_count=1)
    inventory.slots["c"] = make_throwable_instance("rock", stack_count=1)
    assert pick_best_throwable_slot(inventory) == "a"


def test_begin_quick_throw_opens_target_cursor_with_rocks() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 6)
    spawn_test_npc(
        engine.world,
        x=ARENA_X + 3,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    player.components[Position] = Position(ARENA_X, ARENA_Y)
    engine._update_fov()
    begin_quick_throw(
        player,
        engine.inventory_modal,
        engine.message_log,
        engine.world,
        game_map=engine.game_map,
    )
    assert engine.inventory_modal.mode is InventoryModalMode.THROW_TARGET
    assert engine.inventory_modal.throw_slot == STARTER_THROWABLE_SLOT
    assert len(engine.inventory_modal.throw_target_tiles) == 1
    assert engine.inventory_modal.throw_target_index == 0
    text = " ".join(entry.text for entry in engine.message_log.entries())
    assert messages.throw_at_which_target("rock") in text


def test_throw_at_empty_tile_shows_exact_message() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 6)
    player.components[Position] = Position(ARENA_X, ARENA_Y)
    engine._update_fov()
    assert not confirm_player_throw(
        engine.world,
        engine.game_map,
        player,
        STARTER_THROWABLE_SLOT,
        Position(ARENA_X + 2, ARENA_Y),
        engine.message_log,
        rng=random.Random(0),
    )
    text = " ".join(entry.text for entry in engine.message_log.entries())
    assert messages.throw_no_target_there() in text


def test_throw_blocked_by_good_ally_shows_exact_message() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 6)
    spawn_test_npc(
        engine.world,
        x=ARENA_X + 1,
        y=ARENA_Y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    wolf = spawn_test_npc(
        engine.world,
        x=ARENA_X + 3,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    player.components[Position] = Position(ARENA_X, ARENA_Y)
    engine._update_fov()
    begin_quick_throw(
        player,
        engine.inventory_modal,
        engine.message_log,
        engine.world,
        game_map=engine.game_map,
    )
    assert len(engine.inventory_modal.throw_target_tiles) == 1
    wolf_pos = wolf.components[Position]
    assert engine.inventory_modal.throw_target_tiles[0] == wolf_pos
    assert not _confirm_throw(engine)
    text = " ".join(entry.text for entry in engine.message_log.entries())
    assert messages.throw_path_blocked() in text


def test_successful_throw_consumes_stack() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 6)
    spawn_test_npc(
        engine.world,
        x=ARENA_X + 2,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    player.components[Position] = Position(ARENA_X, ARENA_Y)
    engine._update_fov()
    begin_quick_throw(
        player,
        engine.inventory_modal,
        engine.message_log,
        engine.world,
        game_map=engine.game_map,
    )
    assert engine.inventory_modal.throw_target_index == 0
    assert _confirm_throw(engine)
    stack = player.components[Inventory].slots[STARTER_THROWABLE_SLOT]
    assert stack is not None
    assert stack.stack_count == STARTER_ROCK_STACK_COUNT - 1


def test_throw_targets_sorted_near_to_far() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 8)
    far = spawn_test_npc(
        engine.world,
        x=ARENA_X + 5,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    near = spawn_test_npc(
        engine.world,
        x=ARENA_X + 2,
        y=ARENA_Y,
        species="slime",
        alignment=Alignment.EVIL,
    )
    player.components[Position] = Position(ARENA_X, ARENA_Y)
    engine._update_fov()
    tiles = build_throw_target_tiles(engine.world, engine.game_map, player)
    assert len(tiles) == 2
    assert tiles[0] == near.components[Position]
    assert tiles[1] == far.components[Position]


def test_throw_target_cycle_right_then_left_returns_to_nearest() -> None:
    assert cycle_throw_target_index(0, 3, forward=True) == 1
    assert cycle_throw_target_index(1, 3, forward=True) == 2
    assert cycle_throw_target_index(0, 3, forward=False) == 2
    assert cycle_throw_target_index(1, 3, forward=False) == 0


def test_throw_target_modal_right_then_left_returns_to_start() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 8)
    spawn_test_npc(
        engine.world,
        x=ARENA_X + 2,
        y=ARENA_Y,
        species="slime",
        alignment=Alignment.EVIL,
    )
    spawn_test_npc(
        engine.world,
        x=ARENA_X + 5,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    player.components[Position] = Position(ARENA_X, ARENA_Y)
    engine._update_fov()
    begin_quick_throw(
        player,
        engine.inventory_modal,
        engine.message_log,
        engine.world,
        game_map=engine.game_map,
    )
    start_index = engine.inventory_modal.throw_target_index
    handle_throw_target_modal_event(
        _keydown(KeySym.KP_6),
        player,
        engine.inventory_modal,
        engine.world,
        engine.game_map,
        engine.message_log,
    )
    handle_throw_target_modal_event(
        _keydown(KeySym.KP_4),
        player,
        engine.inventory_modal,
        engine.world,
        engine.game_map,
        engine.message_log,
    )
    assert engine.inventory_modal.throw_target_index == start_index


def test_throw_target_two_targets_oscillate_with_left_and_right() -> None:
    index = 0
    index = cycle_throw_target_index(index, 2, forward=True)
    assert index == 1
    index = cycle_throw_target_index(index, 2, forward=False)
    assert index == 0
    index = cycle_throw_target_index(index, 2, forward=False)
    assert index == 1


def test_nothing_to_throw_without_throwables(tmp_path) -> None:
    from tests.item_test_helpers import install_test_item_registry

    install_test_item_registry(tmp_path)
    engine = GameEngine()
    player = engine.player
    assert player is not None
    inventory = player.components[Inventory]
    inventory.slots[STARTER_THROWABLE_SLOT] = None
    assert not begin_quick_throw(
        player,
        engine.inventory_modal,
        engine.message_log,
        engine.world,
        game_map=engine.game_map,
    )
    text = " ".join(entry.text for entry in engine.message_log.entries())
    assert messages.nothing_to_throw() in text


def test_begin_throw_pick_opens_modal() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    assert begin_throw_pick(player, engine.inventory_modal, engine.message_log)
    assert engine.inventory_modal.mode is InventoryModalMode.THROW_PICK