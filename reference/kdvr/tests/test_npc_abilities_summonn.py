"""PR5: SummonN count parameter."""

from __future__ import annotations

import random

import pytest

from src.components import AbilityState, Position, SpeciesId
from src.data.entity_loader import load_entity_registry
from src.engine import GameEngine
from src.map_gen import Tile
from src.spawn import spawn_from_definition
from src.systems.ai import run_monster_turns
from src.systems.fov import update_fov
from src.systems.movement import MOVEMENT_DIRECTIONS
from tests.map_test_helpers import (
    ARENA_X,
    ARENA_Y,
    carve_floor_tile,
    carve_horizontal_line,
    isolate_other_ais,
    spawn_wolf_with_abilities,
)


def _rabbits(engine: GameEngine) -> list:
    return [
        entity
        for entity in engine.world.Q.all_of(components=[SpeciesId])
        if entity.components[SpeciesId].id == "rabbit"
    ]


def _summon2_wolf(engine: GameEngine):
    wolf = spawn_wolf_with_abilities(
        engine.world,
        ARENA_X,
        ARENA_Y,
        ["Summon2 rabbit"],
    )
    isolate_other_ais(engine, keep=(wolf,))
    return wolf


def _carve_all_adjacent(engine: GameEngine, pos: Position) -> None:
    carve_floor_tile(engine, pos.x, pos.y)
    for dx, dy in MOVEMENT_DIRECTIONS:
        carve_floor_tile(engine, pos.x + dx, pos.y + dy)


def _adjacent_rabbit_ids(engine: GameEngine, wolf) -> set[int]:
    wpos = wolf.components[Position]
    adjacent: set[int] = set()
    for rabbit in _rabbits(engine):
        rpos = rabbit.components[Position]
        if max(abs(wpos.x - rpos.x), abs(wpos.y - rpos.y)) == 1:
            adjacent.add(id(rabbit))
    return adjacent


def test_summon2_spawns_two_rabbits_when_space_allows() -> None:
    engine = GameEngine()
    wolf = _summon2_wolf(engine)
    player = engine.player
    assert player is not None
    _carve_all_adjacent(engine, wolf.components[Position])
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 6)
    player.components[Position] = Position(ARENA_X + 4, ARENA_Y)
    update_fov(engine.game_map, ARENA_X + 4, ARENA_Y)
    before_adjacent = _adjacent_rabbit_ids(engine, wolf)
    engine.message_log = type(engine.message_log)()
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(42),
    )
    after_adjacent = _adjacent_rabbit_ids(engine, wolf)
    spawned_ids = after_adjacent - before_adjacent
    assert len(spawned_ids) == 2
    wpos = wolf.components[Position]
    spawned = [r for r in _rabbits(engine) if id(r) in spawned_ids]
    assert len({rabbit.components[Position] for rabbit in spawned}) == 2
    for rabbit in spawned:
        rpos = rabbit.components[Position]
        assert max(abs(wpos.x - rpos.x), abs(wpos.y - rpos.y)) == 1
    assert wolf.components[AbilityState].summon_consumed is True


def test_summon2_partial_spawn_when_fewer_tiles_than_count() -> None:
    """Summon2 spawns only as many rabbits as there are legal adjacent tiles."""
    engine = GameEngine()
    wolf = spawn_wolf_with_abilities(
        engine.world,
        ARENA_X,
        ARENA_Y,
        ["Summon2 rabbit"],
    )
    isolate_other_ais(engine, keep=(wolf,))
    player = engine.player
    assert player is not None
    wpos = wolf.components[Position]
    carve_floor_tile(engine, wpos.x, wpos.y)
    carve_floor_tile(engine, wpos.x + 1, wpos.y)
    game_map = engine.game_map
    for dx, dy in MOVEMENT_DIRECTIONS:
        if (dx, dy) == (1, 0):
            continue
        x, y = wpos.x + dx, wpos.y + dy
        if game_map.in_bounds(x, y):
            game_map.tiles[y, x] = Tile.WALL
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 6)
    player.components[Position] = Position(ARENA_X + 4, ARENA_Y)
    update_fov(engine.game_map, ARENA_X + 4, ARENA_Y)
    before_adjacent = _adjacent_rabbit_ids(engine, wolf)
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(7),
    )
    assert len(_adjacent_rabbit_ids(engine, wolf) - before_adjacent) == 1
    assert wolf.components[AbilityState].summon_consumed is True


@pytest.mark.parametrize("count", [2, 3, 4])
def test_summon_n_via_helper_spawns_up_to_available_tiles(count: int) -> None:
    engine = GameEngine()
    wolf = spawn_wolf_with_abilities(
        engine.world,
        ARENA_X,
        ARENA_Y,
        [f"Summon{count} rabbit"],
    )
    isolate_other_ais(engine, keep=(wolf,))
    player = engine.player
    assert player is not None
    _carve_all_adjacent(engine, wolf.components[Position])
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 6)
    player.components[Position] = Position(ARENA_X + 4, ARENA_Y)
    update_fov(engine.game_map, ARENA_X + 4, ARENA_Y)
    before_adjacent = _adjacent_rabbit_ids(engine, wolf)
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(99),
    )
    expected = min(count, 8)
    assert len(_adjacent_rabbit_ids(engine, wolf) - before_adjacent) == expected