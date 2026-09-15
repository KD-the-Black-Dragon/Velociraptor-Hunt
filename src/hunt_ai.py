"""Raptor mind: heatmap guess, staged stalk, danger-close rush."""

from __future__ import annotations

import json
import random
from functools import lru_cache
from pathlib import Path

import attrs

from src import messages as msg
from src.constants import DATA_DIR
from src.hunt_aut import load_hunt_aut_costs, tenths
from src.hunt_fov import line_visible, visible_tiles
from src.hunt_weather import aut_until_light
from src.hunt_clock import RingState, center_weight, load_hunt_clock
from src.hunt_combat import chebyshev
from src.hunt_facing import FACING_DELTAS, facing_delta, facing_toward, rotate_facing
from src.hunt_heatmap import (
    apply_gunshot,
    best_tile,
    clip_to_reach,
    collapse,
    ensure_maps,
    mark_scans,
    paint_flat_disk,
    sound_plausible,
)
from src.hunt_map import HuntMap, is_long_grass
from src.hunt_raptor import HuntRaptor, raptor_try_step
from src.hunt_stance import AIM_NONE, Gait

HUNT_AI_PATH = DATA_DIR / "hunt_ai.json"


@attrs.define(frozen=True)
class HuntAiConfig:
    habit_observations: int = 8
    habit_ratio: float = 0.6
    stare_streak: int = 6
    edge_weight: float = 0.35
    danger_close: int = 4
    observe_clock_frac: float = 0.33
    sprint_close: int = 5
    gunshot_jitter: int = 3
    gunshot_blur: int = 4
    scan_memory_aut: float = 8.0
    max_observe_dist: int = 7
    speed_mult: float = 2.0
    double_step_aut: float = 2.0
    hide_sit_turns: int = 5
    bait_chance: float = 0.08
    rain_lead_aut: float = 8.0


@attrs.define
class RaptorSense:
    hunter_x: int
    hunter_y: int
    hunter_facing: int
    hunter_aim_depth: int
    hunter_weapon_id: str
    hunter_gait: str
    hunter_sees_raptor: bool
    ring: RingState
    hunter_ring: float
    raptor_ring: float
    clock_remaining: float
    heard_xy: tuple[int, int] | None = None
    gunshot_xy: tuple[int, int] | None = None
    world_aut: float = 0.0
    clock_duration: float = 320.0
    definitely_margin: float = 12.0
    lock_gait: bool = False
    rain_id: str = "medium"
    grass_see_through: int = 2
    under_fire: bool = False
    hunter_cone_range: int = 12
    hunter_cone_half: float = 55.0
    hunter_heading: float | None = None
    hunter_grass_see: int = 2
    hunter_close_blind: int = 0
    speed_mult: float = 2.0
    los_hot_aut: float = 6.0
    stalk_watch: int = 6
    rain_lead_aut: float = 8.0
    cycle_aut: float = 40.0
    double_step_aut: float = 2.0


@lru_cache(maxsize=1)
def load_hunt_ai(path: Path | None = None) -> HuntAiConfig:
    p = path if path is not None else HUNT_AI_PATH
    if not p.is_file():
        return HuntAiConfig()
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return HuntAiConfig()
    return HuntAiConfig(
        habit_observations=int(raw.get("habit_observations", 8)),
        habit_ratio=float(raw.get("habit_ratio", 0.6)),
        stare_streak=int(raw.get("stare_streak", 6)),
        edge_weight=float(raw.get("edge_weight", 0.35)),
        danger_close=int(raw.get("danger_close", 4)),
        observe_clock_frac=float(raw.get("observe_clock_frac", 0.33)),
        sprint_close=int(raw.get("sprint_close", 5)),
        gunshot_jitter=int(raw.get("gunshot_jitter", 3)),
        gunshot_blur=int(raw.get("gunshot_blur", 4)),
        scan_memory_aut=float(raw.get("scan_memory_aut", 8.0)),
        max_observe_dist=int(raw.get("max_observe_dist", 7)),
        speed_mult=float(raw.get("speed_mult", 2.0)),
        double_step_aut=float(raw.get("double_step_aut", 2.0)),
        hide_sit_turns=int(raw.get("hide_sit_turns", 5)),
        bait_chance=float(raw.get("bait_chance", 0.08)),
        rain_lead_aut=float(raw.get("rain_lead_aut", 8.0)),
    )


