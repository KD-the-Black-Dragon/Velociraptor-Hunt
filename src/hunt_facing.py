"""Eight tank facings and vision-cone tests."""

from __future__ import annotations

import math

# Index 0 = north, then clockwise 45°. Screen y grows downward.
FACING_DELTAS: tuple[tuple[int, int], ...] = (
    (0, -1),
    (1, -1),
    (1, 0),
    (1, 1),
    (0, 1),
    (-1, 1),
    (-1, 0),
    (-1, -1),
)

FACING_NAMES: tuple[str, ...] = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")


def wrap_facing(index: int) -> int:
    return int(index) % 8


def rotate_facing(index: int, steps_clockwise: int) -> int:
    return wrap_facing(index + steps_clockwise)


def facing_delta(index: int) -> tuple[int, int]:
    return FACING_DELTAS[wrap_facing(index)]


def facing_name(index: int) -> str:
    return FACING_NAMES[wrap_facing(index)]


def heading_from_facing(index: int) -> float:
    """Degrees clockwise from north for an 8-tick facing."""
    return wrap_facing(index) * 45.0


def heading_toward(from_x: int, from_y: int, to_x: int, to_y: int) -> float:
    """Continuous heading in degrees (north 0, clockwise) toward a tile."""
    dx = to_x - from_x
    dy = to_y - from_y
    if dx == 0 and dy == 0:
        return 0.0
    return math.degrees(math.atan2(dx, -dy)) % 360.0


def angular_delta_deg(a: float, b: float) -> float:
    """Smallest absolute difference between two headings, in degrees."""
    return abs((a - b + 180.0) % 360.0 - 180.0)


def yaw_step_degrees(half_degrees: float) -> float:
    """Yaw by one-third of the cone width (two-thirds overlap; lose/gain one third)."""
    return (2.0 / 3.0) * float(half_degrees)


# Half of 45°: a shot heading is "generally" this 8-tick facing.
FACING_FIRE_HALF_DEGREES = 22.5


def heading_matches_facing(heading_deg: float, facing: int) -> bool:
    """True when the heading sits in this facing's 45° slice (inclusive edges)."""
    return angular_delta_deg(heading_deg, heading_from_facing(facing)) <= (
        FACING_FIRE_HALF_DEGREES + 1e-9
    )


def tile_along_heading(
    origin_x: int,
    origin_y: int,
    heading_deg: float,
    dist: int = 1,
) -> tuple[int, int]:
    """Nearest grid tile at Chebyshev `dist` along a continuous heading."""
    if dist <= 0:
        return origin_x, origin_y
    rad = math.radians(heading_deg % 360.0)
    dx = int(round(math.sin(rad) * dist))
    dy = int(round(-math.cos(rad) * dist))
    if dx == 0 and dy == 0:
        fdx, fdy = facing_delta(nearest_eight_facing(heading_deg))
        dx, dy = fdx * dist, fdy * dist
    return origin_x + dx, origin_y + dy


def nearest_eight_facing(degrees: float, rng=None) -> int:
    """Snap heading to an 8-tick facing. Exact half-ticks pick randomly if rng given."""
    deg = degrees % 360.0
    stepped = deg / 45.0
    frac = stepped - math.floor(stepped)
    if abs(frac - 0.5) <= 1e-9:
        lo = int(math.floor(stepped)) % 8
        hi = (lo + 1) % 8
        if rng is not None:
            return int(rng.choice((lo, hi)))
        return lo
    return int(round(stepped)) % 8


def next_eight_facing(degrees: float, steps_clockwise: int) -> int:
    """Next 8-tick facing in a rotate direction, from a continuous heading.

    On a tick, this is a normal wrap. Off a tick, the first tick strictly in
    that direction counts as the first step (no overshoot past it).
    """
    if steps_clockwise == 0:
        return nearest_eight_facing(degrees)
    unit = (degrees % 360.0) / 45.0
    eps = 1e-9
    if abs(unit - round(unit)) <= eps:
        return wrap_facing(int(round(unit)) + steps_clockwise)
    if steps_clockwise > 0:
        first = int(math.ceil(unit - eps)) % 8
        return wrap_facing(first + (steps_clockwise - 1))
    first = int(math.floor(unit + eps)) % 8
    return wrap_facing(first + (steps_clockwise + 1))


def facing_toward(from_x: int, from_y: int, to_x: int, to_y: int) -> int:
    """Nearest of eight facings from one tile toward another."""
    dx = to_x - from_x
    dy = to_y - from_y
    if dx == 0 and dy == 0:
        return 0
    ang = math.atan2(dx, -dy)
    return int(round(ang / (math.pi / 4.0))) % 8


def in_vision_cone(
    *,
    origin_x: int,
    origin_y: int,
    facing: int,
    tile_x: int,
    tile_y: int,
    cone_range: int,
    half_degrees: float,
    heading_deg: float | None = None,
    close_blind: int = 0,
) -> bool:
    """True when the tile is in the facing/heading cone (Chebyshev range). Own tile always counts."""
    dx = tile_x - origin_x
    dy = tile_y - origin_y
    if dx == 0 and dy == 0:
        return True
    dist = max(abs(dx), abs(dy))
    if dist > cone_range:
        return False
    if close_blind > 0 and dist <= close_blind:
        return False
    if heading_deg is None:
        fdx, fdy = facing_delta(facing)
        facing_rad = math.atan2(fdx, -fdy)
    else:
        facing_rad = math.radians(heading_deg)
    tile_rad = math.atan2(dx, -dy)
    delta = abs((tile_rad - facing_rad + math.pi) % (2 * math.pi) - math.pi)
    return delta <= math.radians(half_degrees) + 1e-9
