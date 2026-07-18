"""PR 5: engulfed state, co-tile combat, immunity, predator freeze."""

from __future__ import annotations

import random
from unittest.mock import patch

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.components import (
    AI,
    Alignment,
    BlocksMovement,
    Engulfed,
    Fighter,
    Player,
    Position,
    Predator,
    Stunned,
    VoreCapable,
)
from src.engine import GameEngine
from src.systems.ai import run_monster_turns, spawn_test_npc

from tests.map_test_helpers import (
    carve_adjacent_line,
    carve_east_of,
    carve_floor_tile,
    ensure_adjacent_floor,
    ensure_wolves,
    first_wolf,
    iter_wolves,
)
from src.systems.combat import _fighter_at, try_action
from src.systems.fov import update_fov
from src import messages
from src.systems.naming import entity_log_name
from src.systems.vore import engulf_player, sync_engulfed_position


def _press(engine: GameEngine, sym: KeySym) -> bool:
    return engine.handle_event(
        tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=Modifier.NONE),
    )


def _advance_modal(engine: GameEngine) -> None:
    while engine.vore_modal.active:
        _press(engine, KeySym.RETURN)


def _engulf_via_successful_vore(engine: GameEngine) -> None:
    player = engine.player
    assert player is not None
    try:
        wolf = first_wolf(engine)
    except AssertionError:
        engine.new_game(seed=9)
        player = engine.player
        assert player is not None
        wolf = first_wolf(engine)
    player.components[Fighter].hp = 0
    player.tags.add(Stunned)
    pos = player.components[Position]
    carve_east_of(engine, pos, 2)
    wolf.components[Position] = Position(pos.x + 1, pos.y)
    update_fov(engine.game_map, pos.x, pos.y)
    with patch("src.systems.vore.resolve_vore_hit", return_value=True):
        engine._consume_player_turn()
        _advance_modal(engine)
    assert Engulfed in player.tags


def test_engulf_after_success_modal() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    _engulf_via_successful_vore(engine)
    predator = list(engine.world.Q.all_of(components=[Predator]))[0]
    assert predator.components[Predator].prey is player
    assert BlocksMovement not in player.tags


def test_engulf_co_locates_player_on_predator_tile() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    _engulf_via_successful_vore(engine)
    predator = list(engine.world.Q.all_of(components=[Predator]))[0]
    assert player.components[Position] == predator.components[Position]


def test_fighter_at_skips_engulfed_player_prefers_predator() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    predator = first_wolf(engine)
    pos = player.components[Position]
    carve_east_of(engine, pos, 2)
    predator.components[Position] = Position(pos.x + 1, pos.y)
    engulf_player(
        engine.world, player, predator, engine.message_log, narrative_type="OV"
    )
    tile = predator.components[Position]
    target = _fighter_at(engine.world, tile.x, tile.y)
    assert target is predator
    assert target is not player


def test_third_monster_bumps_predator_not_engulfed_player() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    predator = first_wolf(engine)
    pos = player.components[Position]
    carve_adjacent_line(engine, pos, 2)
    predator.components[Position] = Position(pos.x + 1, pos.y)
    engulf_player(
        engine.world, player, predator, engine.message_log, narrative_type="OV"
    )
    pred_pos = predator.components[Position]
    third_pos = ensure_adjacent_floor(engine, pred_pos, (1, 0))
    third = spawn_test_npc(
        engine.world,
        x=third_pos.x,
        y=third_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
        accuracy=10.0, evade=1, ac=3, min_damage=3, max_damage=3,
    )
    update_fov(engine.game_map, pos.x, pos.y)

    player_hp_before = player.components[Fighter].hp
    predator_hp_before = predator.components[Fighter].hp
    direction = (pred_pos.x - third.components[Position].x, pred_pos.y - third.components[Position].y)
    try_action(engine.world, engine.game_map, third, direction, engine.message_log)

    assert player.components[Fighter].hp == player_hp_before
    assert predator.components[Fighter].hp < predator_hp_before


def test_predator_frozen_while_holding_prey() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    _engulf_via_successful_vore(engine)
    predator = list(engine.world.Q.all_of(components=[Predator]))[0]
    before = predator.components[Position]
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(0),
        modal=engine.vore_modal,
    )
    after = predator.components[Position]
    assert before == after
    assert player.components[Position] == after


def test_sync_engulfed_position_keeps_co_tile() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    predator = first_wolf(engine)
    engulf_player(
        engine.world, player, predator, engine.message_log, narrative_type="OV"
    )
    predator.components[Position] = Position(10, 10)
    sync_engulfed_position(engine.world, predator)
    assert player.components[Position] == Position(10, 10)


def test_struggle_while_engulfed_consumes_turn() -> None:
    engine = GameEngine()
    _engulf_via_successful_vore(engine)
    turns_before = engine.player_turn_count
    with patch.object(engine.rng, "random", return_value=1.0):
        _press(engine, KeySym.UP)
    assert engine.player_turn_count == turns_before + 1


