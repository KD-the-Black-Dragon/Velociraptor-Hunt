"""Regression: memory chase detour, door shock, and cold-trail timeout."""

from __future__ import annotations

import random

import pytest

from src.components import AIState, Alignment, Position
from src.engine import GameEngine
from src.map_gen import Tile
from src.systems.ai import (
    MEMORY_TRAIL_TURNS_MAX,
    MEMORY_TRAIL_TURNS_MIN,
    explore_reachable_distances,
    run_monster_turns,
    spawn_test_npc,
)
from src.systems.abilities import has_erratic
from tests.map_test_helpers import (
    ARENA_X,
    ARENA_Y,
    carve_floor_rect,
    spawn_wolf_with_abilities,
)


def _u_path_closed_door() -> tuple[GameEngine, Position, Position, Position]:
    """Left stub, bottom detour, right arm; closed door on the short top route."""
    engine = GameEngine()
    for y in range(ARENA_Y - 2, ARENA_Y + 8):
        for x in range(ARENA_X - 2, ARENA_X + 16):
            if engine.game_map.in_bounds(x, y):
                engine.game_map.tiles[y, x] = Tile.WALL

    # left arm + down
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X + 4, ARENA_Y)
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X, ARENA_Y + 4)
    # bottom connector
    carve_floor_rect(engine, ARENA_X, ARENA_Y + 4, ARENA_X + 10, ARENA_Y + 4)
    # right arm up to player
    carve_floor_rect(engine, ARENA_X + 10, ARENA_Y, ARENA_X + 10, ARENA_Y + 4)
    carve_floor_rect(engine, ARENA_X + 6, ARENA_Y, ARENA_X + 10, ARENA_Y)

    door = Position(ARENA_X + 5, ARENA_Y)
    engine.game_map.tiles[door.y, door.x] = Tile.DOOR_CLOSED
    wolf_pos = Position(ARENA_X + 4, ARENA_Y)
    player_pos = Position(ARENA_X + 10, ARENA_Y)
    return engine, wolf_pos, door, player_pos


