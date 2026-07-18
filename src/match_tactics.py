"""PR5 space tactics: flanking angles, pushback, reaction helpers. No ZoC."""

from __future__ import annotations

import math
from collections.abc import Callable
from enum import Enum, auto

import attrs

from src.components import Position
from src.game_map import GameMap, Tile
from src.match_movement import can_entity_enter_tile


class ReactionKind(Enum):
    DODGE = auto()
    PARRY = auto()
    COUNTER = auto()
    IGNORE = auto()


@attrs.define
class PendingReaction:
    """Incoming attack on the PC awaiting a reaction choice."""

    attacker: object  # Entity
    attack_aut_cost: float
    damage_mult: float = 1.0
    accuracy_mult: float = 1.0
    style_label: str = "attack"
    # After choosing Dodge, wait for an open 8-way step.
    awaiting_dodge_dir: bool = False
    announce: str = ""


def vector_angle_deg(ax: int, ay: int, bx: int, by: int) -> float:
    """Angle in degrees between vectors A and B (0..180)."""
    dot = ax * bx + ay * by
    na = math.hypot(ax, ay)
    nb = math.hypot(bx, by)
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    cos_t = max(-1.0, min(1.0, dot / (na * nb)))
    return math.degrees(math.acos(cos_t))


def flank_accuracy_multiplier(
    attacker: Position,
    defender: Position,
    other_adjacent: list[Position],
) -> tuple[float, str]:
    """Angular separation flanking table (design §7.2).

    Returns (accuracy_mult, short note). Solo attacker → 1.0.
    """
    vax = attacker.x - defender.x
    vay = attacker.y - defender.y
    if not other_adjacent:
        return 1.0, ""

    best_ang = 0.0
    for other in other_adjacent:
        obx = other.x - defender.x
        oby = other.y - defender.y
        ang = vector_angle_deg(vax, vay, obx, oby)
        if ang > best_ang:
            best_ang = ang

    # Bins: ~45 penalty, ~90 bonus, ~135 bigger, ~180 biggest
    if best_ang < 67.5:  # includes ~45
        return 0.85, "crowded angle"
    if best_ang < 112.5:  # ~90
        return 1.12, "flank"
    if best_ang < 157.5:  # ~135
        return 1.22, "strong flank"
    return 1.35, "opposite flank"


def chebyshev(a: Position, b: Position) -> int:
    return max(abs(a.x - b.x), abs(a.y - b.y))


def is_open_dodge_tile(
    game_map: GameMap,
    entity: object,
    x: int,
    y: int,
    *,
    blocked: bool,
) -> bool:
    """Dodge destination must be walkable and unoccupied."""
    if blocked:
        return False
    return can_entity_enter_tile(game_map, x, y, entity)  # type: ignore[arg-type]


def push_direction(attacker: Position, defender: Position) -> tuple[int, int]:
    dx = _sign(defender.x - attacker.x)
    dy = _sign(defender.y - attacker.y)
    if dx == 0 and dy == 0:
        return (0, 0)
    return (dx, dy)


def resolve_pushback(
    game_map: GameMap,
    mover: object,
    from_pos: Position,
    dx: int,
    dy: int,
    *,
    tiles: int,
    is_blocked: Callable[[int, int], bool],
) -> tuple[Position, int, bool]:
    """Push up to ``tiles`` steps. Returns (new_pos, wall_bonus_damage, moved).

    Wall/hazard: attempting to enter a wall tile deals bonus damage and stops.
    """
    x, y = from_pos.x, from_pos.y
    wall_dmg = 0
    moved = False
    for _ in range(max(0, tiles)):
        nx, ny = x + dx, y + dy
        if not (0 <= nx < game_map.width and 0 <= ny < game_map.height):
            wall_dmg += 2
            break
        tile = game_map.tiles[ny, nx]
        if tile == Tile.WALL:
            wall_dmg += 2
            break
        if is_blocked(nx, ny):
            break
        if not can_entity_enter_tile(game_map, nx, ny, mover):  # type: ignore[arg-type]
            # treat non-enterable as solid-ish
            wall_dmg += 1
            break
        x, y = nx, ny
        moved = True
    return Position(x, y), wall_dmg, moved


def dodge_fatigue_cost(*, dodges_this_match: int, recent_dodges: int) -> float:
    """Stamina cost for a dodge; scales with repeated / multi pressure."""
    base = 1.0
    return base + 0.5 * max(0, dodges_this_match - 1) + 0.75 * max(0, recent_dodges)


def _sign(v: int) -> int:
    if v > 0:
        return 1
    if v < 0:
        return -1
    return 0
