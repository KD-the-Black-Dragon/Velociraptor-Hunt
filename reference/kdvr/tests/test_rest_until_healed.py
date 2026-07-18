"""Tests for rest-until-healed-or-danger (main keyboard 5)."""

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
    ProperName,
    Stunned,
)
from src.components import Alignment
from src.constants import PLAYER_MAX_HP, REST_UNTIL_MAX_TURNS
from src.engine import GameEngine
from src.events import fire_player_combat_targeted
from src.input_handlers import INSPECT_INVENTORY_KEY, REST_UNTIL_KEY, WAIT_KEYS
from src.systems.item_modals import InventoryModalMode
from src.message_log import MessageCategory
from src.systems.ai import spawn_test_npc
from src.systems.fov import update_fov
from src.systems.rest import (
    RestEndReason,
    advance_rest_frame,
    begin_rest_until_healed_or_danger,
    find_good_ally_alarm_shouter,
    try_rest_until_healed_or_danger,
)


def _press(engine: GameEngine, sym: KeySym) -> None:
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


def test_rest_key_is_main_keyboard_five_not_numpad() -> None:
    assert REST_UNTIL_KEY == KeySym.N5
    assert KeySym.N5 not in WAIT_KEYS
    assert KeySym.KP_5 in WAIT_KEYS


def test_pre_check_full_health_blocks_without_turn() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    fighter = player.components[Fighter]
    fighter.hp = fighter.max_hp

    _press(engine, REST_UNTIL_KEY)

    assert engine.player_turn_count == 0
    assert messages.rest_already_full_health() in engine.message_log.lines()


def test_pre_check_engulfed_blocks_without_turn() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.tags.add(Engulfed)
    player.components[Fighter].hp = 10

    _press(engine, REST_UNTIL_KEY)

    assert engine.player_turn_count == 0
    assert messages.rest_engulfed_no_time() in _danger_lines(engine)


def test_pre_check_visible_evil_blocks_without_turn() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 10
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

    _press(engine, REST_UNTIL_KEY)

    assert engine.player_turn_count == 0
    assert messages.rest_too_dangerous_now() in _danger_lines(engine)


def test_rest_start_message_and_healed_end() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 10
    turns: list[int] = []

    def consume() -> None:
        turns.append(1)
        player.components[Fighter].hp = player.components[Fighter].max_hp

    result = try_rest_until_healed_or_danger(
        player=player,
        game_map=engine.game_map,
        world=engine.world,
        message_log=engine.message_log,
        consume_turn=consume,
        max_turns=5,
    )

    assert result.end_reason == RestEndReason.HEALED
    assert result.consumed_turns == 1
    assert messages.rest_start() in engine.message_log.lines()
    assert messages.rest_fully_healed() in engine.message_log.lines()


def test_attack_interrupt_ends_rest_with_alert() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 10

    def consume() -> None:
        fire_player_combat_targeted()

    result = try_rest_until_healed_or_danger(
        player=player,
        game_map=engine.game_map,
        world=engine.world,
        message_log=engine.message_log,
        consume_turn=consume,
        max_turns=REST_UNTIL_MAX_TURNS,
    )

    assert result.end_reason == RestEndReason.ATTACK
    assert result.consumed_turns == 1
    assert messages.rest_interrupted_by_attack() in _caution_lines(engine)


def test_rest_cap_ends_with_finish_message() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 10

    with patch("src.engine_turn.run_monster_turns"):
        result = try_rest_until_healed_or_danger(
            player=player,
            game_map=engine.game_map,
            world=engine.world,
            message_log=engine.message_log,
            consume_turn=engine._consume_player_turn,
            max_turns=3,
        )

    assert result.end_reason == RestEndReason.CAP
    assert result.consumed_turns == 3
    assert messages.rest_finish() in engine.message_log.lines()


def test_numpad_five_still_single_wait() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 10

    with patch("src.engine_turn.run_monster_turns"):
        _press(engine, KeySym.KP_5)

    assert engine.player_turn_count == 1
    assert messages.rest_start() not in engine.message_log.lines()


def test_stunned_rest_is_silent_per_turn() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    player = engine.player
    assert player is not None
    fighter = player.components[Fighter]
    fighter.hp = 0
    player.tags.add(Stunned)

    with patch("src.engine_turn.run_monster_turns"):
        try_rest_until_healed_or_danger(
            player=player,
            game_map=engine.game_map,
            world=engine.world,
            message_log=engine.message_log,
            consume_turn=engine._consume_player_turn,
            max_turns=1,
        )

    assert messages.stunned_too_tired_to_move() not in engine.message_log.lines()


