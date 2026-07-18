"""Visible map tile foreground colors (PR1 grey palette)."""

from __future__ import annotations

from src.map_gen import Tile
from src.systems.render import (
    DARK_DOOR,
    DARK_FLOOR,
    DARK_STAIRS,
    DARK_WALL,
    DARK_WATER,
    LIGHT_DOOR,
    LIGHT_FLOOR,
    LIGHT_STAIRS,
    LIGHT_WALL,
    LIGHT_WATER,
    _tile_glyph_and_fg,
)


def test_visible_floor_is_dark_grey() -> None:
    char, fg = _tile_glyph_and_fg(Tile.FLOOR, visible=True)
    assert char == "."
    assert fg == LIGHT_FLOOR == (72, 72, 72)


def test_visible_wall_is_mid_grey() -> None:
    char, fg = _tile_glyph_and_fg(Tile.WALL, visible=True)
    assert char == "#"
    assert fg == LIGHT_WALL == (120, 120, 120)


def test_visible_doors_are_mid_grey() -> None:
    closed_char, closed_fg = _tile_glyph_and_fg(Tile.DOOR_CLOSED, visible=True)
    open_char, open_fg = _tile_glyph_and_fg(Tile.DOOR_OPEN, visible=True)
    assert closed_char == "+"
    assert open_char == "-"
    assert closed_fg == open_fg == LIGHT_DOOR == (120, 120, 120)


def test_visible_stairs_and_water_unchanged() -> None:
    _, stairs_fg = _tile_glyph_and_fg(Tile.STAIRS_DOWN, visible=True)
    _, water_fg = _tile_glyph_and_fg(Tile.DEEP_WATER, visible=True)
    assert stairs_fg == LIGHT_STAIRS == (220, 200, 80)
    assert water_fg == LIGHT_WATER == (80, 140, 220)


def test_explored_only_colors_unchanged() -> None:
    _, wall_fg = _tile_glyph_and_fg(Tile.WALL, visible=False)
    _, floor_fg = _tile_glyph_and_fg(Tile.FLOOR, visible=False)
    _, door_fg = _tile_glyph_and_fg(Tile.DOOR_CLOSED, visible=False)
    _, stairs_fg = _tile_glyph_and_fg(Tile.STAIRS_DOWN, visible=False)
    _, water_fg = _tile_glyph_and_fg(Tile.DEEP_WATER, visible=False)
    assert wall_fg == DARK_WALL == (0, 0, 100)
    assert floor_fg == DARK_FLOOR == (50, 50, 150)
    assert door_fg == DARK_DOOR == (70, 50, 30)
    assert stairs_fg == DARK_STAIRS == (90, 80, 40)
    assert water_fg == DARK_WATER == (30, 60, 120)