from __future__ import annotations

import tcod.context

from src.ui.dynamic_layout import clamp_window_pixels, minimum_window_pixels
from src.ui.layout import UILayout


def client_pixels_from_context(
    context: tcod.context.Context,
    layout: UILayout,
) -> tuple[int, int]:
    """Return the live SDL client size (actual), without resizing the window.

    Does not inflate to the design floor — console sizing must match the real
    drawable area or present clips to the top-left under 4K UI scaling.
    """
    min_w, min_h = minimum_window_pixels(layout)
    window = getattr(context, "sdl_window", None)
    if window is None:
        return min_w, min_h
    return int(window.size[0]), int(window.size[1])


def enforce_minimum_window_size(
    context: tcod.context.Context,
    layout: UILayout,
    *,
    requested_w: int | None = None,
    requested_h: int | None = None,
) -> tuple[int, int]:
    """Set SDL min client size and try to grow the window to the design floor.

    Returns the **actual** client size after the attempt (maximized/fullscreen
    may refuse to grow). Callers must size the console from that actual size.

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
    # Prefer live size: OS may ignore resize while maximized/fullscreen.
    actual_w, actual_h = window.size
    return int(actual_w), int(actual_h)
