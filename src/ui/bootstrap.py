from __future__ import annotations

from src.settings_store import SettingsStore
from src.ui.layout import UILayout, load_ui_layout

def load_active_layout(settings: SettingsStore | None = None) -> UILayout:
    """Load the UI layout preset from settings (or defaults)."""
    store = settings or SettingsStore.load()
    return load_ui_layout(store.ui_preset)


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