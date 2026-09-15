"""Circular jungle paddock generation."""

from __future__ import annotations

import json
import math
import random
from enum import Enum
from functools import lru_cache
from pathlib import Path

import attrs

from src.constants import DATA_DIR

HUNT_PADDOCK_PATH = DATA_DIR / "hunt_paddock.json"


class HuntTerrain(Enum):
    WALL = "wall"
    OPEN = "open"
    MUD = "mud"
    GRASS = "grass"
    BUSH = "bush"
    TREE = "tree"


WALKABLE = frozenset({HuntTerrain.OPEN, HuntTerrain.MUD, HuntTerrain.GRASS, HuntTerrain.BUSH})
# Trees and the paddock wall fully block. Long grass is a counted veil (see hunt_fov).
HARD_OPAQUE = frozenset({HuntTerrain.WALL, HuntTerrain.TREE})
OPAQUE = HARD_OPAQUE
LONG_GRASS = frozenset({HuntTerrain.GRASS, HuntTerrain.BUSH})
MUD_TILES = frozenset({HuntTerrain.MUD})


def is_mud(terrain: HuntTerrain) -> bool:
    """Bare mud takes prints. Open grassland, long grass, and bush do not."""
    return terrain in MUD_TILES


def is_long_grass(terrain: HuntTerrain) -> bool:
    """`,` long grass. Legacy bush tiles count as the same veil."""
    return terrain in LONG_GRASS


@attrs.define(frozen=True)
class VisionProfile:
    cone_range: int
    cone_half_degrees: float
    close_blind: int = 0
    line: bool = False


@attrs.define(frozen=True)
class HuntPaddockConfig:
    map_width: int = 61
    map_height: int = 61
    tree_count: int = 64
    grass_blobs: int = 14
    bush_blobs: int = 9
    mud_blobs: int = 8
    open_clearings: int = 6
    blob_radius_min: int = 2
    blob_radius_max: int = 4
    cone_range: int = 12
    cone_half_degrees: float = 55.0
    vision: dict[str, VisionProfile] = attrs.field(factory=dict)
    raptor_cone_range: int = 14
    raptor_cone_half_degrees: float = 55.0
    bullseye_mud_radius: int = 1
    bullseye_ring_inner: int = 3
    bullseye_ring_outer: int = 8
    bullseye_grass_patches: int = 8
    bullseye_grass_radius: int = 3


@lru_cache(maxsize=1)
def load_paddock_config(path: Path | None = None) -> HuntPaddockConfig:
    p = path if path is not None else HUNT_PADDOCK_PATH
    if not p.is_file():
        return HuntPaddockConfig()
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return HuntPaddockConfig()
    walk_range = int(raw.get("cone_range", 12))
    walk_half = float(raw.get("cone_half_degrees", 55.0))
    vision_raw = raw.get("vision", {})
    vision: dict[str, VisionProfile] = {}
    if isinstance(vision_raw, dict):
        for key, profile in vision_raw.items():
            if not isinstance(profile, dict):
                continue
            vision[str(key)] = VisionProfile(
                cone_range=int(profile.get("cone_range", walk_range)),
                cone_half_degrees=float(profile.get("cone_half_degrees", walk_half)),
                close_blind=int(profile.get("close_blind", 0)),
                line=bool(profile.get("line", False)),
            )
    if "walk" not in vision:
        vision["walk"] = VisionProfile(cone_range=walk_range, cone_half_degrees=walk_half)
    return HuntPaddockConfig(
        map_width=int(raw.get("map_width", 61)),
        map_height=int(raw.get("map_height", 61)),
        tree_count=int(raw.get("tree_count", 64)),
        grass_blobs=int(raw.get("grass_blobs", 14)),
        bush_blobs=int(raw.get("bush_blobs", 9)),
        mud_blobs=int(raw.get("mud_blobs", 8)),
        open_clearings=int(raw.get("open_clearings", 6)),
        blob_radius_min=int(raw.get("blob_radius_min", 2)),
        blob_radius_max=int(raw.get("blob_radius_max", 4)),
        cone_range=walk_range,
        cone_half_degrees=walk_half,
        vision=vision,
        raptor_cone_range=int(raw.get("raptor_cone_range", 14)),
        raptor_cone_half_degrees=float(raw.get("raptor_cone_half_degrees", 55.0)),
        bullseye_mud_radius=int(raw.get("bullseye_mud_radius", 1)),
        bullseye_ring_inner=int(raw.get("bullseye_ring_inner", 3)),
        bullseye_ring_outer=int(raw.get("bullseye_ring_outer", 8)),
        bullseye_grass_patches=int(raw.get("bullseye_grass_patches", 8)),
        bullseye_grass_radius=int(raw.get("bullseye_grass_radius", 3)),
    )


