"""Cosmetic hunt dart travel. Harvested from KDVR projectile_anim timing, not imported."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import attrs

from src.constants import DATA_DIR

HUNT_PROJECTILE_PATH = DATA_DIR / "hunt_projectile.json"


@attrs.define(frozen=True)
class HuntProjectileConfig:
    glyph: str = "*"
    fg: tuple[int, int, int] = (0, 255, 255)
    frames_per_tile: int = 1
    frame_sleep_seconds: float = 0.024


@lru_cache(maxsize=1)
def load_hunt_projectile(path: Path | None = None) -> HuntProjectileConfig:
    p = path if path is not None else HUNT_PROJECTILE_PATH
    if not p.is_file():
        return HuntProjectileConfig()
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return HuntProjectileConfig()
    fg_raw = raw.get("fg", [0, 255, 255])
    if not isinstance(fg_raw, list) or len(fg_raw) != 3:
        fg = (0, 255, 255)
    else:
        fg = (int(fg_raw[0]), int(fg_raw[1]), int(fg_raw[2]))
    glyph = str(raw.get("glyph", "*") or "*")[:1]
    return HuntProjectileConfig(
        glyph=glyph,
        fg=fg,
        frames_per_tile=max(1, int(raw.get("frames_per_tile", 1))),
        frame_sleep_seconds=float(raw.get("frame_sleep_seconds", 0.024)),
    )


def reset_hunt_projectile_cache() -> None:
    load_hunt_projectile.cache_clear()


@attrs.define
class HuntDartAnim:
    tiles: tuple[tuple[int, int], ...]
    tile_index: int = 0
    frames_left: int = 1
    active: bool = True


@attrs.define
class PendingHuntShot:
    blocked: bool
    hit_raptor: bool
    damage: int
    would_tranq_full: bool


def begin_dart(tiles: list[tuple[int, int]], *, frames_per_tile: int) -> HuntDartAnim | None:
    path = tuple((int(x), int(y)) for x, y in tiles)
    if not path:
        return None
    return HuntDartAnim(
        tiles=path,
        tile_index=0,
        frames_left=max(1, frames_per_tile),
        active=True,
    )


def advance_dart(anim: HuntDartAnim, *, frames_per_tile: int) -> bool:
    """Advance one cosmetic frame. True when the dart has finished traveling."""
    if not anim.active or not anim.tiles:
        anim.active = False
        return True
    anim.frames_left -= 1
    if anim.frames_left > 0:
        return False
    anim.tile_index += 1
    if anim.tile_index < len(anim.tiles):
        anim.frames_left = max(1, frames_per_tile)
        return False
    anim.active = False
    return True


def dart_draw_tiles(anim: HuntDartAnim) -> tuple[tuple[int, int], ...]:
    """Trail through the current tile (KDVR Path-beam pattern)."""
    if not anim.active or not anim.tiles:
        return ()
    end = min(anim.tile_index, len(anim.tiles) - 1)
    return anim.tiles[: end + 1]