def reset_hunt_ai_cache() -> None:
    load_hunt_ai.cache_clear()


def certain_time_loss(
    hunter_ring: float,
    raptor_ring: float,
    remaining: float,
    margin: float,
) -> bool:
    rem = max(0.0, remaining)
    return hunter_ring - (raptor_ring + rem) >= margin - 1e-9


def _rotate_toward(current: int, desired: int) -> int:
    if current == desired:
        return current
    cw = (desired - current) % 8
    ccw = (current - desired) % 8
    if cw <= ccw:
        return rotate_facing(current, 1)
    return rotate_facing(current, -1)


def _set_gait(raptor: HuntRaptor, gait: Gait, sense: RaptorSense) -> None:
    if not sense.lock_gait:
        raptor.gait = gait


def _aut_for(raptor: HuntRaptor, kind: str) -> float:
    costs = load_hunt_aut_costs()
    if kind == "rotate":
        base = costs.rotate_45
    elif kind == "wait":
        base = costs.wait
    else:
        base = costs.step_for(raptor.gait.value)
    mult = max(1.0, float(getattr(raptor, "speed_mult", 2.0) or 2.0))
    return tenths(base / mult)


def _extra_blocked(
    raptor: HuntRaptor,
    blocked: set[tuple[int, int]],
    danger: set[tuple[int, int]],
    avoid: bool,
) -> set[tuple[int, int]]:
    extra = set(blocked)
    if avoid and danger and (raptor.x, raptor.y) not in danger:
        extra |= danger
    return extra


def _remembered_hunter_los(raptor: HuntRaptor, mmap: HuntMap) -> set[tuple[int, int]]:
    mind = raptor.mind
    if mind.last_seen_x is None or mind.last_seen_y is None:
        return set()
    ox, oy = mind.last_seen_x, mind.last_seen_y
    facings = list(mind.sweep_facings) if mind.sweep_facings else []
    if mind.last_seen_facing is not None:
        facings.append(mind.last_seen_facing)
    if not facings:
        facings = [0]
    tiles: set[tuple[int, int]] = set()
    for facing in set(facings):
        tiles |= visible_tiles(
            mmap,
            origin_x=ox,
            origin_y=oy,
            facing=facing,
            cone_range=max(2, mind.last_seen_cone),
            half_degrees=mind.last_seen_half,
            heading_deg=None,
            close_blind=mind.last_seen_blind,
            grass_see_through=mind.last_seen_grass,
        )
    if mind.last_seen_heading is not None:
        tiles |= line_visible(
            mmap,
            origin_x=ox,
            origin_y=oy,
            heading_deg=mind.last_seen_heading,
            cone_range=max(2, mind.last_seen_cone + 4),
            close_blind=0,
            grass_see_through=mind.last_seen_grass,
        )
    if mind.burn_x is not None and mind.burn_y is not None:
        tiles.add((mind.burn_x, mind.burn_y))
    return tiles


