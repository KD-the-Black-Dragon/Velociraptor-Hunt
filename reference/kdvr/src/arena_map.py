"""Fixed 1×10 hallway map for the 1v1 arena."""

from __future__ import annotations

from src.map_gen import GameMap, Tile

ARENA_WIDTH = 10
ARENA_HEIGHT = 3
ARENA_WALK_Y = 1
ARENA_PLAYER_X = 0
ARENA_ENEMY_X = 9


def build_arena_map(*, aquatic_enemy: bool) -> GameMap:
    """Return a 10×3 map with a single floor row and wall borders."""
    game_map = GameMap(ARENA_WIDTH, ARENA_HEIGHT)
    for x in range(ARENA_WIDTH):
        game_map.tiles[ARENA_WALK_Y, x] = Tile.FLOOR
    for y in (0, ARENA_HEIGHT - 1):
        for x in range(ARENA_WIDTH):
            game_map.tiles[y, x] = Tile.WALL
    if aquatic_enemy:
        game_map.tiles[ARENA_WALK_Y, ARENA_ENEMY_X] = Tile.DEEP_WATER
    game_map.explored[:] = True
    game_map.enter_xy = (ARENA_PLAYER_X, ARENA_WALK_Y)
    return game_map