"""Tests for autoexplore (grave / backtick key)."""

from __future__ import annotations

from unittest.mock import patch

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src import messages
from src.components import (
    AI,
    Engulfed,
    Fighter,
    Position,
    Stunned,
)
from src.components import Alignment
from src.components import ItemCategory
from src.engine import GameEngine
from src.events import fire_player_combat_targeted
from src.input_handlers import AUTOEXPLORE_KEY
from src.map_gen import GameMap, Tile
from src.spawn import spawn_item_entity
from src.systems.ai import spawn_test_npc
from src.systems.inventory import floor_items_at
from src.systems.autoexplore import (
    AutoexploreEndReason,
    AutoexploreSession,
    begin_autoexplore,
    try_autoexplore,
)
from src.message_log import MessageCategory


def _press(engine: GameEngine, sym: KeySym) -> None:
    if engine.autoexplore_in_progress():
        engine.cancel_autoexplore()
    if engine.rest_in_progress():
        engine.cancel_rest()
    engine.handle_event(
        tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=Modifier.NONE),
    )


def _clear_npcs(engine: GameEngine) -> None:
    for entity in list(engine.world.Q.all_of(components=[AI])):
        if entity is engine.player:
            continue
        entity.clear()


def _danger_lines(engine: GameEngine) -> list[str]:
    return [
        entry.text
        for entry in engine.message_log.entries()
        if entry.category is MessageCategory.DANGER
    ]


def _caution_lines(engine: GameEngine) -> list[str]:
    return [
        entry.text
        for entry in engine.message_log.entries()
        if entry.category is MessageCategory.CAUTION
    ]


def _corridor_map(*, width: int = 20, height: int = 9) -> GameMap:
    game_map = GameMap(width, height)
    game_map.tiles[:, :] = Tile.WALL
    mid_y = height // 2
    game_map.tiles[mid_y, 1 : width - 1] = Tile.FLOOR
    game_map.enter_xy = (2, mid_y)
    return game_map


def test_autoexplore_key_is_grave() -> None:
    assert AUTOEXPLORE_KEY == KeySym.GRAVE


def test_begin_blocked_engulfed() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.tags.add(Engulfed)
    player.components[Fighter].hp = 20

    session = begin_autoexplore(
        player=player,
        game_map=engine.game_map,
        world=engine.world,
        message_log=engine.message_log,
    )

    assert session is None
    assert messages.autoexplore_engulfed() in _danger_lines(engine)


def test_begin_blocked_visible_evil() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    fighter = player.components[Fighter]
    fighter.hp = fighter.max_hp
    pos = player.components[Position]
    spawn_test_npc(
        engine.world,
        x=pos.x + 1,
        y=pos.y,
        species="wolf",
        alignment=Alignment.EVIL,
        species_id="wolf",
    )
    engine._update_fov()

    session = begin_autoexplore(
        player=player,
        game_map=engine.game_map,
        world=engine.world,
        message_log=engine.message_log,
    )

    assert session is None
    assert messages.autoexplore_enemy_in_sight() in _danger_lines(engine)


def test_begin_blocked_below_half_hp() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    player = engine.player
    assert player is not None
    fighter = player.components[Fighter]
    fighter.max_hp = 10
    fighter.hp = 4

    session = begin_autoexplore(
        player=player,
        game_map=engine.game_map,
        world=engine.world,
        message_log=engine.message_log,
    )

    assert session is None
    assert messages.autoexplore_too_injured() in _danger_lines(engine)


def test_begin_allowed_at_half_hp() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    player = engine.player
    assert player is not None
    fighter = player.components[Fighter]
    fighter.max_hp = 10
    fighter.hp = 5

    session = begin_autoexplore(
        player=player,
        game_map=engine.game_map,
        world=engine.world,
        message_log=engine.message_log,
    )

    assert session is not None
    assert messages.autoexplore_start() in engine.message_log.lines()