def _face_or_step(
    raptor: HuntRaptor,
    mmap: HuntMap,
    tx: int,
    ty: int,
    blocked: set[tuple[int, int]],
    *,
    danger: set[tuple[int, int]] | None = None,
    avoid: bool = False,
) -> str:
    """Move toward a tile. If the nose is in a tree, step around it (diag/side)."""
    hot = _extra_blocked(raptor, blocked, danger or set(), avoid)
    if raptor.x == tx and raptor.y == ty:
        raptor.last_aut = _aut_for(raptor, "wait")
        return "wait"
    here = chebyshev(raptor.x, raptor.y, tx, ty)
    here_hot = danger is not None and (raptor.x, raptor.y) in danger
    facing = raptor.facing
    diag = {rotate_facing(facing, -1), rotate_facing(facing, 1)}
    side = {rotate_facing(facing, -2), rotate_facing(facing, 2)}
    best_f: int | None = None
    best_score = None
    for f, (dx, dy) in enumerate(FACING_DELTAS):
        nx, ny = raptor.x + dx, raptor.y + dy
        if not mmap.walkable(nx, ny) or (nx, ny) in hot:
            continue
        d = chebyshev(nx, ny, tx, ty)
        progress = here - d
        score = progress * 10.0
        if f == facing:
            score += 3.0
        elif f in diag:
            score += 2.0
        elif f in side:
            score += 1.0
        elif f == rotate_facing(facing, 4):
            score -= 5.0
        if danger is not None and (nx, ny) not in danger:
            score += 2.5
        if here_hot and danger is not None and (nx, ny) not in danger:
            score += 6.0
        if best_score is None or score > best_score:
            best_score = score
            best_f = f
    if best_f is None:
        desired = facing_toward(raptor.x, raptor.y, tx, ty)
        raptor.facing = _rotate_toward(raptor.facing, desired)
        raptor.last_aut = _aut_for(raptor, "rotate")
        return "rotate"
    if best_f == facing or best_f in diag or best_f in side:
        dx, dy = facing_delta(best_f)
        if raptor_try_step(raptor, mmap, dx, dy, blocked=hot):
            raptor.last_aut = _aut_for(raptor, "step")
            return "step"
    raptor.facing = _rotate_toward(raptor.facing, best_f)
    raptor.last_aut = _aut_for(raptor, "rotate")
    return "rotate"


def _sidestep_around(
    raptor: HuntRaptor,
    mmap: HuntMap,
    hx: int,
    hy: int,
    blocked: set[tuple[int, int]],
    *,
    prefer_far: bool,
    danger: set[tuple[int, int]] | None = None,
    avoid: bool = False,
) -> None:
    desired = facing_toward(raptor.x, raptor.y, hx, hy)
    if raptor.facing != desired:
        raptor.facing = _rotate_toward(raptor.facing, desired)
        raptor.last_aut = _aut_for(raptor, "rotate")
        return
    hot = _extra_blocked(raptor, blocked, danger or set(), avoid)
    here = chebyshev(raptor.x, raptor.y, hx, hy)
    best_sign = 0
    best_score = None
    for sign in (-1, 1):
        d = rotate_facing(raptor.facing, sign * 2)
        dx, dy = facing_delta(d)
        nx, ny = raptor.x + dx, raptor.y + dy
        if not mmap.walkable(nx, ny) or (nx, ny) in hot:
            continue
        dist = chebyshev(nx, ny, hx, hy)
        score = dist if prefer_far else -dist
        if danger and (nx, ny) not in danger:
            score += 4.0
        if best_score is None or score > best_score:
            best_score = score
            best_sign = sign
    if best_sign == 0:
        raptor.last_aut = _aut_for(raptor, "wait")
        return
    dx, dy = facing_delta(rotate_facing(raptor.facing, best_sign * 2))
    raptor_try_step(raptor, mmap, dx, dy, blocked=hot)
    raptor.last_aut = _aut_for(raptor, "step")
    _ = here


def _step_maximize_distance(
    raptor: HuntRaptor,
    mmap: HuntMap,
    hx: int,
    hy: int,
    blocked: set[tuple[int, int]],
    *,
    danger: set[tuple[int, int]] | None = None,
    avoid: bool = False,
) -> None:
    hot = _extra_blocked(raptor, blocked, danger or set(), avoid)
    here = chebyshev(raptor.x, raptor.y, hx, hy)
    best: tuple[int, int, int] | None = None
    best_d = here
    for facing, (dx, dy) in enumerate(FACING_DELTAS):
        nx, ny = raptor.x + dx, raptor.y + dy
        if not mmap.walkable(nx, ny) or (nx, ny) in hot:
            continue
        d = chebyshev(nx, ny, hx, hy)
        if danger and (nx, ny) not in danger:
            d += 2
        if d > best_d:
            best_d = d
            best = (nx, ny, facing)
    if best is None:
        _sidestep_around(
            raptor, mmap, hx, hy, blocked, prefer_far=True, danger=danger, avoid=avoid,
        )
        return
    _nx, _ny, facing = best
    if raptor.facing != facing:
        raptor.facing = _rotate_toward(raptor.facing, facing)
        raptor.last_aut = _aut_for(raptor, "rotate")
        return
    dx, dy = facing_delta(facing)
    raptor_try_step(raptor, mmap, dx, dy, blocked=hot)
    raptor.last_aut = _aut_for(raptor, "step")


