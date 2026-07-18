from __future__ import annotations

import attrs

from src.ui.layout import MapViewportTiles, RegionRect, UILayout

# Minimum supported gameplay resolution (design target).
DESIGN_PIXEL_WIDTH = 1360
DESIGN_PIXEL_HEIGHT = 768

MIN_MAP_VIEWPORT_W = 20
MIN_MAP_VIEWPORT_H = 16


def cell_pixel_size(layout: UILayout) -> int:
    return layout.tile_px * layout.tile_scale


def minimum_window_pixels(layout: UILayout) -> tuple[int, int]:
    """Hard floor for the window client area at the minimum supported resolution."""
    return (DESIGN_PIXEL_WIDTH, DESIGN_PIXEL_HEIGHT)


def clamp_window_pixels(
    layout: UILayout,
    pixel_w: int,
    pixel_h: int,
) -> tuple[int, int]:
    """Clamp resize events so the window cannot shrink below the design floor."""
    min_w, min_h = minimum_window_pixels(layout)
    return max(min_w, pixel_w), max(min_h, pixel_h)


def cells_from_pixels(layout: UILayout, pixel_w: int, pixel_h: int) -> tuple[int, int]:
    """Convert clamped window pixels to root console cell counts."""
    pixel_w, pixel_h = clamp_window_pixels(layout, pixel_w, pixel_h)
    cell_px = cell_pixel_size(layout)
    cols = max(1, pixel_w // cell_px)
    rows = max(1, pixel_h // cell_px)
    return cols, rows


def minimum_root_dimensions(baseline: UILayout) -> tuple[int, int]:
    """Smallest root console that preserves chrome floors and minimum map size."""
    side_w = baseline.region("sidebar").w
    log_h = baseline.region("message_log").h
    min_cols = MIN_MAP_VIEWPORT_W + side_w
    min_rows = MIN_MAP_VIEWPORT_H + log_h

    floor_w, floor_h = minimum_window_pixels(baseline)
    floor_cols, floor_rows = (
        floor_w // cell_pixel_size(baseline),
        floor_h // cell_pixel_size(baseline),
    )
    return max(min_cols, floor_cols), max(min_rows, floor_rows)


def resolve_dynamic_layout(
    baseline: UILayout,
    root_cols: int,
    root_rows: int,
) -> UILayout:
    """Recompute regions for a root console size; map viewport flexes first."""
    side_w = baseline.region("sidebar").w
    log_h = baseline.region("message_log").h
    corner_w = baseline.region("status_corner").w

    min_cols, min_rows = minimum_root_dimensions(baseline)
    root_cols = max(min_cols, root_cols)
    root_rows = max(min_rows, root_rows)

    map_w = root_cols - side_w
    map_h = root_rows - log_h
    log_w = root_cols - corner_w

    regions = {
        "map_viewport": RegionRect(0, 0, map_w, map_h),
        "sidebar": RegionRect(map_w, 0, side_w, map_h),
        "message_log": RegionRect(0, map_h, log_w, log_h),
        "status_corner": RegionRect(log_w, map_h, corner_w, log_h),
    }

    layout = attrs.evolve(
        baseline,
        root_cols=root_cols,
        root_rows=root_rows,
        regions=regions,
        map_viewport_tiles=MapViewportTiles(map_w, map_h),
    )
    from src.ui.layout import _validate_region_tiling

    _validate_region_tiling(layout)
    return layout