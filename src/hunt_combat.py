"""Deterministic hunt shot math and weapon combat data."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import attrs

from src.constants import DATA_DIR
from src.hunt_fov import line_tiles
from src.hunt_map import HuntMap, HuntTerrain
from src.hunt_fatigue import accuracy_penalty
from src.hunt_facing import angular_delta_deg, heading_from_facing
from src.hunt_stance import AIM_DEEP, AIM_FOCUS, AIM_NONE

HUNT_COMBAT_PATH = DATA_DIR / "hunt_combat.json"


@attrs.define(frozen=True)
class WeaponCombat:
    weapon_id: str
    ammo: int
    ideal_range_min: int
    ideal_range_max: int
    max_range: int
    base_damage: int
    per_tile_outside: int
    unaimed_penalty: int
    unaimed_cap: int
    aim_bonus: int
    deep_aim_bonus: int
    unaimed_extra_per_tile: int = 0
    rain_medium: int = 0
    rain_heavy: int = 0
    motion_penalty: int = 0
    perp_move_penalty: int = 0
    perp_stand_bonus: int = 0


@attrs.define(frozen=True)
class HuntCombatConfig:
    raptor_max_hp: int
    hunter_running_penalty: int
    weapons: dict[str, WeaponCombat]


@attrs.define(frozen=True)
class ShotPreview:
    range_chebyshev: int
    factors: tuple[str, ...]
    damage: int
    would_tranq_full: bool


@attrs.define(frozen=True)
class ShotResult:
    damage: int
    hit_raptor: bool
    blocked: bool
    factors: tuple[str, ...]
    range_chebyshev: int
    path: tuple[tuple[int, int], ...] = ()


def _weapon(raw: dict, weapon_id: str) -> WeaponCombat:
    return WeaponCombat(
        weapon_id=weapon_id,
        ammo=int(raw.get("ammo", 6)),
        ideal_range_min=int(raw.get("ideal_range_min", 1)),
        ideal_range_max=int(raw.get("ideal_range_max", 4)),
        max_range=int(raw.get("max_range", 8)),
        base_damage=int(raw.get("base_damage", 100)),
        per_tile_outside=int(raw.get("per_tile_outside", 15)),
        unaimed_penalty=int(raw.get("unaimed_penalty", 0)),
        unaimed_cap=int(raw.get("unaimed_cap", 0)),
        aim_bonus=int(raw.get("aim_bonus", 0)),
        deep_aim_bonus=int(raw.get("deep_aim_bonus", 0)),
        unaimed_extra_per_tile=int(raw.get("unaimed_extra_per_tile", 0)),
        rain_medium=int(raw.get("rain_medium", 0)),
        rain_heavy=int(raw.get("rain_heavy", 0)),
        motion_penalty=int(raw.get("motion_penalty", 0)),
        perp_move_penalty=int(raw.get("perp_move_penalty", 0)),
        perp_stand_bonus=int(raw.get("perp_stand_bonus", 0)),
    )


@lru_cache(maxsize=1)
def load_hunt_combat(path: Path | None = None) -> HuntCombatConfig:
    p = path if path is not None else HUNT_COMBAT_PATH
    raw = json.loads(p.read_text(encoding="utf-8"))
    weapons_raw = raw.get("weapons", {}) if isinstance(raw, dict) else {}
    weapons = {
        str(wid): _weapon(spec, str(wid))
        for wid, spec in weapons_raw.items()
        if isinstance(spec, dict)
    }
    return HuntCombatConfig(
        raptor_max_hp=int(raw.get("raptor_max_hp", 100)),
        hunter_running_penalty=int(raw.get("hunter_running_penalty", 30)),
        weapons=weapons,
    )


def reset_hunt_combat_cache() -> None:
    load_hunt_combat.cache_clear()


def weapon_combat(weapon_id: str) -> WeaponCombat:
    cfg = load_hunt_combat()
    if weapon_id in cfg.weapons:
        return cfg.weapons[weapon_id]
    return next(iter(cfg.weapons.values()))


def chebyshev(x0: int, y0: int, x1: int, y1: int) -> int:
    return max(abs(x1 - x0), abs(y1 - y0))


def _heading_is_perp(shot_heading: float | None, facing: int | None) -> bool:
    if shot_heading is None or facing is None:
        return False
    delta = angular_delta_deg(shot_heading, heading_from_facing(facing))
    return abs(delta - 90.0) <= 22.5 + 1e-9


def compute_damage(
    weapon: WeaponCombat,
    *,
    range_chebyshev: int,
    aim_depth: int,
    hunter_running: bool,
    hunter_fatigue: int = 0,
    rain_id: str = "light",
    raptor_moving: bool = False,
    raptor_facing: int | None = None,
    raptor_move_facing: int | None = None,
    shot_heading: float | None = None,
) -> int:
    damage = weapon.base_damage
    if range_chebyshev < weapon.ideal_range_min:
        damage -= (weapon.ideal_range_min - range_chebyshev) * weapon.per_tile_outside
    elif range_chebyshev > weapon.ideal_range_max:
        damage -= (range_chebyshev - weapon.ideal_range_max) * weapon.per_tile_outside
    if aim_depth <= AIM_NONE:
        damage -= weapon.unaimed_penalty
        if range_chebyshev > weapon.ideal_range_max:
            damage -= (range_chebyshev - weapon.ideal_range_max) * weapon.unaimed_extra_per_tile
        if weapon.unaimed_cap > 0:
            damage = min(damage, weapon.unaimed_cap)
    elif aim_depth >= AIM_DEEP:
        damage += weapon.deep_aim_bonus
    elif aim_depth >= AIM_FOCUS:
        damage += weapon.aim_bonus
    stacks = max(0, int(hunter_fatigue))
    if hunter_running and stacks <= 0:
        damage -= load_hunt_combat().hunter_running_penalty
    elif stacks > 0:
        damage -= accuracy_penalty(stacks)
    if rain_id == "heavy":
        damage -= weapon.rain_heavy
    elif rain_id == "medium":
        damage -= weapon.rain_medium
    if raptor_moving:
        damage -= weapon.motion_penalty
        if _heading_is_perp(shot_heading, raptor_move_facing):
            damage -= weapon.perp_move_penalty
    elif aim_depth > AIM_NONE and _heading_is_perp(shot_heading, raptor_facing):
        damage += weapon.perp_stand_bonus
    return max(0, damage)


def loose_factors(
    weapon: WeaponCombat,
    *,
    range_chebyshev: int,
    aim_depth: int,
    hunter_running: bool,
    raptor_visible: bool,
    ammo: int,
    hunter_fatigue: int = 0,
    rain_id: str = "light",
    raptor_moving: bool = False,
    raptor_facing: int | None = None,
    raptor_move_facing: int | None = None,
    shot_heading: float | None = None,
) -> tuple[str, ...]:
    lines: list[str] = [f"range {range_chebyshev}"]
    if aim_depth >= AIM_DEEP:
        lines.append("deep aim")
    elif aim_depth >= AIM_FOCUS:
        lines.append("aiming")
    else:
        lines.append("no aiming")
    if hunter_fatigue > 0:
        lines.append("out of breath")
    elif hunter_running:
        lines.append("you are running")
    if rain_id == "heavy" and weapon.rain_heavy:
        lines.append("heavy rain")
    elif rain_id == "medium" and weapon.rain_medium:
        lines.append("rain")
    if raptor_moving and weapon.motion_penalty:
        lines.append("raptor moving")
        if _heading_is_perp(shot_heading, raptor_move_facing) and weapon.perp_move_penalty:
            lines.append("crossing shot")
    elif aim_depth > AIM_NONE and _heading_is_perp(shot_heading, raptor_facing) and weapon.perp_stand_bonus:
        lines.append("side profile")
    if raptor_visible:
        lines.append("raptor in sight")
    else:
        lines.append("blind fire")
    if ammo <= 0:
        lines.append("no ammo")
    return tuple(lines)


def preview_shot(
    weapon: WeaponCombat,
    *,
    range_chebyshev: int,
    aim_depth: int,
    hunter_running: bool,
    raptor_visible: bool,
    ammo: int,
    hunter_fatigue: int = 0,
    rain_id: str = "light",
    raptor_moving: bool = False,
    raptor_facing: int | None = None,
    raptor_move_facing: int | None = None,
    shot_heading: float | None = None,
) -> ShotPreview:
    damage = compute_damage(
        weapon,
        range_chebyshev=range_chebyshev,
        aim_depth=aim_depth,
        hunter_running=hunter_running,
        hunter_fatigue=hunter_fatigue,
        rain_id=rain_id,
        raptor_moving=raptor_moving,
        raptor_facing=raptor_facing,
        raptor_move_facing=raptor_move_facing,
        shot_heading=shot_heading,
    )
    return ShotPreview(
        range_chebyshev=range_chebyshev,
        factors=loose_factors(
            weapon,
            range_chebyshev=range_chebyshev,
            aim_depth=aim_depth,
            hunter_running=hunter_running,
            raptor_visible=raptor_visible,
            ammo=ammo,
            hunter_fatigue=hunter_fatigue,
            rain_id=rain_id,
            raptor_moving=raptor_moving,
            raptor_facing=raptor_facing,
            raptor_move_facing=raptor_move_facing,
            shot_heading=shot_heading,
        ),
        damage=damage,
        would_tranq_full=damage >= load_hunt_combat().raptor_max_hp,
    )


def aim_ray_end(x0: int, y0: int, x1: int, y1: int, max_range: int) -> tuple[int, int]:
    """Endpoint of the aim line at max_range (cursor only sets direction)."""
    dx = x1 - x0
    dy = y1 - y0
    if dx == 0 and dy == 0 or max_range <= 0:
        return x0, y0
    step = max(abs(dx), abs(dy))
    fx, fy = dx / step, dy / step
    return (int(round(x0 + fx * max_range)), int(round(y0 + fy * max_range)))


def trace_projectile(
    mmap: HuntMap,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    *,
    raptor_xy: tuple[int, int] | None,
    max_range: int,
) -> ShotResult:
    """Linear path from the hunter through the cursor, out to max_range.

    Trees/walls block. A raptor anywhere on that ray is a valid hit (including blind).
    """
    end_x, end_y = aim_ray_end(x0, y0, x1, y1, max_range)
    line = line_tiles(x0, y0, end_x, end_y)
    blocked = False
    hit = False
    last_x, last_y = x0, y0
    path: list[tuple[int, int]] = []
    for i, (x, y) in enumerate(line):
        if i == 0:
            continue
        if chebyshev(x0, y0, x, y) > max_range:
            break
        last_x, last_y = x, y
        path.append((x, y))
        if raptor_xy is not None and (x, y) == raptor_xy:
            hit = True
            break
        terr = mmap.terrain_at(x, y)
        if terr is HuntTerrain.TREE or terr is HuntTerrain.WALL:
            blocked = True
            break
    rng = chebyshev(x0, y0, last_x, last_y)
    if hit and raptor_xy is not None:
        rng = chebyshev(x0, y0, raptor_xy[0], raptor_xy[1])
    return ShotResult(
        damage=0,
        hit_raptor=hit,
        blocked=blocked,
        factors=(),
        range_chebyshev=rng,
        path=tuple(path),
    )