def _look_at(
    raptor: HuntRaptor, tx: int, ty: int,
) -> bool:
    desired = facing_toward(raptor.x, raptor.y, tx, ty)
    if raptor.facing == desired:
        return True
    raptor.facing = _rotate_toward(raptor.facing, desired)
    raptor.last_aut = _aut_for(raptor, "rotate")
    return False


def _strafe(
    raptor: HuntRaptor,
    mmap: HuntMap,
    blocked: set[tuple[int, int]],
    *,
    look: tuple[int, int],
    dest: tuple[int, int] | None,
    prefer_far_from: tuple[int, int] | None,
    danger: set[tuple[int, int]] | None = None,
    avoid: bool = False,
) -> None:
    """Keep facing `look` and sidestep, optionally toward dest / away from a tile."""
    if not _look_at(raptor, look[0], look[1]):
        return
    hot = _extra_blocked(raptor, blocked, danger or set(), avoid)
    best_sign = 0
    best_score = None
    for sign in (-1, 1):
        d = rotate_facing(raptor.facing, sign * 2)
        dx, dy = facing_delta(d)
        nx, ny = raptor.x + dx, raptor.y + dy
        if not mmap.walkable(nx, ny) or (nx, ny) in hot:
            continue
        score = 0.0
        if dest is not None:
            score -= chebyshev(nx, ny, dest[0], dest[1])
        if prefer_far_from is not None:
            score += 1.5 * chebyshev(nx, ny, prefer_far_from[0], prefer_far_from[1])
        if is_long_grass(mmap.terrain_at(nx, ny)):
            score += 0.4
        if danger and (nx, ny) not in danger:
            score += 5.0
        if best_score is None or score > best_score:
            best_score = score
            best_sign = sign
    if best_sign == 0:
        raptor.last_aut = _aut_for(raptor, "wait")
        return
    dx, dy = facing_delta(rotate_facing(raptor.facing, best_sign * 2))
    raptor_try_step(raptor, mmap, dx, dy, blocked=hot)
    raptor.last_aut = _aut_for(raptor, "step")


def _on_cover(mmap: HuntMap, raptor: HuntRaptor) -> bool:
    return any((x, y) == (raptor.x, raptor.y) for x, y, _f in mmap.hide_spots)


def _nearest_cover(
    mmap: HuntMap,
    raptor: HuntRaptor,
    hunter_xy: tuple[int, int] | None,
    danger: set[tuple[int, int]],
) -> tuple[int, int] | None:
    """Closest 3-deep hide, preferring tiles not in remembered hunter LOS."""
    best = None
    best_score = None
    for x, y, _facing in mmap.hide_spots:
        if (x, y) == (raptor.x, raptor.y):
            continue
        score = float(chebyshev(x, y, raptor.x, raptor.y))
        if (x, y) in danger:
            score += 8.0
        if hunter_xy is not None:
            score += 0.05 * chebyshev(x, y, hunter_xy[0], hunter_xy[1])
        if best_score is None or score < best_score:
            best_score = score
            best = (x, y)
    if best is not None:
        return best
    return _nearest_grass(mmap, raptor.x, raptor.y, toward=hunter_xy)


def _pick_hide(
    mmap: HuntMap,
    raptor: HuntRaptor,
    *,
    hunter_xy: tuple[int, int] | None,
    other_angle: bool,
) -> tuple[int, int] | None:
    spots = mmap.hide_spots
    if spots:
        ranked: list[tuple[float, int, int]] = []
        for x, y, facing in spots:
            if (x, y) == (raptor.x, raptor.y):
                continue
            score = 0.0
            if hunter_xy is not None:
                hx, hy = hunter_xy
                here = facing_toward(hx, hy, raptor.x, raptor.y)
                there = facing_toward(hx, hy, x, y)
                span = min((there - here) % 8, (here - there) % 8)
                if other_angle:
                    score -= span
                score += 0.05 * chebyshev(x, y, hx, hy)
            score += 0.02 * chebyshev(x, y, raptor.x, raptor.y)
            ranked.append((score, x, y))
        if ranked:
            ranked.sort()
            return ranked[0][1], ranked[0][2]
    return _nearest_grass(mmap, raptor.x, raptor.y, toward=hunter_xy)


