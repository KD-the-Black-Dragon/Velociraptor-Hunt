"""Arena map drawing for Gladiavore matches (no dungeon UI)."""

from __future__ import annotations

import tcod.console

from src.game_map import GameMap, Tile

LIGHT_WALL = (120, 120, 120)
LIGHT_FLOOR = (160, 140, 90)  # sand
LIGHT_PILLAR = (100, 100, 100)


def _glyph(tile: int) -> tuple[str, tuple[int, int, int]]:
    if tile == Tile.WALL:
        return "#", LIGHT_WALL
    if tile == Tile.FLOOR:
        return ".", LIGHT_FLOOR
    if tile == Tile.DOOR_CLOSED:
        return "+", LIGHT_PILLAR
    if tile == Tile.DOOR_OPEN:
        return "/", LIGHT_FLOOR
    if tile == Tile.DEEP_WATER:
        return "~", (80, 140, 220)
    if tile == Tile.STAIRS_DOWN:
        return ">", (220, 200, 80)
    return " ", (0, 0, 0)


def render_map(console: tcod.console.Console, game_map: GameMap) -> None:
    """Draw full map (matches always reveal the sand pit)."""
    for y in range(game_map.height):
        for x in range(game_map.width):
            if y >= console.height or x >= console.width:
                continue
            ch, fg = _glyph(int(game_map.tiles[y, x]))
            console.print(x, y, ch, fg=fg)
