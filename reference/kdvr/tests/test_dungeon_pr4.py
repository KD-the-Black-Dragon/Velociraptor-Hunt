"""PR 4: aquatic combat, mobility AI, sharks, mobility-aware vore escape."""

from __future__ import annotations

import random
from unittest.mock import patch

from src.components import (
    AI,
    DisplayName,
    Fighter,
    Mobility,
    MobilityType,
    NPCAlignment,
    Position,
    VoreCapable,
)

from src.engine import GameEngine
from src.map_gen import GameMap, Tile, water_positions
from src.spawn import spawn_floor_population
from src.systems.ai import _choose_chase_direction, _pick_random_walkable_tile
from src.systems.combat import try_action
from src.systems.movement import can_move_to, entity_mobility, try_move
from src.systems.vore import (
    _is_valid_escape_tile,
    engulf_player,
    release_engulfed,
)

from tests.map_test_helpers import carve_floor_rect


def _arena_with_shore() -> GameMap:
    """Floor west (x 4–9), deep water east (x 10+) — shore at x=9/10."""
    game_map = GameMap(16, 12)
    game_map.tiles[:, :] = Tile.WALL
    game_map.tiles[4:8, 4:10] = Tile.FLOOR
    game_map.tiles[4:8, 10:14] = Tile.DEEP_WATER
    game_map.enter_xy = (6, 6)
    return game_map


def _shore_shark_pos() -> tuple[int, int]:
    return 10, 6


def _shore_land_pos() -> tuple[int, int]:
    return 9, 6


def _dry_map() -> GameMap:
    game_map = GameMap(12, 10)
    game_map.tiles[:, :] = Tile.WALL
    game_map.tiles[3:7, 3:9] = Tile.FLOOR
    game_map.enter_xy = (4, 5)
    return game_map


def _spawn_shark_on(world, game_map, x: int, y: int):
    from src.spawn import spawn_entity_by_id

    return spawn_entity_by_id(world, "shark", x, y)


def test_aquatic_shore_attack_hits_land_target() -> None:
    from tcod.ecs import Registry

    from src.message_log import MessageLog

    world = Registry()
    game_map = _arena_with_shore()
    shark = _spawn_shark_on(world, game_map, *_shore_shark_pos())
    player = world[object()]
    player.components[Position] = Position(*_shore_land_pos())
    player.components[Fighter] = Fighter(hp=30, max_hp=30, accuracy=10.0, evade=0, ac=1, min_damage=4, max_damage=4)
    log = MessageLog()
    hp_before = player.components[Fighter].hp
    assert try_action(world, game_map, shark, (-1, 0), log)
    assert player.components[Fighter].hp < hp_before
    assert shark.components[Position] == Position(*_shore_shark_pos())


def test_aquatic_cannot_enter_land() -> None:
    from tcod.ecs import Registry

    world = Registry()
    game_map = _arena_with_shore()
    shark = _spawn_shark_on(world, game_map, *_shore_shark_pos())
    assert not try_move(world, game_map, shark, (-1, 0))
    assert shark.components[Position] == Position(*_shore_shark_pos())


def test_flyer_pathing_includes_water() -> None:
    from tcod.ecs import Registry

    world = Registry()
    game_map = _arena_with_shore()
    flyer = world[object()]
    flyer.components[Position] = Position(*_shore_land_pos())
    flyer.components[Mobility] = Mobility(kind=MobilityType.FLY)
    origin = flyer.components[Position]
    assert can_move_to(world, game_map, flyer, origin, (1, 0))
    goal = _pick_random_walkable_tile(
        game_map, random.Random(0), mobility=MobilityType.FLY
    )
    assert game_map.tiles[goal.y, goal.x] in (Tile.FLOOR, Tile.DEEP_WATER, Tile.STAIRS_DOWN)


def test_aquatic_explore_goal_stays_in_water() -> None:
    game_map = _arena_with_shore()
    goal = _pick_random_walkable_tile(
        game_map, random.Random(1), mobility=MobilityType.AQUATIC
    )
    assert game_map.tiles[goal.y, goal.x] == Tile.DEEP_WATER


def test_aquatic_chase_can_close_on_shore_target() -> None:
    from tcod.ecs import Registry

    world = Registry()
    game_map = _arena_with_shore()
    shark = _spawn_shark_on(world, game_map, *_shore_shark_pos())
    player = world[object()]
    player.components[Position] = Position(*_shore_land_pos())
    direction = _choose_chase_direction(
        world,
        game_map,
        shark,
        shark.components[Position],
        player.components[Position],
    )
    assert direction == (-1, 0)


def test_sharks_spawn_on_water_tiles_when_drawn() -> None:
    from tcod.ecs import Registry

    from tests.spawn_test_helpers import fixed_spawn_config

    world = Registry()
    game_map = _arena_with_shore()
    config = fixed_spawn_config(density_pct=0.5, density_variance=0.0)
    spawned = spawn_floor_population(
        world,
        game_map,
        6,
        6,
        floor_depth=1,
        rng=random.Random(0),
        spawn_config=config,
    )
    sharks = [e for e in spawned if e.components[DisplayName].name == "shark"]
    assert len(sharks) >= 1
    for shark in sharks:
        pos = shark.components[Position]
        assert game_map.tiles[pos.y, pos.x] == Tile.DEEP_WATER
        assert entity_mobility(shark) == MobilityType.AQUATIC
        assert shark.components[DisplayName].name == "shark"
        assert VoreCapable in shark.tags