def reset_paddock_config_cache() -> None:
    load_paddock_config.cache_clear()


def vision_profile_for(
    *,
    gait: str,
    aim_depth: int,
    cfg: HuntPaddockConfig,
    weapon_id: str = "",
) -> VisionProfile:
    """Aim depth overrides gait. Rifle aim is a scoped line. Run mode uses the walk cone."""
    if aim_depth >= 2:
        if weapon_id == "rifle" and "rifle_deep_aim" in cfg.vision:
            return cfg.vision["rifle_deep_aim"]
        if "deep_aim" in cfg.vision:
            return cfg.vision["deep_aim"]
    if aim_depth >= 1:
        if weapon_id == "rifle" and "rifle_aim" in cfg.vision:
            return cfg.vision["rifle_aim"]
        if "aim" in cfg.vision:
            return cfg.vision["aim"]
    key = "walk" if gait in ("run", "quick") else gait
    if key in cfg.vision:
        return cfg.vision[key]
    if gait in cfg.vision:
        return cfg.vision[gait]
    return VisionProfile(cone_range=cfg.cone_range, cone_half_degrees=cfg.cone_half_degrees)


@attrs.define
class HuntMap:
    width: int
    height: int
    tiles: list[list[HuntTerrain]]
    radius: float
    center_x: int
    center_y: int
    hide_spots: tuple[tuple[int, int, int], ...] = ()

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def terrain_at(self, x: int, y: int) -> HuntTerrain:
        if not self.in_bounds(x, y):
            return HuntTerrain.WALL
        return self.tiles[y][x]

    def walkable(self, x: int, y: int) -> bool:
        return self.terrain_at(x, y) in WALKABLE

    def opaque(self, x: int, y: int) -> bool:
        return self.terrain_at(x, y) in HARD_OPAQUE

    def hard_opaque(self, x: int, y: int) -> bool:
        return self.terrain_at(x, y) in HARD_OPAQUE

    def inside_circle(self, x: int, y: int) -> bool:
        dx = x - self.center_x
        dy = y - self.center_y
        return dx * dx + dy * dy <= self.radius * self.radius


def _stamp_disk(
    tiles: list[list[HuntTerrain]],
    cx: int,
    cy: int,
    radius: int,
    terrain: HuntTerrain,
    *,
    width: int,
    height: int,
    circle: HuntMap,
    only_interior: bool = True,
    overwrite_trees: bool = False,
) -> None:
    r2 = radius * radius
    for y in range(max(0, cy - radius), min(height, cy + radius + 1)):
        for x in range(max(0, cx - radius), min(width, cx + radius + 1)):
            if (x - cx) * (x - cx) + (y - cy) * (y - cy) > r2:
                continue
            if only_interior and not circle.inside_circle(x, y):
                continue
            if tiles[y][x] is HuntTerrain.WALL:
                continue
            if tiles[y][x] is HuntTerrain.TREE and not overwrite_trees:
                continue
            tiles[y][x] = terrain


def _interior_open(tiles: list[list[HuntTerrain]], mmap: HuntMap) -> list[tuple[int, int]]:
    return [
        (x, y)
        for y in range(mmap.height)
        for x in range(mmap.width)
        if mmap.inside_circle(x, y) and tiles[y][x] is HuntTerrain.OPEN
    ]


