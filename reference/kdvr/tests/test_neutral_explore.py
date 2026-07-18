"""PR4 better-npc-exploration: neutral shared explore path + player tile avoidance."""

from __future__ import annotations

import random

import pytest

from src.components import AIState, Alignment, Position
from src.engine import GameEngine
from src.map_gen import Tile
from src.systems.ai import (
    EXPLORE_OSCILLATION_HISTORY,
    _choose_explore_direction,
    _complete_explore_step,
    _ensure_explore_goal,
    explore_reachable_distances,
    run_monster_turns,
    spawn_test_npc,
)

from tests.map_test_helpers import ARENA_X, ARENA_Y, carve_floor_rect, isolate_other_ais


def _wall_corridor(
    engine: GameEngine,
    *,
    left_x: int,
    right_x: int,
    y: int,
) -> None:
    carve_floor_rect(engine, left_x, y, right_x, y)
    for yy in range(y - 1, y + 2):
        for xx in range(left_x - 1, right_x + 2):
            if yy == y and left_x <= xx <= right_x:
                continue
            if engine.game_map.in_bounds(xx, yy):
                engine.game_map.tiles[yy, xx] = Tile.WALL


def test_neutral_explore_goal_avoids_player_tile() -> None:
    engine = GameEngine()
    y = ARENA_Y
    left = ARENA_X
    right = ARENA_X + 6
    _wall_corridor(engine, left_x=left, right_x=right, y=y)
    rabbit = spawn_test_npc(
        engine.world,
        x=left,
        y=y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
    )
    player = engine.player
    player_pos = Position(left + 2, y)
    player.components[Position] = player_pos
    goal = _ensure_explore_goal(
        rabbit.components[AIState],
        engine.game_map,
        rabbit.components[Position],
        rabbit,
        random.Random(0),
        player=player,
    )
    assert goal != player_pos


def test_neutral_explore_bfs_follows_corridor() -> None:
    engine = GameEngine()
    y = ARENA_Y
    x0 = ARENA_X
    rabbit_pos = Position(x0, y)
    goal_pos = Position(x0 + 3, y + 3)
    carve_floor_rect(engine, x0, y, x0 + 3, y)
    carve_floor_rect(engine, x0 + 3, y, x0 + 3, y + 3)
    for yy in range(y - 1, y + 5):
        for xx in range(x0 - 1, x0 + 5):
            on_path = (yy == y and x0 <= xx <= x0 + 3) or (xx == x0 + 3 and y <= yy <= y + 3)
            if not on_path and engine.game_map.in_bounds(xx, yy):
                engine.game_map.tiles[yy, xx] = Tile.WALL
    rabbit = spawn_test_npc(
        engine.world,
        x=rabbit_pos.x,
        y=rabbit_pos.y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
    )
    state = rabbit.components[AIState]
    direction = _choose_explore_direction(
        engine.world,
        engine.game_map,
        rabbit,
        rabbit_pos,
        goal_pos,
        rabbit,
        random.Random(0),
        recent_positions=state.explore_recent_positions,
    )
    assert direction == (1, 0)


def test_neutral_explore_oscillation_repick_changes_goal() -> None:
    engine = GameEngine()
    y = ARENA_Y
    left = ARENA_X
    right = ARENA_X + 6
    _wall_corridor(engine, left_x=left, right_x=right, y=y)
    rabbit = spawn_test_npc(
        engine.world,
        x=left + 1,
        y=y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
    )
    state = rabbit.components[AIState]
    stuck_goal = Position(right, y)
    state.explore_goal = stuck_goal
    state.explore_frustration_limit = 12
    origin = rabbit.components[Position]
    state.explore_recent_positions.extend(
        [Position(left + 1, y), Position(left, y)] * (EXPLORE_OSCILLATION_HISTORY // 2)
    )
    state.explore_recent_goal_distances.extend([5, 6, 5, 6])
    _complete_explore_step(
        state,
        rabbit,
        engine.game_map,
        origin,
        random.Random(2),
        moved=False,
        player=engine.player,
    )
    assert state.explore_goal is not None
    assert state.explore_goal != stuck_goal


def test_neutral_near_player_keeps_moving(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    y = ARENA_Y
    left = ARENA_X
    right = ARENA_X + 8
    _wall_corridor(engine, left_x=left, right_x=right, y=y)
    rabbit = spawn_test_npc(
        engine.world,
        x=left,
        y=y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
    )
    player = engine.player
    player.components[Position] = Position(right, y)
    monkeypatch.setattr("src.systems.ai.explore.EXPLORE_IDLE_CHANCE", 0.0)
    pos_before = rabbit.components[Position]
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(1),
    )
    assert rabbit.components[Position] != player.components[Position]
    assert rabbit.components[Position] != pos_before


def test_neutral_may_pick_player_adjacent_goal() -> None:
    engine = GameEngine()
    y = ARENA_Y
    left = ARENA_X
    right = ARENA_X + 4
    carve_floor_rect(engine, left, y, right, y)
    rabbit = spawn_test_npc(
        engine.world,
        x=left,
        y=y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
    )
    player = engine.player
    player_pos = Position(left + 2, y)
    player.components[Position] = player_pos
    adjacent = Position(left + 1, y)
    state = rabbit.components[AIState]
    reachable = explore_reachable_distances(
        engine.game_map,
        rabbit.components[Position],
        rabbit,
    )
    assert adjacent in reachable
    state.explore_goal = adjacent
    goal = _ensure_explore_goal(
        state,
        engine.game_map,
        rabbit.components[Position],
        rabbit,
        random.Random(3),
        player=player,
    )
    assert goal == adjacent