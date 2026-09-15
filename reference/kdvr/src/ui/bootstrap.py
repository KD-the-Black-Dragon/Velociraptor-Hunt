from __future__ import annotations

import attrs

from src.settings_store import SettingsStore
from src.ui.layout import UILayout, load_ui_layout

# Options "4K UI scaling" multiplies stock tile_scale by this factor when enabled.
FOUR_K_TILE_SCALE_FACTOR = 2


def layout_for_preset(preset_id: str, *, four_k_scaling: bool = False) -> UILayout:
    """Load a named UI preset, optionally applying 4K (2×) effective tile_scale."""
    layout = load_ui_layout(preset_id)
    if four_k_scaling:
        layout = attrs.evolve(
            layout,
            tile_scale=layout.tile_scale * FOUR_K_TILE_SCALE_FACTOR,
        )
    return layout


def load_active_layout(settings: SettingsStore | None = None) -> UILayout:
    """Load the UI layout preset from settings (or defaults).

    When ``four_k_scaling`` is on, effective ``tile_scale`` is doubled (past-version
    safe: missing settings key stays off).
    """
    store = settings or SettingsStore.load()
    return layout_for_preset(store.ui_preset, four_k_scaling=store.four_k_scaling)


def runtime_console_dimensions(layout: UILayout) -> tuple[int, int]:
    """Root console size from the active layout preset."""
    return layout.root_cols, layout.root_rows


def window_pixel_size(
    layout: UILayout,
    console_w: int,
    console_h: int,
) -> tuple[int, int]:
    """Map layout tile_scale to tcod 21+ window pixels (tile_scale kwarg removed)."""
    return (
        console_w * layout.tile_px * layout.tile_scale,
        console_h * layout.tile_px * layout.tile_scale,
    )