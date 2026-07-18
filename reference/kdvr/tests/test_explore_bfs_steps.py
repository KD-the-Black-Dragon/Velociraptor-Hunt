"""PR3 better-npc-exploration: BFS explore steps, oscillation, evil-evil no swap."""

from __future__ import annotations

import random

import pytest

from src.components import AIState, Alignment, Position
from src.engine import GameEngine
from src.map_gen import Tile
from src.systems.ai import (
    DOOR_SPITE_TURNS_MAX,
    DOOR_SPITE_TURNS_MIN,
    EXPLORE_OSCILLATION_HISTORY,
    _choose_explore_direction,
    _complete_explore_step,
    _explore_is_oscillating,
    explore_distances_to_goal,
    pick_evil_chase,
    run_monster_turns,
    spawn_test_npc,
)
from src.systems.combat import can_npc_swap, try_action

from tests.map_test_helpers import ARENA_X, ARENA_Y, carve_floor_rect
from tests.test_enhancements_3 import carved_bump_pair
from tests.test_explore_reachable_goals import _two_room_map_with_door, _wall_corridor_box


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


def test_explore_bfs_step_follows_corridor_not_greedy_cut() -> None:
    engine = GameEngine()
    y = ARENA_Y
    x0 = ARENA_X
    wolf_pos = Position(x0, y)
    goal_pos = Position(x0 + 3, y + 3)
    carve_floor_rect(engine, x0, y, x0 + 3, y)
    carve_floor_rect(engine, x0 + 3, y, x0 + 3, y + 3)
    for yy in range(y - 1, y + 5):
        for xx in range(x0 - 1, x0 + 5):
            on_path = (yy == y and x0 <= xx <= x0 + 3) or (xx == x0 + 3 and y <= yy <= y + 3)
            if not on_path and engine.game_map.in_bounds(xx, yy):
                engine.game_map.tiles[yy, xx] = Tile.WALL
    wolf = spawn_test_npc(
        engine.world,
        x=wolf_pos.x,
        y=wolf_pos.y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    state = wolf.components[AIState]
    direction = _choose_explore_direction(
        engine.world,
        engine.game_map,
        wolf,
        wolf_pos,
        goal_pos,
        wolf,
        random.Random(0),
        recent_positions=state.explore_recent_positions,
        allow_idle=False,
    )
    assert direction == (1, 0)


def test_explore_oscillation_detection() -> None:
    state = AIState()
    state.explore_recent_positions.extend(
        [
            Position(0, 0),
            Position(1, 0),
            Position(0, 0),
            Position(1, 0),
        ]
    )
    state.explore_recent_goal_distances.extend([30, 29, 30, 29])
    assert _explore_is_oscillating(state)


def test_explore_oscillation_repick_changes_goal() -> None:
    engine = GameEngine()
    y = ARENA_Y
    left = ARENA_X
    right = ARENA_X + 6
    _wall_corridor(engine, left_x=left, right_x=right, y=y)
    wolf = spawn_test_npc(
        engine.world,
        x=left + 1,
        y=y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    state = wolf.components[AIState]
    stuck_goal = Position(right, y)
    state.explore_goal = stuck_goal
    state.explore_frustration_limit = 12
    origin = wolf.components[Position]
    state.explore_recent_positions.extend(
        [Position(left + 1, y), Position(left, y)] * (EXPLORE_OSCILLATION_HISTORY // 2)
    )
    state.explore_recent_goal_distances.extend([5, 6, 5, 6])
    _complete_explore_step(
        state,
        wolf,
        engine.game_map,
        origin,
        random.Random(2),
        moved=False,
    )
    assert state.explore_goal is not None
    assert state.explore_goal != stuck_goal
    assert _chebyshev(state.explore_goal, stuck_goal) >= _chebyshev(origin, stuck_goal)


def _chebyshev(a: Position, b: Position) -> int:
    return max(abs(a.x - b.x), abs(a.y - b.y))


def test_evil_evils_cannot_swap() -> None:
    engine = GameEngine()
    (ax, ay), (bx, by), direction = carved_bump_pair(engine)
    wolf_a = spawn_test_npc(
        engine.world,
        x=ax,
        y=ay,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    wolf_b = spawn_test_npc(
        engine.world,
        x=bx,
        y=by,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    assert not can_npc_swap(wolf_a, wolf_b)
    pos_a_before = wolf_a.components[Position]
    pos_b_before = wolf_b.components[Position]
    try_action(
        engine.world,
        engine.game_map,
        wolf_a,
        direction,
        engine.message_log,
    )
    assert wolf_a.components[Position] == pos_a_before
    assert wolf_b.components[Position] == pos_b_before


def test_unreachable_last_known_primary_cleared_at_closed_door() -> None:
    engine, wolf_pos, _door_pos, far_pos = _two_room_map_with_door(door_open=False)
    wolf = spawn_test_npc(
        engine.world,
        x=wolf_pos.x,
        y=wolf_pos.y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    player = engine.player
    player.components[Position] = far_pos
    state = wolf.components[AIState]
    state.last_known_primary = far_pos
    _entity_target, pos_target, _blocked = pick_evil_chase(
        wolf,
        engine.world,
        engine.game_map,
        player,
        random.Random(0),
    )
    assert state.last_known_primary is None
    assert DOOR_SPITE_TURNS_MIN <= state.door_spite_turns_left <= DOOR_SPITE_TURNS_MAX
    assert _entity_target is None
    assert pos_target is None


def test_unreachable_memory_still_cleared_without_door_partition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = GameEngine()
    y = ARENA_Y
    left = ARENA_X
    wall_x = ARENA_X + 3
    right = ARENA_X + 6
    carve_floor_rect(engine, left, y, wall_x - 1, y)
    carve_floor_rect(engine, wall_x + 1, y, right, y)
    for yy in range(y - 1, y + 2):
        if engine.game_map.in_bounds(wall_x, yy):
            engine.game_map.tiles[yy, wall_x] = Tile.WALL
    _wall_corridor_box(engine, left_x=left, right_x=right, y=y)
    # Keep player off the corridor so chase falls through to explore after sanitize.
    engine.player.components[Position] = Position(1, 1)
    wolf = spawn_test_npc(
        engine.world,
        x=left,
        y=y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    unreachable = Position(right, y)
    state = wolf.components[AIState]
    state.last_known_primary = unreachable
    monkeypatch.setattr("src.systems.ai.explore.EXPLORE_IDLE_CHANCE", 0.0)
    _entity_target, pos_target, _blocked = pick_evil_chase(
        wolf,
        engine.world,
        engine.game_map,
        engine.player,
        random.Random(0),
    )
    assert state.last_known_primary is None
    assert state.door_spite_turns_left == 0
    assert pos_target is not None
    assert pos_target != unreachable


def test_door_spite_waits_then_explores(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine, wolf_pos, _door_pos, far_pos = _two_room_map_with_door(door_open=False)
    wolf = spawn_test_npc(
        engine.world,
        x=wolf_pos.x,
        y=wolf_pos.y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    player = engine.player
    player.components[Position] = far_pos
    state = wolf.components[AIState]
    state.last_known_primary = far_pos
    # Constants live on common/explore modules after PR8 package split.
    monkeypatch.setattr("src.systems.ai.common.DOOR_SPITE_TURNS_MIN", 2)
    monkeypatch.setattr("src.systems.ai.common.DOOR_SPITE_TURNS_MAX", 2)
    monkeypatch.setattr("src.systems.ai.explore.EXPLORE_IDLE_CHANCE", 0.0)

    for _ in range(2):
        run_monster_turns(
            engine.world,
            engine.game_map,
            player,
            engine.message_log,
            rng=random.Random(0),
        )
        assert wolf.components[Position] == wolf_pos
        assert state.door_spite_turns_left >= 0

    assert state.door_spite_turns_left == 0
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(0),
    )
    assert state.explore_goal is not None
    assert state.explore_goal != far_pos


def test_explore_idle_can_skip_turn(monkeypatch: pytest.MonkeyPatch) -> None:
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
    monkeypatch.setattr("src.systems.ai.explore.EXPLORE_IDLE_CHANCE", 1.0)
    direction = _choose_explore_direction(
        engine.world,
        engine.game_map,
        wolf,
        origin,
        Position(origin.x + 4, origin.y),
        wolf,
        random.Random(0),
        recent_positions=state.explore_recent_positions,
    )
    assert direction is None


def test_explore_direction_avoids_other_npc_tiles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = GameEngine()
    y = ARENA_Y
    left = ARENA_X
    carve_floor_rect(engine, left, y, left + 4, y)
    wolf_a = spawn_test_npc(
        engine.world,
        x=left,
        y=y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    wolf_b = spawn_test_npc(
        engine.world,
        x=left + 2,
        y=y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    state = wolf_a.components[AIState]
    monkeypatch.setattr("src.systems.ai.explore.EXPLORE_IDLE_CHANCE", 0.0)
    direction = _choose_explore_direction(
        engine.world,
        engine.game_map,
        wolf_a,
        wolf_a.components[Position],
        Position(left + 4, y),
        wolf_a,
        random.Random(0),
        blocked_tiles=frozenset({wolf_b.components[Position]}),
        recent_positions=state.explore_recent_positions,
    )
    assert direction is not None
    dest = wolf_a.components[Position] + direction
    assert dest != wolf_b.components[Position]


def test_explore_distances_to_goal_runs_from_goal() -> None:
    engine = GameEngine()
    y = ARENA_Y
    carve_floor_rect(engine, ARENA_X, y, ARENA_X + 4, y)
    wolf = spawn_test_npc(
        engine.world,
        x=ARENA_X,
        y=y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
    )
    goal = Position(ARENA_X + 4, y)
    distances = explore_distances_to_goal(engine.game_map, goal, wolf)
    assert distances[Position(ARENA_X, y)] == 4
    assert distances[goal] == 0