def test_memory_chase_takes_detour_around_closed_door(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Long enough trail for this short U-detour; timeout covered separately.
    monkeypatch.setattr("src.systems.ai.chase.MEMORY_TRAIL_TURNS_MIN", 40)
    monkeypatch.setattr("src.systems.ai.chase.MEMORY_TRAIL_TURNS_MAX", 40)
    monkeypatch.setattr("src.systems.ai.common.DOOR_SHOCK_TURNS_MIN", 2)
    monkeypatch.setattr("src.systems.ai.common.DOOR_SHOCK_TURNS_MAX", 2)

    engine, wolf_pos, door, player_pos = _u_path_closed_door()
    engine.player.components[Position] = player_pos
    wolf = spawn_test_npc(
        engine.world,
        x=wolf_pos.x,
        y=wolf_pos.y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    state = wolf.components[AIState]
    state.last_known_primary = player_pos

    reachable = explore_reachable_distances(engine.game_map, wolf_pos, wolf)
    assert player_pos in reachable

    door_face_streak = 0
    max_door_face_streak = 0
    reached_detour = False
    reached_memory = False
    saw_shock = False

    for t in range(45):
        run_monster_turns(
            engine.world,
            engine.game_map,
            engine.player,
            engine.message_log,
            rng=random.Random(t),
            player_turn_count=t,
        )
        if state.door_spite_turns_left > 0 and state.last_known_primary is not None:
            saw_shock = True
        p = wolf.components[Position]
        if p.y == ARENA_Y and abs(p.x - door.x) <= 1:
            door_face_streak += 1
            max_door_face_streak = max(max_door_face_streak, door_face_streak)
        else:
            door_face_streak = 0
        if p.y >= ARENA_Y + 3:
            reached_detour = True
        if p == player_pos:
            reached_memory = True
            break

    assert saw_shock, "expected brief door shock before detour"
    assert reached_detour or reached_memory, (
        f"wolf never left door face; last={wolf.components[Position]} "
        f"lk={state.last_known_primary} goal={state.explore_goal}"
    )
    # Euclidean dance was indefinite (50+ turns on two tiles). Allow a short linger.
    assert max_door_face_streak < 16


def test_memory_trail_timeout_gives_up_without_los(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Even with a valid detour path, cold trail clears last-known."""
    monkeypatch.setattr("src.systems.ai.chase.MEMORY_TRAIL_TURNS_MIN", 5)
    monkeypatch.setattr("src.systems.ai.chase.MEMORY_TRAIL_TURNS_MAX", 5)
    monkeypatch.setattr("src.systems.ai.common.DOOR_SHOCK_TURNS_MIN", 0)
    monkeypatch.setattr("src.systems.ai.common.DOOR_SHOCK_TURNS_MAX", 0)

    engine, wolf_pos, _door, player_pos = _u_path_closed_door()
    engine.player.components[Position] = player_pos
    wolf = spawn_test_npc(
        engine.world,
        x=wolf_pos.x,
        y=wolf_pos.y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    state = wolf.components[AIState]
    state.last_known_primary = player_pos

    for t in range(8):
        run_monster_turns(
            engine.world,
            engine.game_map,
            engine.player,
            engine.message_log,
            rng=random.Random(0),
            player_turn_count=t,
        )

    assert state.last_known_primary is None
    assert state.memory_blind_turns == 0
    assert MEMORY_TRAIL_TURNS_MIN <= MEMORY_TRAIL_TURNS_MAX


def test_no_path_still_door_spite_then_explore() -> None:
    """Closed door with no detour: sanitize + spite, then explore (no infinite wait)."""
    engine = GameEngine()
    y = ARENA_Y
    left = ARENA_X
    door_x = ARENA_X + 4
    right = ARENA_X + 6
    carve_floor_rect(engine, left, y, door_x - 1, y)
    carve_floor_rect(engine, door_x + 1, y, right, y)
    engine.game_map.tiles[y, door_x] = Tile.DOOR_CLOSED
    for yy in range(y - 1, y + 2):
        for xx in range(left - 1, right + 2):
            if yy == y and left <= xx <= right:
                continue
            if engine.game_map.in_bounds(xx, yy):
                engine.game_map.tiles[yy, xx] = Tile.WALL

    wolf_pos = Position(left, y)
    far = Position(right, y)
    engine.player.components[Position] = far
    wolf = spawn_test_npc(
        engine.world,
        x=wolf_pos.x,
        y=wolf_pos.y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    state = wolf.components[AIState]
    state.last_known_primary = far

    saw_spite = False
    for t in range(20):
        run_monster_turns(
            engine.world,
            engine.game_map,
            engine.player,
            engine.message_log,
            rng=random.Random(0),
            player_turn_count=t,
        )
        if state.door_spite_turns_left > 0:
            saw_spite = True
        if t >= 14 and state.door_spite_turns_left == 0:
            assert state.last_known_primary is None
            break
    assert saw_spite


def test_two_erratics_in_corridor_do_not_freeze_forever() -> None:
    """Two erratics in a short corridor should keep taking turns without hard-lock."""
    engine = GameEngine()
    y = ARENA_Y
    left = ARENA_X
    right = ARENA_X + 5
    carve_floor_rect(engine, left, y, right, y)
    for yy in range(y - 1, y + 2):
        for xx in range(left - 1, right + 2):
            if yy == y and left <= xx <= right:
                continue
            if engine.game_map.in_bounds(xx, yy):
                engine.game_map.tiles[yy, xx] = Tile.WALL

    engine.player.components[Position] = Position(1, 1)
    engine.game_map.tiles[1, 1] = Tile.FLOOR

    a = spawn_wolf_with_abilities(engine.world, left, y, ["Erratic"])
    b = spawn_wolf_with_abilities(engine.world, left + 2, y, ["Erratic"])
    assert has_erratic(a) and has_erratic(b)

    # No quarry memory: pure explore / erratic random in the box.
    for entity in (a, b):
        st = entity.components[AIState]
        st.last_known_primary = None
        st.last_known_neutral = None

    moved = 0
    prev_a = a.components[Position]
    prev_b = b.components[Position]
    for t in range(30):
        run_monster_turns(
            engine.world,
            engine.game_map,
            engine.player,
            engine.message_log,
            rng=random.Random(t + 11),
            player_turn_count=t,
        )
        pa = a.components[Position]
        pb = b.components[Position]
        if pa != prev_a or pb != prev_b:
            moved += 1
        prev_a, prev_b = pa, pb
        assert pa.y == y and left <= pa.x <= right
        assert pb.y == y and left <= pb.x <= right

    # At least some motion expected from erratic/explore; not a hard freeze.
    assert moved >= 5