def _center_ring_tile(
    mmap: HuntMap,
    raptor: HuntRaptor,
    *,
    radius: int,
    rng: random.Random,
) -> tuple[int, int]:
    cx, cy = mmap.center_x, mmap.center_y
    best = (cx, cy)
    best_score = None
    for y in range(mmap.height):
        for x in range(mmap.width):
            if not mmap.walkable(x, y):
                continue
            d = chebyshev(x, y, cx, cy)
            if abs(d - radius) > 2:
                continue
            score = -abs(d - radius) + rng.random() * 0.2
            if is_long_grass(mmap.terrain_at(x, y)):
                score += 0.3
            if (x, y) == (raptor.x, raptor.y):
                score -= 0.5
            if best_score is None or score > best_score:
                best_score = score
                best = (x, y)
    return best


def _behind_tile(sense: RaptorSense, dist: int) -> tuple[int, int]:
    dx, dy = facing_delta((sense.hunter_facing + 4) % 8)
    return sense.hunter_x + dx * dist, sense.hunter_y + dy * dist


def _nearest_grass(
    mmap: HuntMap,
    x: int,
    y: int,
    *,
    toward: tuple[int, int] | None = None,
) -> tuple[int, int] | None:
    best = None
    best_score = None
    for gy in range(mmap.height):
        for gx in range(mmap.width):
            if not is_long_grass(mmap.terrain_at(gx, gy)):
                continue
            d = chebyshev(gx, gy, x, y)
            extra = 0
            if toward is not None:
                extra = chebyshev(gx, gy, toward[0], toward[1])
            score = d + extra * 0.5
            if best_score is None or score < best_score:
                best_score = score
                best = (gx, gy)
    return best


def _update_profile(
    raptor: HuntRaptor,
    mmap: HuntMap,
    sense: RaptorSense,
    cfg: HuntAiConfig,
) -> None:
    if not raptor.sees(sense.hunter_x, sense.hunter_y):
        return
    mind = raptor.mind
    mind.last_seen_x = sense.hunter_x
    mind.last_seen_y = sense.hunter_y
    mind.last_seen_facing = sense.hunter_facing
    mind.last_seen_aim = sense.hunter_aim_depth
    mind.last_seen_heading = sense.hunter_heading
    mind.last_seen_cone = sense.hunter_cone_range
    mind.last_seen_half = sense.hunter_cone_half
    mind.last_seen_grass = sense.hunter_grass_see
    mind.last_seen_blind = sense.hunter_close_blind
    sweep = list(mind.sweep_facings) + [sense.hunter_facing]
    mind.sweep_facings = tuple(sweep[-6:])
    if sense.hunter_sees_raptor:
        mind.burn_x, mind.burn_y = raptor.x, raptor.y
        mind.burn_aut = sense.world_aut
    mind.observations += 1
    busy = sense.hunter_gait in ("run", "quick") or (
        mind.last_obs_facing is not None and mind.last_obs_facing != sense.hunter_facing
    )
    if busy or sense.hunter_aim_depth > AIM_NONE:
        mind.hunter_busy = min(12, mind.hunter_busy + 1)
        mind.stare_streak = 0
        mind.stalk_watch = 0
    else:
        mind.hunter_busy = max(0, mind.hunter_busy - 1)
        mind.stare_streak += 1
        mind.stalk_watch += 1
    if mind.last_obs_facing is not None and mind.last_obs_facing != sense.hunter_facing:
        mind.rotate_hits += 1
    mind.last_obs_facing = sense.hunter_facing
    if center_weight(mmap, sense.hunter_x, sense.hunter_y) <= cfg.edge_weight:
        mind.edge_hits += 1


def _hunter_print_in_cone(
    raptor: HuntRaptor,
    prints: list | None,
) -> tuple[int, int] | None:
    if not prints:
        return None
    best = None
    best_aut = -1.0
    for print_ in prints:
        if getattr(print_, "owner", "") != "hunter":
            continue
        if not raptor.sees(print_.x, print_.y):
            continue
        placed = float(getattr(print_, "placed_aut", 0.0))
        if placed >= best_aut:
            best_aut = placed
            best = (print_.x, print_.y)
    return best


