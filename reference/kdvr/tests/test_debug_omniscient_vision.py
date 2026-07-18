"""Debug F5: player omniscient vision without changing NPC line of sight."""

from __future__ import annotations

from src.components import Position
from src.engine import GameEngine
from src.map_gen import Tile
from src.systems.fov import can_see, update_fov

from tests.map_test_helpers import ARENA_X, ARENA_Y, carve_floor_rect, first_wolf


def test_omniscient_vision_reveals_entire_map_for_player() -> None:
    engine = GameEngine()
    engine._debug_omniscient_vision = True
    engine._update_fov()
    assert engine.game_map.visible.all()
    assert engine.game_map.explored.all()


def test_omniscient_vision_does_not_change_npc_line_of_sight() -> None:
    engine = GameEngine()
    wolf = first_wolf(engine)
    player = engine.player
    assert player is not None
    y = ARENA_Y
    left = ARENA_X
    right = ARENA_X + 20
    carve_floor_rect(engine, left, y, right, y)
    wall_x = ARENA_X + 10
    engine.game_map.tiles[y, wall_x] = Tile.WALL
    wolf.components[Position] = Position(left, y)
    player.components[Position] = Position(right, y)
    wolf_pos = wolf.components[Position]
    player_pos = player.components[Position]
    before = can_see(
        engine.game_map,
        wolf_pos.x,
        wolf_pos.y,
        player_pos.x,
        player_pos.y,
    )
    assert not before
    engine._debug_omniscient_vision = True
    engine._update_fov()
    after = can_see(
        engine.game_map,
        wolf_pos.x,
        wolf_pos.y,
        player_pos.x,
        player_pos.y,
    )
    assert engine.game_map.visible.all()
    assert after == before


def test_toggle_omniscient_vision_restores_normal_fov() -> None:
    engine = GameEngine()
    engine._toggle_debug_omniscient_vision()
    assert engine._debug_omniscient_vision is True
    assert engine.game_map.visible.all()
    engine._toggle_debug_omniscient_vision()
    assert engine._debug_omniscient_vision is False
    assert not engine.game_map.visible.all()