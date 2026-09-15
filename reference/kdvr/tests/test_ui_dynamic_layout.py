"""PR11: dynamic layout resize — map viewport flex."""

from __future__ import annotations

from src.ui.dynamic_layout import (
    DESIGN_PIXEL_HEIGHT,
    DESIGN_PIXEL_WIDTH,
    clamp_window_pixels,
    cells_from_pixels,
    minimum_root_dimensions,
    minimum_window_pixels,
    resolve_dynamic_layout,
)
from src.ui.layout import load_ui_layout


def test_resolve_dynamic_layout_grows_map_viewport() -> None:
    baseline = load_ui_layout()
    grown = resolve_dynamic_layout(baseline, 100, 50)
    assert grown.root_cols == 100
    assert grown.root_rows == 50
    assert grown.map_viewport_tiles.w == 100 - baseline.region("sidebar").w
    assert grown.map_viewport_tiles.h == 50 - baseline.region("message_log").h


def test_resolve_dynamic_layout_shrinks_map_viewport() -> None:
    baseline = load_ui_layout()
    min_cols, min_rows = minimum_root_dimensions(baseline)
    shrunk = resolve_dynamic_layout(baseline, min_cols, min_rows)
    assert shrunk.root_cols == min_cols
    assert shrunk.root_rows == min_rows
    assert shrunk.map_viewport_tiles.w == min_cols - baseline.region("sidebar").w
    assert shrunk.map_viewport_tiles.h == min_rows - baseline.region("message_log").h


def test_resolve_dynamic_layout_preserves_chrome_widths() -> None:
    baseline = load_ui_layout()
    layout = resolve_dynamic_layout(baseline, 90, 45)
    assert layout.region("sidebar").w == baseline.region("sidebar").w
    assert layout.region("status_corner").w == baseline.region("status_corner").w
    assert layout.region("message_log").h == baseline.region("message_log").h


def test_status_corner_is_ten_cells_wide_in_preset() -> None:
    layout = load_ui_layout()
    assert layout.region("status_corner").w == 10
    assert layout.region("message_log").w == 70


def test_minimum_window_pixels_match_design_resolution() -> None:
    layout = load_ui_layout()
    min_w, min_h = minimum_window_pixels(layout)
    assert min_w == DESIGN_PIXEL_WIDTH
    assert min_h == DESIGN_PIXEL_HEIGHT


def test_minimum_window_pixels_scales_with_tile_scale() -> None:
    import attrs

    layout = load_ui_layout()
    scaled = attrs.evolve(layout, tile_scale=layout.tile_scale * 2)
    min_w, min_h = minimum_window_pixels(scaled)
    assert min_w == DESIGN_PIXEL_WIDTH * 2
    assert min_h == DESIGN_PIXEL_HEIGHT * 2


def test_clamp_window_pixels_enforces_design_floor() -> None:
    layout = load_ui_layout()
    clamped_w, clamped_h = clamp_window_pixels(layout, 800, 600)
    min_w, min_h = minimum_window_pixels(layout)
    assert clamped_w == min_w
    assert clamped_h == min_h


def test_cells_from_pixels_at_1360x768() -> None:
    layout = load_ui_layout()
    cols, rows = cells_from_pixels(layout, DESIGN_PIXEL_WIDTH, DESIGN_PIXEL_HEIGHT)
    assert cols == 56
    assert rows == 32


def test_resolve_at_design_floor_uses_narrow_standard_sidebar() -> None:
    baseline = load_ui_layout()
    min_cols, min_rows = minimum_root_dimensions(baseline)
    layout = resolve_dynamic_layout(baseline, min_cols, min_rows)
    assert layout.map_viewport_tiles.w == min_cols - baseline.region("sidebar").w
    assert layout.region("sidebar").w == 23