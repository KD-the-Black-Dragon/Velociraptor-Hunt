"""Tests for enhancements-1: wait, regen, stunned turn pass, TYUGHJBNM movement."""

from __future__ import annotations

from unittest.mock import patch

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src import messages
from src.components import AI, Fighter, Position, Stunned
from src.constants import NATURAL_REGEN_EVERY_N_PLAYER_TURNS
from src.engine import GameEngine
from src.events import on_player_turn_consumed
from src.input_handlers import DIRECTION_KEYS, WAIT_KEYS
from src.systems.combat import try_action


def _press(engine: GameEngine, sym: KeySym) -> bool:
    """Simulate KeyDown; return True if handle_event requests quit."""
    return engine.handle_event(
        tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=Modifier.NONE),
    )


def test_new_game_resets_turn_counter() -> None:
    engine = GameEngine()
    for _ in range(3):
        _press(engine, KeySym.KP_5)
    assert engine.player_turn_count == 3
    engine.new_game()
    assert engine.player_turn_count == 0


def test_wait_consumes_turn() -> None:
    engine = GameEngine()
    assert engine.player_turn_count == 0
    _press(engine, KeySym.KP_5)
    assert engine.player_turn_count == 1
    _press(engine, KeySym.PERIOD)
    assert engine.player_turn_count == 2
    _press(engine, KeySym.H)
    assert engine.player_turn_count == 3


def test_stunned_wait_uses_tired_message() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 0
    player.tags.add(Stunned)
    _press(engine, KeySym.H)
    assert messages.stunned_too_tired_to_move() in engine.message_log.lines()
    assert engine.player_turn_count == 1


def test_stunned_movement_consumes_turn() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    fighter = player.components[Fighter]
    fighter.hp = 0
    player.tags.add(Stunned)
    origin = player.components[Position]

    assert not try_action(engine.world, engine.game_map, player, (1, 0), engine.message_log)

    _press(engine, KeySym.RIGHT)
    assert player.components[Position] == origin
    assert engine.player_turn_count == 1
    assert messages.stunned_too_tired_to_move() in engine.message_log.lines()


def test_natural_regen_on_eighth_turn() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    fighter = player.components[Fighter]
    fighter.hp = 20
    with patch("src.engine_turn.run_monster_turns"):
        for _ in range(NATURAL_REGEN_EVERY_N_PLAYER_TURNS - 1):
            _press(engine, KeySym.KP_5)
        assert fighter.hp == 20
        _press(engine, KeySym.KP_5)
    assert fighter.hp == 21


def test_no_regen_at_max_hp() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    fighter = player.components[Fighter]
    assert fighter.hp == fighter.max_hp
    with patch("src.engine_turn.run_monster_turns"):
        for _ in range(NATURAL_REGEN_EVERY_N_PLAYER_TURNS):
            _press(engine, KeySym.KP_5)
    assert fighter.hp == fighter.max_hp


def test_regen_clears_stunned_with_message() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    fighter = player.components[Fighter]
    fighter.hp = 0
    player.tags.add(Stunned)
    with patch("src.engine_turn.run_monster_turns"):
        for _ in range(NATURAL_REGEN_EVERY_N_PLAYER_TURNS):
            _press(engine, KeySym.KP_5)
    assert fighter.hp == 1
    assert Stunned not in player.tags
    assert messages.no_longer_stunned() in engine.message_log.lines()


def test_keyboard_direction_y_moves_north() -> None:
    from src.systems.movement import can_move_to

    assert DIRECTION_KEYS[KeySym.Y] == (0, -1)
    for seed in range(200):
        engine = GameEngine()
        engine.new_game(seed=seed)
        player = engine.player
        assert player is not None
        pos = player.components[Position]
        direction = DIRECTION_KEYS[KeySym.Y]
        if not can_move_to(engine.world, engine.game_map, player, pos, direction):
            continue
        dest = pos + direction
        _press(engine, KeySym.Y)
        assert player.components[Position] == dest
        assert engine.player_turn_count == 1
        return
    raise AssertionError("No seed found with walkable north step for keyboard move test")


def test_wait_keys_defined() -> None:
    assert KeySym.KP_5 in WAIT_KEYS
    assert KeySym.PERIOD in WAIT_KEYS
    assert KeySym.H in WAIT_KEYS
    assert KeySym.H not in DIRECTION_KEYS


def test_player_turn_consumed_hook() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    seen: list[bool] = []

    def _callback(entity: object) -> None:
        assert entity is player
        seen.append(True)

    on_player_turn_consumed.append(_callback)
    try:
        _press(engine, KeySym.KP_5)
        assert seen == [True]
    finally:
        on_player_turn_consumed.remove(_callback)


def test_stunned_inventory_unchanged() -> None:
    from src.components import Inventory
    from src.systems.inventory import make_potion_instance

    engine = GameEngine()
    player = engine.player
    assert player is not None
    fighter = player.components[Fighter]
    fighter.hp = 0
    player.tags.add(Stunned)
    player.components[Inventory].slots["a"] = make_potion_instance()
    from src.systems.inventory import use_inventory_slot

    count_before = engine.player_turn_count
    assert use_inventory_slot(player, "a", engine.message_log)
    assert fighter.hp > 0
    assert engine.player_turn_count == count_before
    assert messages.stunned_too_tired_to_move() not in engine.message_log.lines()