def test_no_sharks_without_water() -> None:
    from tcod.ecs import Registry

    world = Registry()
    game_map = _dry_map()
    assert not water_positions(game_map)
    spawned = spawn_floor_population(world, game_map, 4, 5, floor_depth=1)
    assert not [e for e in spawned if e.components[DisplayName].name == "shark"]


def test_new_game_spawns_ground_npcs() -> None:
    engine = GameEngine()
    engine.new_game(seed=42)
    land_npcs = [
        e
        for e in engine.world.Q.all_of(components=[AI])
        if entity_mobility(e) == MobilityType.GROUND
    ]
    assert len(land_npcs) > 0


def test_ground_escape_rejects_water_tile() -> None:
    from tcod.ecs import Registry

    world = Registry()
    game_map = _arena_with_shore()
    player = world[object()]
    player.components[Position] = Position(*_shore_land_pos())
    player.components[Mobility] = Mobility(kind=MobilityType.GROUND)
    water = Position(*_shore_shark_pos())
    assert not _is_valid_escape_tile(
        game_map, world, water, exclude={player}, prey=player
    )


def test_aquatic_escape_allows_water_tile() -> None:
    from tcod.ecs import Registry

    world = Registry()
    game_map = _arena_with_shore()
    prey = world[object()]
    prey.components[Position] = Position(*_shore_land_pos())
    prey.components[Mobility] = Mobility(kind=MobilityType.AQUATIC)
    water = Position(*_shore_shark_pos())
    assert _is_valid_escape_tile(
        game_map, world, water, exclude={prey}, prey=prey
    )


def test_ground_player_escape_avoids_water() -> None:
    from tcod.ecs import Registry

    from src.components import BlocksMovement, Engulfed, Player, Predator
    from src.message_log import MessageLog

    world = Registry()
    game_map = _arena_with_shore()
    player = world[object()]
    land = Position(*_shore_land_pos())
    player.components[Position] = land
    player.components[Fighter] = Fighter(hp=0, max_hp=30, accuracy=10.0, evade=0, ac=1, min_damage=4, max_damage=4)
    player.components[Mobility] = Mobility(kind=MobilityType.GROUND)
    player.tags.add(Player)
    player.tags.add(BlocksMovement)

    wolf = world[object()]
    wolf.components[Position] = land
    wolf.components[Fighter] = Fighter(hp=30, max_hp=30, accuracy=10.0, evade=2, ac=2, min_damage=4, max_damage=4)
    wolf.components[Predator] = Predator(
        prey=player, narrative_type="OV", failed_struggles=0
    )
    player.tags.add(Engulfed)
    player.tags.discard(BlocksMovement)

    log = MessageLog()
    release_engulfed(
        world,
        player,
        wolf,
        game_map,
        log,
        escape_direction=(1, 0),
        rng=random.Random(0),
    )
    pos = player.components[Position]
    assert game_map.tiles[pos.y, pos.x] != Tile.DEEP_WATER


def test_aquatic_prey_escape_can_use_water() -> None:
    from tcod.ecs import Registry

    from src.components import BlocksMovement, Engulfed, Predator
    from src.message_log import MessageLog
    from src.systems.vore import release_npc_engulfed

    world = Registry()
    game_map = _arena_with_shore()
    prey = world[object()]
    prey.components[Position] = Position(*_shore_land_pos())
    prey.components[Mobility] = Mobility(kind=MobilityType.AQUATIC)
    prey.tags.add(BlocksMovement)

    predator = world[object()]
    predator.components[Position] = Position(*_shore_land_pos())
    predator.components[Predator] = Predator(
        prey=prey, narrative_type="OV", failed_struggles=0
    )
    prey.tags.add(Engulfed)
    prey.tags.discard(BlocksMovement)

    log = MessageLog()
    with patch(
        "src.systems.vore.find_adjacent_free_tile",
        return_value=Position(*_shore_shark_pos()),
    ):
        release_npc_engulfed(world, prey, predator, game_map, log)
    assert prey.components[Position] == Position(*_shore_shark_pos())
    sx, sy = _shore_shark_pos()
    assert game_map.tiles[sy, sx] == Tile.DEEP_WATER


def test_holding_shark_shore_attacks_adjacent_knight() -> None:
    from src.components import Alignment, Predator, Stunned
    from src.message_log import MessageLog
    from src.systems.ai import _try_predator_holding_attack, spawn_test_npc

    from tcod.ecs import Registry

    world = Registry()
    game_map = _arena_with_shore()
    log = MessageLog()
    shark = _spawn_shark_on(world, game_map, *_shore_shark_pos())
    prey = world.new_entity()
    prey.components[Position] = Position(*_shore_shark_pos())
    prey.components[Fighter] = Fighter(hp=0, max_hp=10, accuracy=10.0, evade=0, ac=0, min_damage=0, max_damage=0)
    prey.tags.add(Stunned)
    shark.components[Predator] = Predator(
        prey=prey, narrative_type="OV", failed_struggles=0
    )
    lx, ly = _shore_land_pos()
    knight = spawn_test_npc(
        world,
        x=lx,
        y=ly,
        species="knight",
        alignment=Alignment.GOOD,
    )
    hp_before = knight.components[Fighter].hp
    _try_predator_holding_attack(world, game_map, shark, log, rng=random.Random(0))
    assert knight.components[Fighter].hp < hp_before
    assert shark.components[Position] == Position(*_shore_shark_pos())