def test_inventory_blocked_while_engulfed() -> None:
    engine = GameEngine()
    _engulf_via_successful_vore(engine)
    _press(engine, KeySym.i)
    assert any(
        "cannot reach your pack" in line for line in engine.message_log.lines()
    )


def test_wait_allowed_while_engulfed() -> None:
    engine = GameEngine()
    _engulf_via_successful_vore(engine)
    turns_before = engine.player_turn_count
    _press(engine, KeySym.H)
    assert engine.player_turn_count == turns_before + 1


def test_engulf_fires_hook() -> None:
    engine = GameEngine()
    fired: list[tuple[object, object]] = []

    def _hook(prey, predator) -> None:
        fired.append((prey, predator))

    from src.events import on_player_engulfed

    on_player_engulfed.append(_hook)
    try:
        _engulf_via_successful_vore(engine)
        assert len(fired) == 1
        assert fired[0][0] is engine.player
    finally:
        on_player_engulfed.remove(_hook)


def test_defeating_predator_releases_player_same_turn() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    predator = first_wolf(engine)
    pos = player.components[Position]
    carve_adjacent_line(engine, pos, 2)
    predator.components[Position] = Position(pos.x + 1, pos.y)
    engulf_player(
        engine.world, player, predator, engine.message_log, narrative_type="OV"
    )
    pred_pos = predator.components[Position]
    third_pos = ensure_adjacent_floor(engine, pred_pos, (1, 0))
    third = spawn_test_npc(
        engine.world,
        x=third_pos.x,
        y=third_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
        accuracy=10.0,
        evade=0,
        ac=0,
        min_damage=5,
        max_damage=5,
    )
    predator.components[Fighter].hp = 1
    update_fov(engine.game_map, pos.x, pos.y)

    direction = (
        pred_pos.x - third.components[Position].x,
        pred_pos.y - third.components[Position].y,
    )
    expected_escape = messages.vore_escaped(entity_log_name(predator))
    try_action(engine.world, engine.game_map, third, direction, engine.message_log)

    assert Engulfed not in player.tags
    assert predator.components.get(Predator) is None
    assert expected_escape in engine.message_log.lines()
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(0),
        modal=engine.vore_modal,
    )


def _move_non_wolves_away(engine: GameEngine) -> None:
    player_pos = engine.player.components[Position]
    assert player_pos is not None
    x = min(player_pos.x + 25, 78)
    y = min(player_pos.y + 15, 41)
    for entity in engine.world.Q.all_of(components=[AI, Position]):
        if VoreCapable not in entity.tags:
            entity.components[Position] = Position(x, y)
            y = min(y + 1, 42)


def test_roaming_wolf_wanders_while_player_engulfed() -> None:
    engine = GameEngine()
    _move_non_wolves_away(engine)
    player = engine.player
    assert player is not None
    monsters = ensure_wolves(engine, 2)
    predator, rover = monsters[0], monsters[1]
    player_pos = player.components[Position]
    far_x = min(player_pos.x + 30, 75)
    far_y = min(player_pos.y + 20, 40)
    for wolf in monsters[2:]:
        carve_floor_tile(engine, far_x, far_y)
        wolf.components[Position] = Position(far_x, far_y)
        far_y = min(far_y + 1, 41)
    pos = player.components[Position]
    carve_east_of(engine, pos, 6)
    predator.components[Position] = Position(pos.x + 1, pos.y)
    engulf_player(
        engine.world, player, predator, engine.message_log, narrative_type="OV"
    )
    rover.components[Position] = Position(pos.x + 5, pos.y)
    rover_before = rover.components[Position]
    update_fov(engine.game_map, pos.x, pos.y)

    chase_calls: list[Position] = []

    def _fake_chase(world, game_map, monster, origin, target, **kwargs):
        chase_calls.append(target)
        return None

    # Direction helpers live in chase/pipeline after PR8–PR9 package split;
    # patch where they are looked up (not only package re-exports).
    with patch("src.systems.ai.chase._choose_chase_direction", side_effect=_fake_chase):
        with patch("src.systems.ai.movement._choose_wander_direction", return_value=None):
            with patch(
                "src.systems.ai.chase._choose_explore_direction",
                return_value=None,
            ):
                with patch("random.Random.random", return_value=0.9):
                    run_monster_turns(
                        engine.world,
                        engine.game_map,
                        player,
                        engine.message_log,
                        rng=random.Random(0),
                        modal=engine.vore_modal,
                    )

    assert player.components[Position] not in chase_calls
    assert rover.components[Position] == rover_before


def test_no_vore_attempt_while_engulfed() -> None:
    engine = GameEngine()
    _engulf_via_successful_vore(engine)
    wolves = ensure_wolves(engine, 2)
    other = next(m for m in wolves if m.components.get(Predator) is None)
    player = engine.player
    assert player is not None
    player_pos = player.components[Position]
    other.components[Position] = Position(player_pos.x, player_pos.y + 1)
    update_fov(engine.game_map, player_pos.x, player_pos.y)
    opened = run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(0),
        modal=engine.vore_modal,
    )
    assert opened is False