def test_begin_blocked_stunned() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    player = engine.player
    assert player is not None
    fighter = player.components[Fighter]
    fighter.hp = fighter.max_hp
    player.tags.add(Stunned)

    session = begin_autoexplore(
        player=player,
        game_map=engine.game_map,
        world=engine.world,
        message_log=engine.message_log,
    )

    assert session is None
    assert messages.stunned_too_tired_to_move() in _danger_lines(engine)


def test_start_message_via_key() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = player.components[Fighter].max_hp

    _press(engine, AUTOEXPLORE_KEY)

    assert engine.autoexplore_in_progress()
    assert messages.autoexplore_start() in engine.message_log.lines()


def test_complete_on_fully_explored_floor() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    player = engine.player
    assert player is not None
    fighter = player.components[Fighter]
    fighter.hp = fighter.max_hp
    engine.game_map.reveal_all()

    result = try_autoexplore(
        engine=engine,
        consume_turn=lambda: None,
    )

    assert result.end_reason == AutoexploreEndReason.COMPLETE
    assert messages.autoexplore_complete() in engine.message_log.lines()


def test_picks_up_known_item_on_explored_tile() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    player = engine.player
    assert player is not None
    fighter = player.components[Fighter]
    fighter.hp = fighter.max_hp

    game_map = _corridor_map()
    mid_y = game_map.height // 2
    player.components[Position] = Position(2, mid_y)
    item_x = 6
    spawn_item_entity(
        engine.world,
        ItemCategory.WEAPON,
        "dagger",
        item_x,
        mid_y,
    )
    game_map.explored[mid_y, item_x] = True
    engine.game_map = game_map
    engine._update_fov()

    with patch("src.engine_turn.run_monster_turns"):
        result = try_autoexplore(
            engine=engine,
            consume_turn=engine._consume_player_turn,
        )

    assert result.consumed_turns >= 1
    assert len(floor_items_at(engine.world, item_x, mid_y)) == 0


def _autoexplore_corridor_engine() -> GameEngine:
    engine = GameEngine()
    _clear_npcs(engine)
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = player.components[Fighter].max_hp
    game_map = _corridor_map()
    mid_y = game_map.height // 2
    player.components[Position] = Position(2, mid_y)
    game_map.explored[mid_y, 2] = True
    engine.game_map = game_map
    engine._update_fov()
    return engine


def test_danger_interrupt_visible_evil() -> None:
    engine = _autoexplore_corridor_engine()
    player = engine.player
    assert player is not None

    def consume() -> None:
        pos = player.components[Position]
        spawn_test_npc(
            engine.world,
            x=pos.x + 1,
            y=pos.y,
            species="wolf",
            alignment=Alignment.EVIL,
            species_id="wolf",
        )
        engine._update_fov()
        engine._consume_player_turn()

    with patch("src.engine_turn.run_monster_turns"):
        result = try_autoexplore(engine=engine, consume_turn=consume)

    assert result.end_reason == AutoexploreEndReason.DANGER
    assert messages.rest_danger_approaches() in _caution_lines(engine)


def test_attack_interrupt() -> None:
    engine = _autoexplore_corridor_engine()

    def consume() -> None:
        fire_player_combat_targeted()
        engine._consume_player_turn()

    with patch("src.engine_turn.run_monster_turns"):
        result = try_autoexplore(engine=engine, consume_turn=consume)

    assert result.end_reason == AutoexploreEndReason.ATTACK
    assert messages.rest_interrupted_by_attack() in _caution_lines(engine)


def test_manual_cancel_silent() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = player.components[Fighter].max_hp
    engine.autoexplore_session = AutoexploreSession(active=True)
    engine.message_log.clear()

    engine.cancel_autoexplore()

    assert not engine.autoexplore_in_progress()
    assert messages.autoexplore_complete() not in engine.message_log.lines()
    assert messages.rest_danger_approaches() not in engine.message_log.lines()