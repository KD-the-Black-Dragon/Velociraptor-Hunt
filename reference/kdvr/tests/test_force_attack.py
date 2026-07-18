"""Tests for Ctrl+direction force-attack."""

from __future__ import annotations

import random
from unittest.mock import patch

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src import messages
from src.components import Alignment, Fighter, Position, Stunned
from src.engine import GameEngine
from src.input_handlers import is_ctrl_direction
from src.map_gen import Tile
from src.systems.ai import spawn_test_npc
from src.systems.combat import try_force_attack

from tests.entity_test_helpers import spawn_fixture_wolf
from tests.map_test_helpers import (
    ARENA_X,
    ARENA_Y,
    carve_floor_rect,
    ensure_adjacent_floor,
    isolate_other_ais,
)


def _ctrl_press(engine: GameEngine, sym: KeySym) -> None:
    engine.handle_event(
        tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=Modifier.CTRL),
    )


def _setup_player_east_of_wolf() -> tuple[GameEngine, object, int]:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    isolate_other_ais(engine)
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X + 2, ARENA_Y)
    player.components[Position] = Position(ARENA_X, ARENA_Y)
    wolf = spawn_fixture_wolf(engine.world, ARENA_X + 1, ARENA_Y)
    wolf_hp = wolf.components[Fighter].hp
    return engine, wolf, wolf_hp


def test_is_ctrl_direction_detects_movement_keys() -> None:
    event = tcod.event.KeyDown(
        sym=KeySym.RIGHT,
        scancode=Scancode.UNKNOWN,
        mod=Modifier.CTRL,
    )
    assert is_ctrl_direction(event) == (1, 0)
    plain = tcod.event.KeyDown(
        sym=KeySym.RIGHT,
        scancode=Scancode.UNKNOWN,
        mod=Modifier.NONE,
    )
    assert is_ctrl_direction(plain) is None


def test_hits_adjacent_evil_without_moving() -> None:
    engine, wolf, wolf_hp = _setup_player_east_of_wolf()
    player = engine.player
    assert player is not None
    pos_before = player.components[Position]

    with patch("src.systems.combat.resolve_attack", return_value=(True, 5)):
        assert try_force_attack(
            engine.world,
            engine.game_map,
            player,
            (1, 0),
            engine.message_log,
            rng=random.Random(0),
        )

    assert player.components[Position] == pos_before
    assert wolf.components[Fighter].hp < wolf_hp


def test_empty_air_consumes_turn() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    isolate_other_ais(engine)
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X + 1, ARENA_Y)
    player.components[Position] = Position(ARENA_X, ARENA_Y)

    assert try_force_attack(
        engine.world,
        engine.game_map,
        player,
        (1, 0),
        engine.message_log,
    )
    assert messages.attack_empty_air() in engine.message_log.lines()


def test_does_not_swap_good() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    isolate_other_ais(engine)
    player_pos = Position(ARENA_X, ARENA_Y)
    knight_pos = ensure_adjacent_floor(engine, player_pos, (1, 0))
    player.components[Position] = player_pos
    knight = spawn_test_npc(
        engine.world,
        x=knight_pos.x,
        y=knight_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
    )

    assert try_force_attack(
        engine.world,
        engine.game_map,
        player,
        (1, 0),
        engine.message_log,
    )

    assert knight.components[Position] == knight_pos
    assert player.components[Position] == player_pos
    assert messages.attack_empty_air() in engine.message_log.lines()
    assert messages.player_swap_places("knight") not in engine.message_log.lines()


def test_does_not_open_door() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    isolate_other_ais(engine)
    player_pos = Position(ARENA_X, ARENA_Y)
    dest = ensure_adjacent_floor(engine, player_pos, (1, 0))
    player.components[Position] = player_pos
    engine.game_map.tiles[dest.y, dest.x] = Tile.DOOR_CLOSED

    assert try_force_attack(
        engine.world,
        engine.game_map,
        player,
        (1, 0),
        engine.message_log,
    )

    assert engine.game_map.tiles[dest.y, dest.x] == Tile.DOOR_CLOSED
    assert messages.attack_empty_air() in engine.message_log.lines()
    assert messages.door_opened() not in engine.message_log.lines()


def test_stunned_empty_air() -> None:
    engine, wolf, wolf_hp = _setup_player_east_of_wolf()
    player = engine.player
    assert player is not None
    player.tags.add(Stunned)

    assert try_force_attack(
        engine.world,
        engine.game_map,
        player,
        (1, 0),
        engine.message_log,
    )

    assert messages.stunned_too_tired_to_move() in engine.message_log.lines()
    assert wolf.components[Fighter].hp == wolf_hp
    assert messages.attack_empty_air() not in engine.message_log.lines()


def test_engulfed_routes_to_struggle() -> None:
    from src.components import Engulfed
    from src.systems.vore import engulf_player
    from tests.map_test_helpers import carve_east_of, first_wolf

    engine = GameEngine()
    player = engine.player
    assert player is not None
    wolf = first_wolf(engine)
    pos = player.components[Position]
    carve_east_of(engine, pos, 2)
    wolf.components[Position] = Position(pos.x + 1, pos.y)
    engulf_player(engine.world, player, wolf, engine.message_log, narrative_type="OV")
    assert Engulfed in player.tags
    player.tags.discard(Stunned)
    turns_before = engine.player_turn_count

    with patch("src.engine_input.try_struggle") as struggle:
        struggle.return_value = True
        _ctrl_press(engine, KeySym.UP)

    struggle.assert_called_once()
    assert engine.player_turn_count == turns_before + 1
    assert messages.attack_empty_air() not in engine.message_log.lines()