def generate_paddock(seed: int, config: HuntPaddockConfig | None = None) -> HuntMap:
    cfg = config if config is not None else load_paddock_config()
    rng = random.Random(seed)
    w, h = cfg.map_width, cfg.map_height
    cx, cy = w // 2, h // 2
    radius = float(min(cx, cy) - 1)
    tiles = [[HuntTerrain.WALL for _ in range(w)] for _ in range(h)]
    mmap = HuntMap(width=w, height=h, tiles=tiles, radius=radius, center_x=cx, center_y=cy)
    for y in range(h):
        for x in range(w):
            if mmap.inside_circle(x, y):
                tiles[y][x] = HuntTerrain.OPEN

    _stamp_bullseye(tiles, mmap, cfg, rng)

    def outside_bullseye(x: int, y: int) -> bool:
        d = max(abs(x - cx), abs(y - cy))
        return d > cfg.bullseye_ring_outer

    def blob(kind: HuntTerrain, count: int) -> None:
        for _ in range(count):
            spots = [
                (x, y)
                for (x, y) in _interior_open(tiles, mmap)
                if outside_bullseye(x, y)
            ]
            if not spots:
                return
            bx, by = rng.choice(spots)
            rad = rng.randint(cfg.blob_radius_min, cfg.blob_radius_max)
            _stamp_disk(tiles, bx, by, rad, kind, width=w, height=h, circle=mmap)

    open_spots = [
        (x, y) for (x, y) in _interior_open(tiles, mmap) if outside_bullseye(x, y)
    ]
    rng.shuffle(open_spots)
    planted = 0
    for x, y in open_spots:
        if planted >= cfg.tree_count:
            break
        tiles[y][x] = HuntTerrain.TREE
        planted += 1

    blob(HuntTerrain.GRASS, cfg.grass_blobs + cfg.bush_blobs)

    for _ in range(cfg.open_clearings):
        spots = [
            (x, y)
            for y in range(h)
            for x in range(w)
            if mmap.inside_circle(x, y) and outside_bullseye(x, y)
        ]
        if not spots:
            break
        ox, oy = rng.choice(spots)
        rad = rng.randint(cfg.blob_radius_min, cfg.blob_radius_max + 1)
        _stamp_disk(
            tiles,
            ox,
            oy,
            rad,
            HuntTerrain.OPEN,
            width=w,
            height=h,
            circle=mmap,
            overwrite_trees=True,
        )

    blob(HuntTerrain.MUD, cfg.mud_blobs)

    mmap.tiles = tiles
    mmap.hide_spots = collect_hide_spots(mmap)
    return mmap


def _stamp_bullseye(
    tiles: list[list[HuntTerrain]],
    mmap: HuntMap,
    cfg: HuntPaddockConfig,
    rng: random.Random,
) -> None:
    """Mud disk plus a ring of long-grass patches with open ground between."""
    _stamp_disk(
        tiles,
        mmap.center_x,
        mmap.center_y,
        cfg.bullseye_mud_radius,
        HuntTerrain.MUD,
        width=mmap.width,
        height=mmap.height,
        circle=mmap,
    )
    patches = max(0, cfg.bullseye_grass_patches)
    if patches <= 0:
        return
    mid = (cfg.bullseye_ring_inner + cfg.bullseye_ring_outer) / 2.0
    for i in range(patches):
        angle = (2.0 * math.pi * i) / patches + rng.uniform(-0.12, 0.12)
        dist = mid + rng.uniform(-0.6, 0.6)
        gx = int(round(mmap.center_x + math.cos(angle) * dist))
        gy = int(round(mmap.center_y + math.sin(angle) * dist))
        _stamp_disk(
            tiles,
            gx,
            gy,
            cfg.bullseye_grass_radius,
            HuntTerrain.GRASS,
            width=mmap.width,
            height=mmap.height,
            circle=mmap,
            overwrite_trees=True,
        )


def collect_hide_spots(mmap: HuntMap) -> tuple[tuple[int, int, int], ...]:
    """Grass tiles 3 deep that look out through two grass tiles into the open.

    Layout along facing: hide, grass, grass, open/mud. Hunter looking in sees
    two veils and not the raptor; the raptor looking out sees the field.
    """
    from src.hunt_facing import FACING_DELTAS

    spots: list[tuple[int, int, int]] = []
    for y in range(mmap.height):
        for x in range(mmap.width):
            if not is_long_grass(mmap.terrain_at(x, y)):
                continue
            for facing, (dx, dy) in enumerate(FACING_DELTAS):
                x1, y1 = x + dx, y + dy
                x2, y2 = x + 2 * dx, y + 2 * dy
                x3, y3 = x + 3 * dx, y + 3 * dy
                if not is_long_grass(mmap.terrain_at(x1, y1)):
                    continue
                if not is_long_grass(mmap.terrain_at(x2, y2)):
                    continue
                edge = mmap.terrain_at(x3, y3)
                if edge not in (HuntTerrain.OPEN, HuntTerrain.MUD):
                    continue
                spots.append((x, y, facing))
    return tuple(spots)


def nearest_walkable(mmap: HuntMap, x: int, y: int) -> tuple[int, int]:
    if mmap.walkable(x, y):
        return x, y
    best: tuple[int, int] | None = None
    best_d = 10**9
    for ty in range(mmap.height):
        for tx in range(mmap.width):
            if not mmap.walkable(tx, ty):
                continue
            d = max(abs(tx - x), abs(ty - y))
            if d < best_d:
                best_d = d
                best = (tx, ty)
    if best is None:
        return mmap.center_x, mmap.center_y
    return best
