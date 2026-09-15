"""Cone FOV with Bresenham occlusion."""

from __future__ import annotations

from src.hunt_facing import in_vision_cone, tile_along_heading
from src.hunt_map import HuntMap, is_long_grass


def _cheb(x0: int, y0: int, x1: int, y1: int) -> int:
    return max(abs(x1 - x0), abs(y1 - y0))


def line_tiles(x0: int, y0: int, x1: int, y1: int) -> list[tuple[int, int]]:
    points: list[tuple[int, int]] = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    x, y = x0, y0
    while True:
        points.append((x, y))
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy
    return points


def has_line_of_sight(
    mmap: HuntMap,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    *,
    grass_see_through: int = 2,
) -> bool:
    """True if trees/walls and too much consecutive long grass do not block.

    Origin grass does not count (standing in grass sees out more easily).
    Destination may be a tree. ``grass_see_through`` is how many consecutive
    long-grass tiles after the origin may be looked through.
    """
    line = line_tiles(x0, y0, x1, y1)
    consecutive = 0
    for x, y in line[1:]:
        if mmap.hard_opaque(x, y):
            return (x, y) == (x1, y1)
        if is_long_grass(mmap.terrain_at(x, y)):
            consecutive += 1
            if consecutive > grass_see_through:
                return False
        else:
            consecutive = 0
    return True


def line_visible(
    mmap: HuntMap,
    *,
    origin_x: int,
    origin_y: int,
    heading_deg: float,
    cone_range: int,
    close_blind: int,
    grass_see_through: int = 2,
) -> set[tuple[int, int]]:
    """Scoped FOV: Bresenham along heading. Close tiles are blind but the line continues."""
    seen: set[tuple[int, int]] = {(origin_x, origin_y)}
    end_x, end_y = tile_along_heading(origin_x, origin_y, heading_deg, max(1, cone_range))
    for x, y in line_tiles(origin_x, origin_y, end_x, end_y)[1:]:
        dist = _cheb(origin_x, origin_y, x, y)
        if dist > cone_range:
            break
        if not has_line_of_sight(
            mmap, origin_x, origin_y, x, y, grass_see_through=grass_see_through,
        ):
            if mmap.hard_opaque(x, y) and dist > close_blind:
                seen.add((x, y))
            break
        if dist > close_blind:
            seen.add((x, y))
        if mmap.hard_opaque(x, y):
            break
    return seen


def visible_tiles(
    mmap: HuntMap,
    *,
    origin_x: int,
    origin_y: int,
    facing: int,
    cone_range: int,
    half_degrees: float,
    heading_deg: float | None = None,
    close_blind: int = 0,
    grass_see_through: int = 2,
) -> set[tuple[int, int]]:
    seen: set[tuple[int, int]] = {(origin_x, origin_y)}
    for y in range(max(0, origin_y - cone_range), min(mmap.height, origin_y + cone_range + 1)):
        for x in range(max(0, origin_x - cone_range), min(mmap.width, origin_x + cone_range + 1)):
            if not in_vision_cone(
                origin_x=origin_x,
                origin_y=origin_y,
                facing=facing,
                tile_x=x,
                tile_y=y,
                cone_range=cone_range,
                half_degrees=half_degrees,
                heading_deg=heading_deg,
                close_blind=close_blind,
            ):
                continue
            if has_line_of_sight(
                mmap, origin_x, origin_y, x, y,
                grass_see_through=grass_see_through,
            ):
                seen.add((x, y))
    return seen