def raptor_act(
    raptor: HuntRaptor,
    mmap: HuntMap,
    *,
    sense: RaptorSense,
    rng: random.Random,
    prints: list | None = None,
    range_penalty: int = 0,
    cfg: HuntAiConfig | None = None,
) -> None:
    ox, oy = raptor.x, raptor.y
    try:
        _raptor_act_body(
            raptor,
            mmap,
            sense=sense,
            rng=rng,
            prints=prints,
            range_penalty=range_penalty,
            cfg=cfg,
        )
    finally:
        raptor.record_motion(ox, oy)


def _raptor_act_body(
    raptor: HuntRaptor,
    mmap: HuntMap,
    *,
    sense: RaptorSense,
    rng: random.Random,
    prints: list | None,
    range_penalty: int,
    cfg: HuntAiConfig | None,
) -> None:
    ai = cfg if cfg is not None else load_hunt_ai()
    costs = load_hunt_aut_costs()
    raptor.speed_mult = sense.speed_mult
    raptor.refresh_fov(
        mmap,
        range_penalty=range_penalty,
        grass_see_through=sense.grass_see_through,
    )
    blocked = {(sense.hunter_x, sense.hunter_y)}
    ensure_maps(raptor, mmap)
    _update_profile(raptor, mmap, sense, ai)
    seen = raptor.sees(sense.hunter_x, sense.hunter_y)
    dist = chebyshev(raptor.x, raptor.y, sense.hunter_x, sense.hunter_y)
    mind = raptor.mind
    heave = certain_time_loss(
        sense.hunter_ring, sense.raptor_ring, sense.clock_remaining, sense.definitely_margin,
    )

    hunter_xy = (sense.hunter_x, sense.hunter_y) if seen else None
    mark_scans(raptor, mmap, world_aut=sense.world_aut, hunter_xy=hunter_xy)

    thought = msg.hunt_thought_scan()
    ignored_sound = False

    if seen:
        collapse(
            raptor, mmap, sense.hunter_x, sense.hunter_y,
            radius=0, world_aut=sense.world_aut,
        )
    else:
        print_xy = _hunter_print_in_cone(raptor, prints)
        if print_xy is not None:
            collapse(
                raptor, mmap, print_xy[0], print_xy[1],
                radius=1, world_aut=sense.world_aut,
            )
            thought = msg.hunt_thought_print()
        elif sense.gunshot_xy is not None:
            apply_gunshot(
                raptor,
                mmap,
                sense.gunshot_xy,
                rng=rng,
                jitter=ai.gunshot_jitter,
                blur=ai.gunshot_blur,
                world_aut=sense.world_aut,
            )
            thought = msg.hunt_thought_gunshot()
        elif sense.heard_xy is not None:
            hx, hy = sense.heard_xy
            window = sense.double_step_aut or ai.double_step_aut
            doubled = (
                mind.last_heard_x is not None
                and mind.last_heard_y is not None
                and (sense.world_aut - mind.last_heard_aut) <= window
                and chebyshev(hx, hy, mind.last_heard_x, mind.last_heard_y) <= 1
            )
            if doubled:
                mx = (hx + mind.last_heard_x) // 2
                my = (hy + mind.last_heard_y) // 2
                collapse(
                    raptor, mmap, mx, my,
                    radius=1, world_aut=sense.world_aut,
                )
                thought = msg.hunt_thought_sound()
            mind.last_heard_x, mind.last_heard_y = hx, hy
            mind.last_heard_aut = sense.world_aut
            if not doubled:
                if sound_plausible(
                    raptor, mmap, hx, hy,
                    world_aut=sense.world_aut,
                    run_cost=costs.run,
                    memory=ai.scan_memory_aut,
                ):
                    paint_flat_disk(raptor, mmap, hx, hy, radius=1, weight=0.85)
                    thought = msg.hunt_thought_sound()
                else:
                    ignored_sound = True
                    thought = msg.hunt_thought_ignore_sound()

    clip_to_reach(raptor, mmap, world_aut=sense.world_aut, run_cost=costs.run)
    target = best_tile(raptor, mmap)

    danger = _remembered_hunter_los(raptor, mmap)

    def go(tx: int, ty: int, *, avoid: bool = False) -> None:
        _face_or_step(raptor, mmap, tx, ty, blocked, danger=danger, avoid=avoid)

    turtle = (
        sense.rain_id != "light"
        and aut_until_light(sense.world_aut, cycle_aut=sense.cycle_aut) <= sense.rain_lead_aut
    ) or sense.rain_id == "light"
    behind = facing_toward(
        sense.hunter_x, sense.hunter_y, raptor.x, raptor.y,
    ) in (
        (sense.hunter_facing + 3) % 8,
        (sense.hunter_facing + 4) % 8,
        (sense.hunter_facing + 5) % 8,
    )
    run_aut = max(0.1, costs.run / max(1.0, raptor.speed_mult))
    can_commit = (
        (raptor.x, raptor.y) not in danger
        and dist * run_aut < 1.6
    )

    # --- intent ---
    if seen and dist <= ai.danger_close:
        mind.intent = "rush"
        thought = msg.hunt_thought_rush()
        _set_gait(raptor, Gait.RUN, sense)
        go(sense.hunter_x, sense.hunter_y)
    elif (
        seen
        and sense.rain_id == "heavy"
        and not sense.hunter_sees_raptor
        and behind
        and can_commit
        and not turtle
    ):
        mind.intent = "rush"
        thought = msg.hunt_thought_sprint_in()
        _set_gait(raptor, Gait.RUN, sense)
        go(sense.hunter_x, sense.hunter_y)
    elif heave:
        mind.intent = "heave"
        thought = msg.hunt_thought_heave()
        _set_gait(raptor, Gait.RUN, sense)
        if seen:
            go(sense.hunter_x, sense.hunter_y)
        elif target is not None:
            go(target[0], target[1])
        else:
            go(mmap.center_x, mmap.center_y)
    elif sense.under_fire or (seen and sense.hunter_aim_depth > AIM_NONE):
        _set_gait(raptor, Gait.RUN, sense)
        known = (sense.hunter_x, sense.hunter_y) if seen else target
        if not _on_cover(mmap, raptor):
            mind.intent = "cover"
            thought = msg.hunt_thought_cover()
            cover = _nearest_cover(mmap, raptor, known, danger)
            if cover is not None:
                go(cover[0], cover[1], avoid=True)
            else:
                _step_maximize_distance(
                    raptor, mmap, sense.hunter_x, sense.hunter_y, blocked,
                    danger=danger, avoid=True,
                )
        else:
            mind.intent = "break"
            thought = msg.hunt_thought_break()
            hide = _pick_hide(mmap, raptor, hunter_xy=known, other_angle=True)
            if hide is not None:
                go(hide[0], hide[1], avoid=True)
            else:
                _step_maximize_distance(
                    raptor, mmap, sense.hunter_x, sense.hunter_y, blocked,
                    danger=danger, avoid=True,
                )
    elif seen and mind.stare_streak >= ai.stare_streak and not sense.hunter_sees_raptor:
        if dist <= ai.sprint_close:
            mind.intent = "sprint_in"
            thought = msg.hunt_thought_sprint_in()
            _set_gait(raptor, Gait.RUN, sense)
            go(sense.hunter_x, sense.hunter_y)
        else:
            mind.intent = "sneak"
            thought = msg.hunt_thought_sneak()
            _set_gait(raptor, Gait.SNEAK, sense)
            bx, by = _behind_tile(sense, 1)
            go(bx, by)
    elif seen and mind.hunter_busy >= 3:
        mind.intent = "watch"
        thought = msg.hunt_thought_watch()
        _set_gait(raptor, Gait.WALK, sense)
        peak = target or (sense.hunter_x, sense.hunter_y)
        _strafe(
            raptor, mmap, blocked,
            look=peak,
            dest=None,
            prefer_far_from=(sense.hunter_x, sense.hunter_y),
            danger=danger,
            avoid=True,
        )
    elif seen and sense.hunter_sees_raptor:
        _set_gait(raptor, Gait.RUN, sense)
        known = (sense.hunter_x, sense.hunter_y)
        if not _on_cover(mmap, raptor):
            mind.intent = "cover"
            thought = msg.hunt_thought_cover()
            cover = _nearest_cover(mmap, raptor, known, danger)
            if cover is not None:
                go(cover[0], cover[1], avoid=True)
            else:
                _step_maximize_distance(
                    raptor, mmap, sense.hunter_x, sense.hunter_y, blocked,
                    danger=danger, avoid=True,
                )
        else:
            mind.intent = "circle"
            thought = msg.hunt_thought_circle()
            hide = _pick_hide(mmap, raptor, hunter_xy=known, other_angle=True)
            if hide is not None:
                go(hide[0], hide[1], avoid=True)
            else:
                _sidestep_around(
                    raptor, mmap, sense.hunter_x, sense.hunter_y, blocked,
                    prefer_far=True, danger=danger, avoid=True,
                )
    elif seen:
        mind.intent = "observe"
        thought = msg.hunt_thought_observe()
        _set_gait(raptor, Gait.SNEAK, sense)
        hide = _pick_hide(
            mmap, raptor, hunter_xy=(sense.hunter_x, sense.hunter_y), other_angle=False,
        )
        if hide is not None and dist < ai.max_observe_dist:
            go(hide[0], hide[1], avoid=True)
        elif dist < ai.max_observe_dist:
            _step_maximize_distance(
                raptor, mmap, sense.hunter_x, sense.hunter_y, blocked,
                danger=danger, avoid=True,
            )
        else:
            go(*_behind_tile(sense, 2), avoid=True)
    elif turtle:
        mind.intent = "hide"
        thought = msg.hunt_thought_hide()
        _set_gait(raptor, Gait.SNEAK, sense)
        hide = _pick_hide(mmap, raptor, hunter_xy=target, other_angle=False)
        on_hide = any((hx, hy) == (raptor.x, raptor.y) for hx, hy, _f in mmap.hide_spots)
        if on_hide and mind.hide_sit < ai.hide_sit_turns:
            mind.hide_sit += 1
            raptor.last_aut = _aut_for(raptor, "wait")
        elif hide is not None:
            mind.hide_sit = 0
            go(hide[0], hide[1], avoid=True)
        else:
            go(*_center_ring_tile(mmap, raptor, radius=8, rng=rng), avoid=True)
    elif sense.ring is RingState.RAPTOR_WINNING:
        mind.intent = "hide"
        thought = msg.hunt_thought_hide()
        _set_gait(raptor, Gait.SNEAK, sense)
        hide = _pick_hide(mmap, raptor, hunter_xy=target, other_angle=False)
        if hide is not None:
            go(hide[0], hide[1])
        else:
            go(*_center_ring_tile(mmap, raptor, radius=8, rng=rng))
    elif target is not None:
        mind.intent = "stalk"
        if thought == msg.hunt_thought_scan():
            thought = msg.hunt_thought_sound() if sense.heard_xy else thought
        _set_gait(raptor, Gait.WALK, sense)
        go(target[0], target[1])
    elif sense.rain_id == "heavy":
        mind.intent = "relay"
        thought = msg.hunt_thought_relay()
        _set_gait(raptor, Gait.RUN, sense)
        hide = _pick_hide(mmap, raptor, hunter_xy=None, other_angle=False)
        if hide is not None:
            go(hide[0], hide[1])
        else:
            go(*_center_ring_tile(mmap, raptor, radius=8, rng=rng))
    elif sense.ring is RingState.HUNTER_WINNING:
        mind.intent = "contest"
        thought = msg.hunt_thought_contest()
        _set_gait(raptor, Gait.WALK, sense)
        go(*_center_ring_tile(mmap, raptor, radius=4, rng=rng))
    else:
        mind.intent = "patrol"
        thought = msg.hunt_thought_patrol()
        _set_gait(raptor, Gait.WALK, sense)
        go(*_center_ring_tile(mmap, raptor, radius=8, rng=rng))

    if ignored_sound and mind.intent in ("scan", "stalk"):
        thought = msg.hunt_thought_ignore_sound()
    mind.thought = thought
