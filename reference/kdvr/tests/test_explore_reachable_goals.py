"""PR1 better-npc-exploration: BFS reachable explore goals."""

from __future__ import annotations

import random

from src.components import (
    AIState,
    Abilities,
    Alignment,
    Mobility,
    MobilityType,
    Position,
)
from src.data.ability_parser import FixedAbility
from src.engine import GameEngine
from src.map_gen import Tile
from src.systems.ai import (
    _ensure_explore_goal,
    _pick_weighted_far_explore_goal,
    entity_explore_can_traverse,
    explore_reachable_distances,
    pick_evil_chase,
    spawn_test_npc,
)

from tests.map_test_helpers import ARENA_X, ARENA_Y, carve_floor_rect, isolate_other_ais


def _wall_corridor_box(
    engine: GameEngine,
    *,
    left_x: int,
    right_x: int,
    y: int,
) -> None:
    """Seal a horizontal corridor segment from the rest of the dungeon."""
    for yy in range(y - 1, y + 2):
        for xx in range(left_x - 1, right_x + 2):
            if yy == y and left_x <= xx <= right_x:
                continue
            if engine.game_map.in_bounds(xx, yy):
                engine.game_map.tiles[yy, xx] = Tile.WALL


def _two_room_map_with_door(*, door_open: bool) -> tuple[GameEngine, Position, Position, Position]:
    engine = GameEngine()
    y = ARENA_Y
    left_x = ARENA_X
    door_x = ARENA_X + 4
    right_x = ARENA_X + 6
    carve_floor_rect(engine, left_x, y, door_x - 1, y)
    carve_floor_rect(engine, door_x + 1, y, right_x, y)
    engine.game_map.tiles[y, door_x] = (
        Tile.DOOR_OPEN if door_open else Tile.DOOR_CLOSED
    )
    _wall_corridor_box(engine, left_x=left_x, right_x=right_x, y=y)
    return (
        engine,
        Position(left_x, y),
        Position(door_x, y),
        Position(right_x, y),
    )


def test_closed_door_partitions_explore_reachable_set() -> None:
    engine, wolf_pos, door_pos, far_pos = _two_room_map_with_door(door_open=False)
    wolf = spawn_test_npc(
        engine.world,
        x=wolf_pos.x,
        y=wolf_pos.y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    reachable = explore_reachable_distances(engine.game_map, wolf_pos, wolf)
    assert door_pos not in reachable
    assert far_pos not in reachable


def test_open_door_connects_explore_reachable_set() -> None:
    engine, wolf_pos, _door_pos, far_pos = _two_room_map_with_door(door_open=True)
    wolf = spawn_test_npc(
        engine.world,
        x=wolf_pos.x,
        y=wolf_pos.y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    reachable = explore_reachable_distances(engine.game_map, wolf_pos, wolf)
    assert far_pos in reachable


def test_explore_goal_never_beyond_closed_door() -> None:
    engine, wolf_pos, _door_pos, far_pos = _two_room_map_with_door(door_open=False)
    wolf = spawn_test_npc(
        engine.world,
        x=wolf_pos.x,
        y=wolf_pos.y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    for seed in range(40):
        state = wolf.components[AIState]
        state.explore_goal = None
        goal = _ensure_explore_goal(
            state,
            engine.game_map,
            wolf_pos,
            wolf,
            random.Random(seed),
        )
        assert goal != far_pos
        assert far_pos not in explore_reachable_distances(
            engine.game_map, wolf_pos, wolf
        )


def test_closed_door_invalidates_existing_explore_goal() -> None:
    engine, wolf_pos, door_pos, far_pos = _two_room_map_with_door(door_open=True)
    wolf = spawn_test_npc(
        engine.world,
        x=wolf_pos.x,
        y=wolf_pos.y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    state = wolf.components[AIState]
    state.explore_goal = far_pos
    engine.game_map.tiles[door_pos.y, door_pos.x] = Tile.DOOR_CLOSED
    goal = _ensure_explore_goal(
        state,
        engine.game_map,
        wolf_pos,
        wolf,
        random.Random(3),
    )
    assert goal != far_pos


def test_weighted_far_bias_prefers_distant_tiles() -> None:
    reachable = {
        Position(0, 0): 0,
        Position(1, 0): 1,
        Position(10, 0): 10,
    }
    origin = Position(0, 0)
    counts = {Position(1, 0): 0, Position(10, 0): 0}
    rng = random.Random(0)
    for _ in range(1000):
        goal = _pick_weighted_far_explore_goal(reachable, origin, rng)
        assert goal is not None
        counts[goal] += 1
    assert counts[Position(10, 0)] > counts[Position(1, 0)]


def test_aquatic_explore_reachable_stays_in_water() -> None:
    engine = GameEngine()
    water_y = ARENA_Y
    left_x = ARENA_X
    right_x = ARENA_X + 4
    for x in range(left_x, right_x + 1):
        engine.game_map.tiles[water_y, x] = Tile.DEEP_WATER
    shore = Position(right_x + 1, water_y)
    engine.game_map.tiles[shore.y, shore.x] = Tile.FLOOR
    _wall_corridor_box(engine, left_x=left_x, right_x=right_x + 1, y=water_y)

    shark = spawn_test_npc(
        engine.world,
        x=ARENA_X + 2,
        y=water_y,
        species="shark",
        alignment=Alignment.EVIL,
    )
    shark.components[Mobility] = Mobility(kind=MobilityType.AQUATIC)
    origin = shark.components[Position]
    reachable = explore_reachable_distances(engine.game_map, origin, shark)
    assert shore not in reachable
    assert all(
        engine.game_map.tiles[position.y, position.x] == Tile.DEEP_WATER
        for position in reachable
    )


def test_hands_stub_allows_closed_door_in_explore_bfs() -> None:
    engine, wolf_pos, door_pos, far_pos = _two_room_map_with_door(door_open=False)
    wolf = spawn_test_npc(
        engine.world,
        x=wolf_pos.x,
        y=wolf_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    wolf.components[Abilities] = Abilities(parsed=(FixedAbility(ability_id="hands"),))
    assert entity_explore_can_traverse(engine.game_map, door_pos.x, door_pos.y, wolf)
    reachable = explore_reachable_distances(engine.game_map, wolf_pos, wolf)
    assert far_pos in reachable


def test_pick_evil_chase_explore_uses_reachable_goal() -> None:
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
    _entity_target, pos_target, _blocked = pick_evil_chase(
        wolf,
        engine.world,
        engine.game_map,
        player,
        random.Random(5),
    )
    assert _entity_target is None
    assert pos_target is not None
    assert pos_target != far_pos