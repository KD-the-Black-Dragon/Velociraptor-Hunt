"""Cell and pixel geometry for Gladiavore match HUD (status / log / reaction)."""

from __future__ import annotations

import attrs

from src.ui.layout import RegionRect, UILayout

# Reaction panel defaults (cells). Tunable after playtest without JSON churn.
REACTION_PANEL_MIN_W = 22
REACTION_PANEL_H = 10
MATCH_LOG_MAX_LINES = 10


@attrs.define(frozen=True)
class MatchHudBands:
    """Cell-space bands for fight-phase match chrome (origin = console top-left)."""

    map_w: int
    map_h: int
    root_w: int
    root_h: int
    status: RegionRect
    log: RegionRect
    reaction: RegionRect | None


def match_hud_bands(
    *,
    map_w: int,
    map_h: int,
    root_w: int,
    root_h: int,
    reaction_active: bool,
) -> MatchHudBands:
    """Compute status (right of map), log (bottom), optional reaction (low-right).

    Map is drawn at (0, 0). Status fills the gutter to the right of the map
    down to the log band. Log uses the bottom rows; when a reaction modal is
    active it leaves a low-right strip for the reaction panel.
    """
    map_w = max(1, map_w)
    map_h = max(1, map_h)
    root_w = max(map_w + 1, root_w)
    root_h = max(map_h + 2, root_h)

    log_top = min(map_h, root_h - 2)
    log_h = max(1, root_h - log_top - 1)  # reserve 1 row for footer keys
    status_w = max(1, root_w - map_w)
    status = RegionRect(x=map_w, y=0, w=status_w, h=log_top)

    reaction: RegionRect | None = None
    if reaction_active:
        rw = min(max(REACTION_PANEL_MIN_W, status_w), root_w)
        # Prefer at least status width; cap so log still has room
        rw = min(rw, max(12, root_w // 3 + 4))
        if rw >= root_w - 8:
            rw = max(12, root_w // 3)
        rh = min(REACTION_PANEL_H, log_h)
        reaction = RegionRect(x=root_w - rw, y=log_top, w=rw, h=rh)
        log = RegionRect(x=0, y=log_top, w=max(1, root_w - rw), h=log_h)
    else:
        log = RegionRect(x=0, y=log_top, w=root_w, h=log_h)

    return MatchHudBands(
        map_w=map_w,
        map_h=map_h,
        root_w=root_w,
        root_h=root_h,
        status=status,
        log=log,
        reaction=reaction,
    )


def region_to_pixel_rect(
    region: RegionRect,
    *,
    layout: UILayout,
    scale: int,
    dest_x: int,
    dest_y: int,
) -> tuple[float, float, float, float]:
    """Map a cell region to the integer-scaled present destination rect."""
    cell = layout.tile_px * layout.tile_scale
    return (
        float(dest_x + region.x * cell * scale),
        float(dest_y + region.y * cell * scale),
        float(region.w * cell * scale),
        float(region.h * cell * scale),
    )


def region_pixel_size(region: RegionRect, *, layout: UILayout) -> tuple[int, int]:
    """Unscaled pixel size of a cell region (before window integer scale)."""
    cell = layout.tile_px * layout.tile_scale
    return region.w * cell, region.h * cell