def test_find_good_ally_alarm_shouter_prefers_visible_ally_with_evil_los() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    player = engine.player
    assert player is not None
    pos = player.components[Position]

    ally = spawn_test_npc(
        engine.world,
        x=pos.x + 1,
        y=pos.y,
        species="knight",
        alignment=Alignment.GOOD,
        species_id="knight",
    )
    evil = spawn_test_npc(
        engine.world,
        x=pos.x + 2,
        y=pos.y,
        species="wolf",
        alignment=Alignment.EVIL,
        species_id="wolf",
    )
    update_fov(engine.game_map, pos.x, pos.y)

    def fake_visible_good_evils(monster, world, game_map):
        if monster is ally:
            return [evil]
        return []

    with patch(
        "src.systems.danger_interrupts._visible_good_evils",
        side_effect=fake_visible_good_evils,
    ):
        assert find_good_ally_alarm_shouter(engine.game_map, engine.world, player) is ally


def test_ally_alarm_when_evil_visible_to_ally_not_player() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 15
    pos = player.components[Position]

    ally = spawn_test_npc(
        engine.world,
        x=pos.x + 1,
        y=pos.y,
        species="knight",
        alignment=Alignment.GOOD,
        species_id="knight",
    )
    ally.components[ProperName] = ProperName(name="Sir Bob")

    evil = spawn_test_npc(
        engine.world,
        x=pos.x + 2,
        y=pos.y,
        species="wolf",
        alignment=Alignment.EVIL,
        species_id="wolf",
    )
    update_fov(engine.game_map, pos.x, pos.y)
    evil_pos = evil.components[Position]
    engine.game_map.visible[evil_pos.y, evil_pos.x] = False

    def fake_visible_good_evils(monster, world, game_map):
        if monster is ally:
            return [evil]
        return []

    with patch("src.engine_turn.run_monster_turns"), patch(
        "src.systems.rest._visible_good_evils",
        side_effect=fake_visible_good_evils,
    ), patch("src.systems.danger_interrupts.player_has_visible_evil", return_value=False):
        result = try_rest_until_healed_or_danger(
            player=player,
            game_map=engine.game_map,
            world=engine.world,
            message_log=engine.message_log,
            consume_turn=engine._consume_player_turn,
            max_turns=1,
        )

    assert result.end_reason == RestEndReason.ALLY_ALARM
    assert messages.good_ally_shouts_alarm("Sir Bob") in _caution_lines(engine)


def _finish_rest(engine: GameEngine) -> None:
    while engine.rest_in_progress():
        engine.advance_rest_animation()


def test_main_keyboard_five_starts_incremental_rest() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = PLAYER_MAX_HP - 1

    _press(engine, REST_UNTIL_KEY)

    assert messages.rest_start() in engine.message_log.lines()
    assert engine.rest_in_progress()
    assert engine.player_turn_count == 0

    with patch("src.engine_turn.run_monster_turns"):
        _finish_rest(engine)

    assert not engine.rest_in_progress()
    assert engine.player_turn_count >= 1


def test_manual_interrupt_cancels_rest_and_waits_one_turn() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 10

    _press(engine, REST_UNTIL_KEY)
    assert engine.rest_in_progress()

    with patch("src.engine_turn.run_monster_turns"):
        _press(engine, KeySym.KP_5)

    assert not engine.rest_in_progress()
    assert engine.player_turn_count == 1
    assert messages.rest_finish() not in engine.message_log.lines()
    assert messages.rest_fully_healed() not in engine.message_log.lines()


def test_manual_interrupt_cancels_rest_and_opens_inventory() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 10

    _press(engine, REST_UNTIL_KEY)
    assert engine.rest_in_progress()

    _press(engine, INSPECT_INVENTORY_KEY)

    assert not engine.rest_in_progress()
    assert engine.inventory_modal.mode is not InventoryModalMode.NONE


def test_manual_interrupt_cancels_rest_and_moves() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 10

    _press(engine, REST_UNTIL_KEY)
    assert engine.rest_in_progress()

    with patch("src.engine_turn.run_monster_turns"), patch(
        "src.engine_input.try_action",
        return_value=True,
    ):
        _press(engine, KeySym.RIGHT)

    assert not engine.rest_in_progress()
    assert engine.player_turn_count == 1


def test_rest_frame_batches_silent_turns_without_dirty_screen() -> None:
    engine = GameEngine()
    _clear_npcs(engine)
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 10
    session = begin_rest_until_healed_or_danger(
        player=player,
        game_map=engine.game_map,
        world=engine.world,
        message_log=engine.message_log,
        max_turns=20,
    )
    assert session is not None

    with patch("src.engine_turn.run_monster_turns"), patch.object(
        engine, "_apply_natural_regen"
    ):
        frame = advance_rest_frame(
            player=player,
            game_map=engine.game_map,
            world=engine.world,
            message_log=engine.message_log,
            session=session,
            consume_turn=engine._consume_player_turn,
        )

    assert session.consumed == 16
    assert not frame.finished
    assert frame.screen_dirty is False