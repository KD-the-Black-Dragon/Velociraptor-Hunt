from __future__ import annotations

import random

import attrs


@attrs.define(frozen=True)
class DensityDefaults:
    density_pct: float
    density_variance: float
    min_npcs: int
    max_npcs: int | None


@attrs.define(frozen=True)
class DepthBand:
    min_depth: int
    max_depth: int
    density_pct: float
    density_variance: float
    min_npcs: int
    max_npcs: int | None


@attrs.define(frozen=True)
class DungeonSpawnConfig:
    schema_version: int
    defaults: DensityDefaults
    depth_bands: tuple[DepthBand, ...]

    def resolve_band(self, floor_depth: int) -> DepthBand:
        for band in self.depth_bands:
            if band.min_depth <= floor_depth <= band.max_depth:
                return band
        return DepthBand(
            min_depth=floor_depth,
            max_depth=floor_depth,
            density_pct=self.defaults.density_pct,
            density_variance=self.defaults.density_variance,
            min_npcs=self.defaults.min_npcs,
            max_npcs=self.defaults.max_npcs,
        )


def compute_target_npc_count(
    valid_tile_count: int,
    floor_depth: int,
    config: DungeonSpawnConfig,
    rng: random.Random,
    *,
    density_multiplier: float = 1.0,
) -> int:
    """Return how many NPCs to spawn for this floor given valid candidate tiles.

    ``density_multiplier`` scales the density-derived target (difficulty profile);
    min/max NPC clamps still apply, then valid tile cap.
    """
    if valid_tile_count <= 0:
        return 0

    band = config.resolve_band(floor_depth)
    multiplier = rng.uniform(1.0 - band.density_variance, 1.0 + band.density_variance)
    dens = max(0.0, float(density_multiplier))
    raw = valid_tile_count * band.density_pct * multiplier * dens
    target = max(band.min_npcs, round(raw))
    if band.max_npcs is not None:
        target = min(target, band.max_npcs)
    return min(target, valid_tile_count)