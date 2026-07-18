"""PR2 better-npc-exploration: explore frustration and farthest-endpoint re-pick."""

from __future__ import annotations

import random

from src.components import AIState, Alignment, Position
from src.engine import GameEngine
from src.map_gen import Tile
from src.systems.ai import (
    EXPLORE_FRUSTRATION_MAX,
    _complete_explore_step,
    _ensure_explore_goal,
    _explore_frustration_give_up,
    _pick_farthest_explore_goal,
    _record_memory_pursuit_blocked,
    explore_reachable_distances,
    run_monster_turns,
    spawn_test_npc,
)

from tests.map_test_helpers import ARENA_X, ARENA_Y, carve_floor_rect, isolate_other_ais
from tests.test_explore_reachable_goals import _two_room_map_with_door, _wall_corridor_box


def test_blocked_explore_step_increments_frustration() -> None:
    engine = GameEngine()
    origin = Position(ARENA_X, ARENA_Y)
    carve_floor_rect(engine, origin.x, origin.y, origin.x + 4, origin.y)
    wolf = spawn_test_npc(
        engine.world,
        x=origin.x,
        y=origin.y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    state = wolf.components[AIState]
    goal = Position(origin.x + 4, origin.y)
    state.explore_goal = goal
    state.explore_frustration_limit = EXPLORE_FRUSTRATION_MAX

    _complete_explore_step(
        state,
        wolf,
        engine.game_map,
        origin,
        random.Random(0),
        moved=False,
    )
    assert state.explore_frustration == 1


def test_explore_progress_resets_frustration() -> None:
    engine = GameEngine()
    origin = Position(ARENA_X, ARENA_Y)
    carve_floor_rect(engine, origin.x, origin.y, origin.x + 4, origin.y)
    wolf = spawn_test_npc(
        engine.world,
        x=origin.x,
        y=origin.y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    state = wolf.components[AIState]
    goal = Position(origin.x + 3, origin.y)
    state.explore_goal = goal
    state.explore_frustration = 5
    state.explore_frustration_limit = EXPLORE_FRUSTRATION_MAX
    wolf.components[Position] = Position(origin.x + 1, origin.y)

    _complete_explore_step(
        state,
        wolf,
        engine.game_map,
        origin,
        random.Random(0),
        moved=True,
    )
    assert state.explore_frustration == 0


def test_explore_frustration_limit_triggers_farthest_repick() -> None:
    engine = GameEngine()
    y = ARENA_Y
    left_x = ARENA_X
    right_x = ARENA_X + 6
    carve_floor_rect(engine, left_x, y, right_x, y)
    _wall_corridor_box(engine, left_x=left_x, right_x=right_x, y=y)
    wolf = spawn_test_npc(
        engine.world,
        x=left_x,
        y=y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    state = wolf.components[AIState]
    origin = wolf.components[Position]
    reachable = explore_reachable_distances(engine.game_map, origin, wolf)
    expected_farthest = _pick_farthest_explore_goal(
        reachable,
        origin,
        random.Random(99),
    )
    assert expected_farthest == Position(right_x, y)

    state.explore_goal = Position(left_x + 1, y)
    state.explore_frustration = EXPLORE_FRUSTRATION_MAX - 1
    state.explore_frustration_limit = EXPLORE_FRUSTRATION_MAX

    _complete_explore_step(
        state,
        wolf,
        engine.game_map,
        origin,
        random.Random(99),
        moved=False,
    )
    assert state.explore_frustration == 0
    assert 8 <= state.explore_frustration_limit <= EXPLORE_FRUSTRATION_MAX
    assert state.explore_goal == expected_farthest
    assert state.explore_force_farthest_on_repick is False


def test_memory_pursuit_does_not_touch_explore_frustration() -> None:
    state = AIState()
    state.explore_frustration = 2
    state.explore_frustration_limit = EXPLORE_FRUSTRATION_MAX
    state.chase_frustration_limit = EXPLORE_FRUSTRATION_MAX
    for _ in range(EXPLORE_FRUSTRATION_MAX):
        _record_memory_pursuit_blocked(state)
    assert state.explore_frustration == 2
    assert state.explore_frustration_limit == EXPLORE_FRUSTRATION_MAX


def test_door_explore_frustration_repick_stays_on_near_side() -> None:
    engine, wolf_pos, _door_pos, far_pos = _two_room_map_with_door(door_open=False)
    wolf = spawn_test_npc(
        engine.world,
        x=wolf_pos.x,
        y=wolf_pos.y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    isolate_other_ais(engine, keep=(wolf,))
    player = engine.player
    player.components[Position] = Position(1, 1)
    state = wolf.components[AIState]
    state.last_known_primary = None
    state.last_known_neutral = None
    state.explore_goal = Position(wolf_pos.x + 2, wolf_pos.y)
    state.explore_frustration = EXPLORE_FRUSTRATION_MAX - 1
    state.explore_frustration_limit = EXPLORE_FRUSTRATION_MAX

    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(7),
    )

    assert state.explore_goal is not None
    assert state.explore_goal != far_pos
    assert state.explore_frustration == 0


def test_new_explore_goal_sets_frustration_limit() -> None:
    engine = GameEngine()
    origin = Position(ARENA_X, ARENA_Y)
    carve_floor_rect(engine, origin.x, origin.y, origin.x + 3, origin.y)
    wolf = spawn_test_npc(
        engine.world,
        x=origin.x,
        y=origin.y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    state = wolf.components[AIState]
    _ensure_explore_goal(
        state,
        engine.game_map,
        origin,
        wolf,
        random.Random(1),
    )
    assert state.explore_goal is not None
    assert EXPLORE_FRUSTRATION_MAX >= state.explore_frustration_limit >= 8
    assert state.explore_frustration == 0


def test_explore_frustration_give_up_sets_farthest_flag() -> None:
    state = AIState(explore_goal=Position(1, 1))
    state.explore_frustration = 5
    state.explore_frustration_limit = 10
    _explore_frustration_give_up(state)
    assert state.explore_goal is None
    assert state.explore_frustration == 0
    assert state.explore_frustration_limit == 0
    assert state.explore_force_farthest_on_repick is True