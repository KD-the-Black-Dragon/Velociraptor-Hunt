"""Curated arena maps for Gladiavore matches (little procgen)."""

from __future__ import annotations

from src.game_map import GameMap, Tile

# Default sand pit (design: ~20×20).
SAND_PIT_WIDTH = 20
SAND_PIT_HEIGHT = 20

# Fixed pillar holes for cover (curated, not random).
_SAND_PIT_PILLARS: tuple[tuple[int, int], ...] = (
    (6, 6),
    (13, 6),
    (6, 13),
    (13, 13),
    (10, 10),
)


def build_sand_pit_map() -> GameMap:
    """Open sand rectangle with border walls and a few pillars."""
    w, h = SAND_PIT_WIDTH, SAND_PIT_HEIGHT
    game_map = GameMap(w, h)
    for y in range(h):
        for x in range(w):
            if x == 0 or y == 0 or x == w - 1 or y == h - 1:
                game_map.tiles[y, x] = Tile.WALL
            else:
                game_map.tiles[y, x] = Tile.FLOOR
    for px, py in _SAND_PIT_PILLARS:
        if 0 < px < w - 1 and 0 < py < h - 1:
            game_map.tiles[py, px] = Tile.WALL
    game_map.explored[:] = True
    game_map.visible[:] = True
    game_map.enter_xy = (2, h // 2)
    return game_map


def sand_pit_player_spawn() -> tuple[int, int]:
    return (2, SAND_PIT_HEIGHT // 2)


def sand_pit_enemy_spawns(count: int) -> list[tuple[int, int]]:
    """East-side spawn slots for opponents."""
    cx = SAND_PIT_WIDTH - 3
    mid = SAND_PIT_HEIGHT // 2
    if count <= 1:
        return [(cx, mid)]
    if count == 2:
        return [(cx, mid - 2), (cx, mid + 2)]
    # 3+
    slots = [(cx, mid - 3), (cx, mid), (cx, mid + 3)]
    while len(slots) < count:
        slots.append((cx - 1, mid + (len(slots) - 3)))
    return slots[:count]
