"""PR11: good NPCs path through neutrals via swap during chase/follow."""

from __future__ import annotations

import random

from src.components import Alignment, Position
from src.engine import GameEngine
from src.map_gen import Tile
from src.systems.ai import (
    GOOD_CHASE_SWAPPABLE_ALIGNMENTS,
    _choose_good_follow_direction,
    run_monster_turns,
    spawn_test_npc,
)
from src.systems.combat import try_action
from src.systems.fov import update_fov
from src.systems.movement import can_move_to, can_step_for_chase

from tests.map_test_helpers import ARENA_X, ARENA_Y, carve_floor_rect, isolate_other_ais


def _one_wide_corridor(engine: GameEngine, length: int) -> list[Position]:
    isolate_other_ais(engine)
    y = ARENA_Y
    x1 = ARENA_X
    x2 = ARENA_X + length - 1
    carve_floor_rect(engine, x1, y, x2, y)
    for x in range(x1 - 1, x2 + 2):
        for wall_y in (y - 1, y + 1):
            if engine.game_map.in_bounds(x, wall_y):
                engine.game_map.tiles[wall_y, x] = Tile.WALL
    return [Position(x1 + offset, y) for offset in range(length)]


def test_can_step_for_chase_rejects_good_into_good_for_follow() -> None:
    engine = GameEngine()
    tiles = _one_wide_corridor(engine, 2)
    knight_a = spawn_test_npc(
        engine.world,
        x=tiles[0].x,
        y=tiles[0].y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    spawn_test_npc(
        engine.world,
        x=tiles[1].x,
        y=tiles[1].y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    assert not can_step_for_chase(
        engine.world,
        engine.game_map,
        knight_a,
        tiles[0],
        (1, 0),
        swappable_defender_alignments=GOOD_CHASE_SWAPPABLE_ALIGNMENTS,
    )


def test_can_step_for_chase_allows_good_into_neutral() -> None:
    engine = GameEngine()
    tiles = _one_wide_corridor(engine, 2)
    knight = spawn_test_npc(
        engine.world,
        x=tiles[0].x,
        y=tiles[0].y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    rabbit = spawn_test_npc(
        engine.world,
        x=tiles[1].x,
        y=tiles[1].y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
    )
    assert not can_move_to(
        engine.world,
        engine.game_map,
        knight,
        tiles[0],
        (1, 0),
    )
    assert can_step_for_chase(
        engine.world,
        engine.game_map,
        knight,
        tiles[0],
        (1, 0),
    )
    assert try_action(
        engine.world,
        engine.game_map,
        knight,
        (1, 0),
        engine.message_log,
    )
    assert knight.components[Position] == tiles[1]
    assert rabbit.components[Position] == tiles[0]


def test_good_follow_direction_does_not_step_into_blocking_good() -> None:
    engine = GameEngine()
    tiles = _one_wide_corridor(engine, 3)
    player = engine.player
    assert player is not None
    knight_a = spawn_test_npc(
        engine.world,
        x=tiles[0].x,
        y=tiles[0].y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    spawn_test_npc(
        engine.world,
        x=tiles[1].x,
        y=tiles[1].y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    player.components[Position] = tiles[2]
    direction = _choose_good_follow_direction(
        engine.world,
        engine.game_map,
        knight_a,
        tiles[0],
        player,
    )
    assert direction != (1, 0)
    if direction is not None:
        assert knight_a.components[Position] + direction != tiles[1]


def test_good_follow_direction_steps_into_blocking_neutral() -> None:
    engine = GameEngine()
    tiles = _one_wide_corridor(engine, 3)
    player = engine.player
    assert player is not None
    knight = spawn_test_npc(
        engine.world,
        x=tiles[0].x,
        y=tiles[0].y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    spawn_test_npc(
        engine.world,
        x=tiles[1].x,
        y=tiles[1].y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
    )
    player.components[Position] = tiles[2]
    direction = _choose_good_follow_direction(
        engine.world,
        engine.game_map,
        knight,
        tiles[0],
        player,
    )
    assert direction == (1, 0)


def test_knight_follows_player_past_rabbit_in_corridor() -> None:
    engine = GameEngine()
    tiles = _one_wide_corridor(engine, 5)
    player = engine.player
    assert player is not None
    knight = spawn_test_npc(
        engine.world,
        x=tiles[0].x,
        y=tiles[0].y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    rabbit = spawn_test_npc(
        engine.world,
        x=tiles[2].x,
        y=tiles[2].y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
    )
    rabbit_start = rabbit.components[Position]
    player.components[Position] = tiles[4]
    update_fov(engine.game_map, tiles[0].x, tiles[0].y)

    for _ in range(6):
        run_monster_turns(
            engine.world,
            engine.game_map,
            player,
            engine.message_log,
            rng=random.Random(0),
        )

    knight_pos = knight.components[Position]
    assert knight_pos.x > rabbit_start.x
    assert knight_pos.x >= tiles[3].x


def test_two_knights_follow_player_without_swap_freeze() -> None:
    engine = GameEngine()
    tiles = _one_wide_corridor(engine, 5)
    player = engine.player
    assert player is not None
    knight_rear = spawn_test_npc(
        engine.world,
        x=tiles[0].x,
        y=tiles[0].y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    knight_front = spawn_test_npc(
        engine.world,
        x=tiles[1].x,
        y=tiles[1].y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    rear_start = knight_rear.components[Position]
    front_start = knight_front.components[Position]
    player.components[Position] = tiles[4]
    update_fov(engine.game_map, tiles[0].x, tiles[0].y)

    for _ in range(8):
        run_monster_turns(
            engine.world,
            engine.game_map,
            player,
            engine.message_log,
            rng=random.Random(0),
        )

    assert (
        knight_rear.components[Position].x > rear_start.x
        or knight_front.components[Position].x > front_start.x
    )
    assert knight_front.components[Position].x >= tiles[2].x