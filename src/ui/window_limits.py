from __future__ import annotations

import tcod.context

from src.ui.dynamic_layout import clamp_window_pixels, minimum_window_pixels
from src.ui.layout import UILayout


def client_pixels_from_context(
    context: tcod.context.Context,
    layout: UILayout,
) -> tuple[int, int]:
    """Return the live SDL client size (clamped), without resizing the window."""
    min_w, min_h = minimum_window_pixels(layout)
    window = getattr(context, "sdl_window", None)
    if window is None:
        return min_w, min_h
    return clamp_window_pixels(layout, *window.size)


def enforce_minimum_window_size(
    context: tcod.context.Context,
    layout: UILayout,
    *,
    requested_w: int | None = None,
    requested_h: int | None = None,
) -> tuple[int, int]:
    """Set SDL min client size and clamp the window to the design floor.

    SDL minimum size applies to the client (drawable) area; OS title bar and
    borders sit outside that region.
    """
    min_w, min_h = minimum_window_pixels(layout)
    window = getattr(context, "sdl_window", None)
    if window is None:
        width = max(min_w, requested_w if requested_w is not None else min_w)
        height = max(min_h, requested_h if requested_h is not None else min_h)
        return width, height

    window.min_size = (min_w, min_h)

    if requested_w is not None and requested_h is not None:
        clamped_w, clamped_h = clamp_window_pixels(layout, requested_w, requested_h)
    else:
        current_w, current_h = window.size
        clamped_w, clamped_h = clamp_window_pixels(layout, current_w, current_h)

    if window.size != (clamped_w, clamped_h):
        window.size = (clamped_w, clamped_h)
    return clamped_w, clamped_h