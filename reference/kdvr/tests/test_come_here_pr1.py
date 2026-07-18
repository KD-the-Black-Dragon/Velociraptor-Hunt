"""PR1: Come here! shout plumbing (flags + cooldown; no AI pathing)."""

from __future__ import annotations

import tcod.event
from tcod.event import KeySym

from src.components import AIState, Engulfed, Position
from src.engine import GameEngine
from src.input_handlers import COME_HERE_KEY
from src.messages import (
    come_here_engulfed_fizzle,
    come_here_hoarse,
    come_here_shout,
)
from src.spawn import spawn_entity_by_id
from src.systems.come_here import (
    COME_HERE_COOLDOWN_TURNS,
    ComeHereResult,
    good_allies_in_player_fov,
    try_come_here_shout,
)
from src.systems.fov import update_fov
from tests.map_test_helpers import isolate_other_ais


def _key(sym: KeySym) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=None, mod=0)


def _place_knight_in_fov(engine: GameEngine):
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    knight = spawn_entity_by_id(engine.world, "knight", pos.x + 1, pos.y)
    update_fov(engine.game_map, pos.x, pos.y)
    return knight


def test_come_here_key_is_main_keyboard_one_not_numpad() -> None:
    assert COME_HERE_KEY is KeySym.N1
    assert COME_HERE_KEY is not KeySym.KP_1


def test_shout_sets_come_here_on_good_in_fov() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.new_game(seed=11)
    knight = _place_knight_in_fov(engine)
    player = engine.player
    assert player is not None

    result, last = try_come_here_shout(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        player_turn_count=engine.player_turn_count,
        last_come_here_turn=engine.last_come_here_turn,
    )
    assert result is ComeHereResult.SHOUTED
    assert last == engine.player_turn_count
    assert knight.components[AIState].come_here is True
    assert come_here_shout() in engine.message_log.lines()


def test_shout_skips_good_outside_fov() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.new_game(seed=12)
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    far = spawn_entity_by_id(engine.world, "knight", pos.x + 40, pos.y)
    update_fov(engine.game_map, pos.x, pos.y)
    assert far not in good_allies_in_player_fov(engine.world, engine.game_map, player)

    try_come_here_shout(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        player_turn_count=0,
        last_come_here_turn=-1,
    )
    state = far.components.get(AIState)
    assert state is None or state.come_here is False


def test_cooldown_blocks_spam_without_turn() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.new_game(seed=13)
    player = engine.player
    assert player is not None
    turns_before = engine.player_turn_count

    engine.handle_event(_key(COME_HERE_KEY))
    assert engine.player_turn_count == turns_before + 1
    assert come_here_shout() in engine.message_log.lines()

    turns_after = engine.player_turn_count
    engine.handle_event(_key(COME_HERE_KEY))
    assert engine.player_turn_count == turns_after  # no turn
    assert come_here_hoarse() in engine.message_log.lines()


def test_cooldown_expires_after_four_turns() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.new_game(seed=14)
    player = engine.player
    assert player is not None
    _place_knight_in_fov(engine)

    engine.handle_event(_key(COME_HERE_KEY))
    engine.player_turn_count += COME_HERE_COOLDOWN_TURNS
    # last shout was at turn T; after +4, elapsed >= 4 → allow
    result, _ = try_come_here_shout(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        player_turn_count=engine.player_turn_count,
        last_come_here_turn=engine.last_come_here_turn,
    )
    assert result is ComeHereResult.SHOUTED
    assert COME_HERE_COOLDOWN_TURNS == 4


def test_engulfed_fizzle_no_flags_consumes_turn() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.new_game(seed=15)
    player = engine.player
    assert player is not None
    knight = _place_knight_in_fov(engine)
    player.tags.add(Engulfed)
    turns = engine.player_turn_count

    engine.handle_event(_key(COME_HERE_KEY))
    assert engine.player_turn_count == turns + 1
    assert come_here_engulfed_fizzle() in engine.message_log.lines()
    assert come_here_shout() not in engine.message_log.lines()
    state = knight.components.get(AIState)
    assert state is None or state.come_here is False


def test_aistate_come_here_defaults_false_on_spawn() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.new_game(seed=16)
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    knight = spawn_entity_by_id(engine.world, "knight", pos.x + 2, pos.y)
    state = knight.components.get(AIState)
    assert state is not None
    assert state.come_here is False
