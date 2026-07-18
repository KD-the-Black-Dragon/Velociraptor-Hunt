"""PR2: doors — placement, player open/close, FOV and NPC blocking."""

from __future__ import annotations

import random

from src.components import MobilityType, Position
from src.constants import MAP_HEIGHT, MAP_WIDTH
from src.engine import GameEngine
from src.map_gen import (
    GameMap,
    Tile,
    can_enter_tile,
    door_positions,
    generate_dungeon,
    is_transparent_tile,
    validate_land_connectivity,
)
from src.map_gen_layouts.doors import (
    _adjacent_door_pairs,
    _is_corridor_mouth,
    _remove_adjacent_doors,
    place_doors,
)
from src.spawn import spawn_entity_by_id
from src.systems.combat import try_action
from src.systems.fov import can_see, update_fov
from src.systems.movement import can_move_to, try_move
from tests.map_test_helpers import carve_floor_tile, relocate_player, spawn_wolf_with_abilities


def _corridor_room_map() -> GameMap:
    """Room (west) connected by a 1-wide corridor (east) to open space."""
    game_map = GameMap(20, 12)
    game_map.tiles[:, :] = Tile.WALL
    game_map.tiles[4:8, 2:8] = Tile.FLOOR
    game_map.tiles[5, 8:14] = Tile.FLOOR
    game_map.enter_xy = (5, 5)
    return game_map


def test_closed_door_blocks_transparency_and_ground_entry() -> None:
    game_map = _corridor_room_map()
    game_map.tiles[5, 8] = Tile.DOOR_CLOSED
    assert not is_transparent_tile(Tile.DOOR_CLOSED)
    assert is_transparent_tile(Tile.DOOR_OPEN)
    assert not can_enter_tile(game_map, 8, 5, MobilityType.GROUND)


def test_closed_door_blocks_fov() -> None:
    game_map = _corridor_room_map()
    game_map.tiles[5, 8] = Tile.DOOR_CLOSED
    update_fov(game_map, 3, 5)
    assert not can_see(game_map, 3, 5, 12, 5)


def test_open_door_restores_fov() -> None:
    game_map = _corridor_room_map()
    game_map.tiles[5, 8] = Tile.DOOR_OPEN
    update_fov(game_map, 3, 5)
    assert can_see(game_map, 3, 5, 12, 5)


def test_player_opens_door_without_moving() -> None:
    engine = GameEngine()
    relocate_player(engine, 5, 5)
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    engine.game_map.tiles[5, 6] = Tile.DOOR_CLOSED

    consumed = try_action(
        engine.world,
        engine.game_map,
        player,
        (1, 0),
        engine.message_log,
    )
    assert consumed
    assert engine.game_map.tiles[5, 6] == Tile.DOOR_OPEN
    assert player.components[Position] == pos


def test_engine_closes_and_misses_open_door() -> None:
    engine = GameEngine()
    relocate_player(engine, 5, 5)
    engine.game_map.tiles[5, 6] = Tile.DOOR_OPEN
    assert engine._try_close_door((1, 0))
    assert engine.game_map.tiles[5, 6] == Tile.DOOR_CLOSED

    assert not engine._try_close_door((0, -1))


def test_close_door_blocked_by_entity() -> None:
    engine = GameEngine()
    relocate_player(engine, 5, 5)
    carve_floor_tile(engine, 6, 5)
    wolf = spawn_entity_by_id(engine.world, "wolf", 6, 5)
    engine.game_map.tiles[5, 6] = Tile.DOOR_OPEN
    assert wolf is not None
    assert not engine._try_close_door((1, 0))
    assert engine.game_map.tiles[5, 6] == Tile.DOOR_OPEN


def test_room_corner_is_not_corridor_mouth() -> None:
    game_map = GameMap(12, 12)
    game_map.tiles[:, :] = Tile.WALL
    game_map.tiles[3:8, 3:9] = Tile.FLOOR
    assert not _is_corridor_mouth(game_map, 3, 3)
    assert not _is_corridor_mouth(game_map, 7, 3)


def test_room_interior_is_not_corridor_mouth() -> None:
    game_map = GameMap(20, 16)
    game_map.tiles[:, :] = Tile.WALL
    game_map.tiles[2:14, 2:18] = Tile.FLOOR
    for y in range(4, 12):
        for x in range(4, 16):
            assert not _is_corridor_mouth(game_map, x, y)


def test_corridor_mouth_candidate_on_threshold() -> None:
    game_map = _corridor_room_map()
    assert _is_corridor_mouth(game_map, 8, 5)


def test_adjacent_doors_are_deduplicated() -> None:
    game_map = GameMap(10, 8)
    game_map.tiles[:, :] = Tile.WALL
    game_map.tiles[3, 2:7] = Tile.FLOOR
    game_map.tiles[3, 4] = Tile.DOOR_CLOSED
    game_map.tiles[3, 5] = Tile.DOOR_CLOSED
    assert _adjacent_door_pairs(game_map)
    _remove_adjacent_doors(game_map, random.Random(0))
    assert not _adjacent_door_pairs(game_map)
    door_tiles = [
        Tile(game_map.tiles[y, x])
        for y in range(game_map.height)
        for x in range(game_map.width)
        if Tile(game_map.tiles[y, x]) in (Tile.DOOR_CLOSED, Tile.DOOR_OPEN)
    ]
    assert len(door_tiles) == 1


def test_npc_cannot_enter_closed_door() -> None:
    engine = GameEngine()
    carve_floor_tile(engine, 5, 5)
    carve_floor_tile(engine, 6, 5)
    wolf = spawn_wolf_with_abilities(engine.world, 5, 5, ["Range6"])
    engine.game_map.tiles[5, 6] = Tile.DOOR_CLOSED
    wolf_pos = wolf.components[Position]
    assert not try_move(engine.world, engine.game_map, wolf, (1, 0))
    assert wolf.components[Position] == wolf_pos


def test_place_doors_on_corridor_mouth() -> None:
    game_map = _corridor_room_map()
    placed = place_doors(game_map, random.Random(0))
    assert placed >= 1
    assert any(
        game_map.tiles[y, x] == Tile.DOOR_CLOSED
        for x, y in door_positions(game_map)
    )
    assert validate_land_connectivity(game_map)


def test_generated_maps_may_include_doors() -> None:
    seen_doors = False
    for seed in range(25):
        dungeon = generate_dungeon(MAP_WIDTH, MAP_HEIGHT, seed=seed)
        if door_positions(dungeon):
            seen_doors = True
            break
    assert seen_doors


def test_npc_pathfinding_treats_closed_door_as_blocked() -> None:
    from tcod.ecs import Registry

    world = Registry()
    game_map = GameMap(12, 10)
    game_map.tiles[:, :] = Tile.WALL
    game_map.tiles[5, 5] = Tile.FLOOR
    game_map.tiles[5, 7] = Tile.FLOOR
    game_map.tiles[5, 6] = Tile.DOOR_CLOSED
    wolf = spawn_wolf_with_abilities(world, 5, 5, ["Range6"])
    assert not can_move_to(
        world,
        game_map,
        wolf,
        Position(5, 5),
        (1, 0),
    )