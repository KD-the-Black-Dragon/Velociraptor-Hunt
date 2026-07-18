"""PR 6: examine mode, engulfed block, Ctrl+Q quit, Escape cancel."""

from __future__ import annotations

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src import messages
from src.components import Engulfed, ExamineDescription, Item, Position
from src.engine import GameEngine
from src.input_handlers import EXAMINE_KEY
from src.spawn import WOLF_EXAMINE_DESCRIPTION
from src.systems.vore import engulf_player

from tests.map_test_helpers import carve_east_of, ensure_adjacent_floor, first_wolf


def _press(engine: GameEngine, sym: KeySym, *, mod: Modifier = Modifier.NONE):
    return engine.handle_event(
        tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=mod),
    )


def _ctrl_q(engine: GameEngine):
    return _press(engine, KeySym.Q, mod=Modifier.CTRL)


def test_examine_enter_does_not_consume_turn() -> None:
    engine = GameEngine()
    turns_before = engine.player_turn_count
    _press(engine, EXAMINE_KEY)
    assert engine.examine_state.active
    assert engine.examine_state.cursor == engine.player.components[Position]
    assert engine.player_turn_count == turns_before


def test_examine_cursor_moves_not_player() -> None:
    engine = GameEngine()
    start = engine.player.components[Position]
    _press(engine, EXAMINE_KEY)
    _press(engine, KeySym.RIGHT)
    assert engine.examine_state.cursor == Position(start.x + 1, start.y)
    assert engine.player.components[Position] == start


def test_examine_wolf_description_in_modal_not_log() -> None:
    engine = GameEngine()
    player = engine.player
    wolf = first_wolf(engine)
    wpos = wolf.components[Position]
    ensure_adjacent_floor(engine, wpos, (-1, 0))
    player.components[Position] = Position(wpos.x - 1, wpos.y)
    _press(engine, EXAMINE_KEY)
    _press(engine, KeySym.RIGHT)
    _press(engine, KeySym.RETURN)
    assert engine.examine_state.showing_description
    assert engine.examine_state.description_text == WOLF_EXAMINE_DESCRIPTION
    assert WOLF_EXAMINE_DESCRIPTION not in engine.message_log.lines()


def test_examine_empty_floor_message() -> None:
    engine = GameEngine()
    _press(engine, EXAMINE_KEY)
    _press(engine, KeySym.RETURN)
    assert engine.examine_state.description_text == messages.examine_nothing_here()


def test_examine_potion_on_floor(tmp_path) -> None:
    from src.components import ItemCategory
    from src.spawn import spawn_item_entity
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
                "examine_potion",
                display_name="examine potion",
                heal_amount=17,
            )
        ],
    )
    registry = load_fixture_registry(tmp_path)
    install_item_registry(registry)
    engine = GameEngine()
    player = engine.player
    assert player is not None
    start = player.components[Position]
    carve_east_of(engine, start, 2)
    isolated = Position(start.x + 1, start.y)
    spawn_item_entity(
        engine.world,
        ItemCategory.POTION,
        "examine_potion",
        isolated.x,
        isolated.y,
        registry=registry,
    )
    engine.examine_state.enter(isolated)
    _press(engine, KeySym.RETURN)
    assert "Heals 17 HP" in engine.examine_state.description_text
    assert "examine potion" in engine.examine_state.description_text


def test_examine_engulfed_blocked() -> None:
    engine = GameEngine()
    player = engine.player
    wolf = first_wolf(engine)
    pos = player.components[Position]
    carve_east_of(engine, pos, 2)
    wolf.components[Position] = Position(pos.x + 1, pos.y)
    engulf_player(
        engine.world, player, wolf, engine.message_log, narrative_type="OV"
    )
    turns_before = engine.player_turn_count
    _press(engine, EXAMINE_KEY)
    assert not engine.examine_state.active
    assert messages.examine_engulfed_cant_see() in engine.message_log.lines()
    assert engine.player_turn_count == turns_before


def test_escape_cancels_examine_not_quit() -> None:
    from src.engine import EngineEventResult

    engine = GameEngine()
    _press(engine, EXAMINE_KEY)
    assert engine.examine_state.active
    assert _press(engine, KeySym.ESCAPE) is EngineEventResult.CONTINUE
    assert not engine.examine_state.active


def test_escape_dismisses_description_back_to_cursor() -> None:
    engine = GameEngine()
    _press(engine, EXAMINE_KEY)
    _press(engine, KeySym.RETURN)
    assert engine.examine_state.showing_description
    _press(engine, KeySym.ESCAPE)
    assert engine.examine_state.active
    assert not engine.examine_state.showing_description


def test_escape_does_not_quit_from_gameplay() -> None:
    from src.engine import EngineEventResult

    engine = GameEngine()
    assert _press(engine, KeySym.ESCAPE) is EngineEventResult.CONTINUE
    assert engine.player is not None


def test_ctrl_q_does_not_quit_engine_directly() -> None:
    from src.engine import EngineEventResult

    engine = GameEngine()
    assert _ctrl_q(engine) is EngineEventResult.CONTINUE


def test_ctrl_q_during_examine_still_non_exit_at_engine() -> None:
    from src.engine import EngineEventResult

    engine = GameEngine()
    _press(engine, EXAMINE_KEY)
    assert _ctrl_q(engine) is EngineEventResult.CONTINUE