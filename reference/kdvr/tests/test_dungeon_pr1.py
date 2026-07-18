"""PR 1: tile types, mobility, FOV transparency, render glyphs."""

from __future__ import annotations

import tcod.console

from src import messages
from src.components import Mobility, MobilityType, Player, Position, Renderable
from src.engine import GameEngine
from src.map_gen import GameMap, Tile, can_enter_tile, is_transparent_tile
from src.message_log import MessageLog
from src.data.entity_loader import load_entity_registry
from src.spawn import spawn_from_definition
from src.systems.combat import try_action
from src.systems.fov import can_see, update_fov
from src.systems.movement import can_move_to, entity_mobility, try_move
from src.systems.render import render_map


def _small_map() -> GameMap:
    game_map = GameMap(12, 10)
    game_map.tiles[:, :] = Tile.WALL
    game_map.tiles[4:6, 2:10] = Tile.FLOOR
    game_map.tiles[5, 5:8] = Tile.DEEP_WATER
    game_map.tiles[4, 8] = Tile.STAIRS_DOWN
    game_map.enter_xy = (2, 5)
    return game_map


def test_tile_transparency() -> None:
    assert is_transparent_tile(Tile.FLOOR)
    assert is_transparent_tile(Tile.DEEP_WATER)
    assert is_transparent_tile(Tile.STAIRS_DOWN)
    assert not is_transparent_tile(Tile.WALL)


def test_mobility_traversal_matrix() -> None:
    game_map = _small_map()
    assert can_enter_tile(game_map, 2, 5, MobilityType.GROUND)
    assert not can_enter_tile(game_map, 5, 5, MobilityType.GROUND)
    assert can_enter_tile(game_map, 5, 5, MobilityType.FLY)
    assert can_enter_tile(game_map, 5, 5, MobilityType.AQUATIC)
    assert not can_enter_tile(game_map, 2, 5, MobilityType.AQUATIC)
    assert can_enter_tile(game_map, 8, 4, MobilityType.GROUND)
    assert can_enter_tile(game_map, 8, 4, MobilityType.STATIONARY)
    assert not can_enter_tile(game_map, 8, 4, MobilityType.AQUATIC)


def test_is_walkable_includes_stairs() -> None:
    game_map = _small_map()
    assert game_map.is_walkable(8, 4)
    assert game_map.is_transparent(5, 5)


def test_fov_passes_through_deep_water() -> None:
    game_map = _small_map()
    update_fov(game_map, 2, 5)
    assert can_see(game_map, 2, 5, 9, 5)


def test_ground_player_blocked_by_water() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    game_map = _small_map()
    player.components[Position] = Position(4, 5)
    assert entity_mobility(player) == MobilityType.GROUND
    assert not try_move(engine.world, game_map, player, (1, 0))


def test_player_deep_water_attempt_shows_message() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    game_map = _small_map()
    player.components[Position] = Position(4, 5)
    log = MessageLog()
    assert not try_action(engine.world, game_map, player, (1, 0), log)
    assert messages.cant_enter_deep_water() in log.lines()


def test_flyer_crosses_water() -> None:
    from tcod.ecs import Registry

    world = Registry()
    game_map = _small_map()
    flyer = world[object()]
    flyer.components[Position] = Position(4, 5)
    flyer.components[Mobility] = Mobility(kind=MobilityType.FLY)
    assert try_move(world, game_map, flyer, (1, 0))
    assert flyer.components[Position] == Position(5, 5)


def test_aquatic_stays_in_water() -> None:
    from tcod.ecs import Registry

    world = Registry()
    game_map = _small_map()
    aquatic = world[object()]
    aquatic.components[Position] = Position(5, 5)
    aquatic.components[Mobility] = Mobility(kind=MobilityType.AQUATIC)
    assert not try_move(world, game_map, aquatic, (-1, 0))
    assert try_move(world, game_map, aquatic, (1, 0))
    assert aquatic.components[Position] == Position(6, 5)


def test_player_spawns_with_ground_mobility() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    assert entity_mobility(player) == MobilityType.GROUND


def test_spawned_npcs_have_ground_mobility() -> None:
    from tcod.ecs import Registry

    world = Registry()
    knight_def = load_entity_registry().get("knight")
    knight = spawn_from_definition(world, knight_def, 1, 1)
    assert entity_mobility(knight) == MobilityType.GROUND


def test_render_map_draws_water_and_stairs() -> None:
    console = tcod.console.Console(12, 10, order="F")
    game_map = _small_map()
    game_map.explored[:] = True
    game_map.visible[:] = True
    render_map(console, game_map)

    def ch(x: int, y: int) -> str:
        return chr(int(console.rgba[x, y]["ch"]))

    assert ch(5, 5) == "~"
    assert ch(8, 4) == ">"


def test_can_move_to_respects_mobility() -> None:
    from tcod.ecs import Registry

    world = Registry()
    game_map = _small_map()
    aquatic = world[object()]
    aquatic.components[Position] = Position(5, 5)
    aquatic.components[Mobility] = Mobility(kind=MobilityType.AQUATIC)
    origin = aquatic.components[Position]
    assert not can_move_to(world, game_map, aquatic, origin, (-1, 0))
    assert can_move_to(world, game_map, aquatic, origin, (1, 0))