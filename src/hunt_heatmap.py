"""Raptor occupancy belief. Not player coordinates — a guess from fair clues."""

from __future__ import annotations

from typing import Any

import numpy as np

from src.hunt_combat import chebyshev
from src.hunt_map import HuntMap
from src.hunt_raptor import HuntRaptor


def ensure_maps(raptor: HuntRaptor, mmap: HuntMap) -> None:
    h, w = mmap.height, mmap.width
    if (
        raptor.belief is None
        or getattr(raptor.belief, "shape", None) != (h, w)
    ):
        raptor.belief = np.zeros((h, w), dtype=np.float32)
        raptor.scanned_aut = np.full((h, w), -1.0e9, dtype=np.float32)


def reach_radius(*, world_aut: float, fix_aut: float, run_cost: float) -> int:
    """How far a sprinting hunter could have gone since the last fix."""
    dt = max(0.0, world_aut - fix_aut)
    cost = max(0.1, run_cost)
    return int(dt / cost + 1e-9)


def collapse(
    raptor: HuntRaptor,
    mmap: HuntMap,
    x: int,
    y: int,
    *,
    radius: int,
    world_aut: float,
    weight: float = 1.0,
) -> None:
    ensure_maps(raptor, mmap)
    raptor.belief.fill(0.0)
    rad = max(0, int(radius))
    for ty in range(max(0, y - rad), min(mmap.height, y + rad + 1)):
        for tx in range(max(0, x - rad), min(mmap.width, x + rad + 1)):
            if chebyshev(tx, ty, x, y) > rad:
                continue
            if not mmap.walkable(tx, ty):
                continue
            raptor.belief[ty, tx] = weight
    raptor.mind.fix_x = x
    raptor.mind.fix_y = y
    raptor.mind.fix_aut = world_aut


def paint_flat_disk(
    raptor: HuntRaptor,
    mmap: HuntMap,
    cx: int,
    cy: int,
    *,
    radius: int,
    weight: float = 1.0,
) -> None:
    """Equal weight in the disk. Does not peak at the center."""
    ensure_maps(raptor, mmap)
    rad = max(0, int(radius))
    for ty in range(max(0, cy - rad), min(mmap.height, cy + rad + 1)):
        for tx in range(max(0, cx - rad), min(mmap.width, cx + rad + 1)):
            if chebyshev(tx, ty, cx, cy) > rad:
                continue
            if not mmap.walkable(tx, ty):
                continue
            raptor.belief[ty, tx] = max(float(raptor.belief[ty, tx]), weight)


def mark_scans(
    raptor: HuntRaptor,
    mmap: HuntMap,
    *,
    world_aut: float,
    hunter_xy: tuple[int, int] | None,
) -> None:
    ensure_maps(raptor, mmap)
    for x, y in raptor.visible:
        raptor.scanned_aut[y, x] = world_aut
        if hunter_xy is not None and (x, y) == hunter_xy:
            continue
        raptor.belief[y, x] *= 0.15


def clip_to_reach(
    raptor: HuntRaptor,
    mmap: HuntMap,
    *,
    world_aut: float,
    run_cost: float,
) -> None:
    fx, fy = raptor.mind.fix_x, raptor.mind.fix_y
    if fx is None or fy is None:
        return
    rad = reach_radius(
        world_aut=world_aut, fix_aut=raptor.mind.fix_aut, run_cost=run_cost,
    )
    ensure_maps(raptor, mmap)
    yy, xx = np.mgrid[0:mmap.height, 0:mmap.width]
    dist = np.maximum(np.abs(xx - fx), np.abs(yy - fy))
    raptor.belief[dist > rad] = 0.0


def recently_scanned(
    raptor: HuntRaptor,
    x: int,
    y: int,
    *,
    world_aut: float,
    memory: float,
) -> bool:
    if raptor.scanned_aut is None:
        return False
    if not (0 <= y < raptor.scanned_aut.shape[0] and 0 <= x < raptor.scanned_aut.shape[1]):
        return False
    return (world_aut - float(raptor.scanned_aut[y, x])) <= memory


def sound_plausible(
    raptor: HuntRaptor,
    mmap: HuntMap,
    x: int,
    y: int,
    *,
    world_aut: float,
    run_cost: float,
    memory: float,
) -> bool:
    if not mmap.walkable(x, y):
        return False
    if recently_scanned(raptor, x, y, world_aut=world_aut, memory=memory):
        return False
    fx, fy = raptor.mind.fix_x, raptor.mind.fix_y
    if fx is None or fy is None:
        return True
    rad = reach_radius(
        world_aut=world_aut, fix_aut=raptor.mind.fix_aut, run_cost=run_cost,
    )
    return chebyshev(x, y, fx, fy) <= rad + 1


def best_tile(raptor: HuntRaptor, mmap: HuntMap) -> tuple[int, int] | None:
    ensure_maps(raptor, mmap)
    if float(np.max(raptor.belief)) <= 1e-6:
        return None
    idx = int(np.argmax(raptor.belief))
    y, x = divmod(idx, mmap.width)
    if not mmap.walkable(x, y):
        return None
    return x, y


def apply_gunshot(
    raptor: HuntRaptor,
    mmap: HuntMap,
    true_xy: tuple[int, int],
    *,
    rng: Any,
    jitter: int,
    blur: int,
    world_aut: float,
) -> tuple[int, int]:
    """Jittered apparent center, then a flat blur disk. Returns apparent C."""
    tx, ty = true_xy
    spots: list[tuple[int, int]] = []
    j = max(0, int(jitter))
    for y in range(ty - j, ty + j + 1):
        for x in range(tx - j, tx + j + 1):
            if chebyshev(x, y, tx, ty) <= j and mmap.walkable(x, y):
                spots.append((x, y))
    if not spots:
        spots = [(tx, ty)] if mmap.walkable(tx, ty) else []
    if not spots:
        return tx, ty
    cx, cy = spots[int(rng.randrange(len(spots)))]
    ensure_maps(raptor, mmap)
    raptor.belief.fill(0.0)
    paint_flat_disk(raptor, mmap, cx, cy, radius=blur, weight=1.0)
    raptor.mind.fix_x = cx
    raptor.mind.fix_y = cy
    raptor.mind.fix_aut = world_aut
    return cx, cy
