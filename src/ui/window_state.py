"""Window geometry persistence, first-launch sizing, and fullscreen handling."""

from __future__ import annotations

from typing import TYPE_CHECKING

import attrs
import tcod.console
import tcod.context
from tcod.cffi import lib
from tcod.sdl.video import Window, WindowFlags

from src.ui.dynamic_layout import DESIGN_PIXEL_HEIGHT, DESIGN_PIXEL_WIDTH, clamp_window_pixels
from src.ui.layout import UILayout
from src.ui.window_limits import enforce_minimum_window_size

if TYPE_CHECKING:
    from src.app import App

DISPLAY_INSET_PX = 48
_VIDEO_INITIALIZED = False


@attrs.define
class WindowPreferences:
    """Persisted window client geometry and mode flags."""

    client_width: int = DESIGN_PIXEL_WIDTH
    client_height: int = DESIGN_PIXEL_HEIGHT
    x: int = 0
    y: int = 0
    maximized: bool = False
    fullscreen: bool = False


@attrs.define
class WindowSessionState:
    """Snapshot taken when entering fullscreen (not persisted separately)."""

    client_width: int
    client_height: int
    x: int
    y: int
    maximized: bool


def ensure_video_initialized() -> None:
    """Initialize SDL video once before querying display metrics."""
    global _VIDEO_INITIALIZED
    if _VIDEO_INITIALIZED:
        return
    lib.SDL_Init(lib.SDL_INIT_VIDEO)
    _VIDEO_INITIALIZED = True


def primary_desktop_pixel_size() -> tuple[int, int]:
    """Primary display desktop resolution, or design minimum on failure."""
    ensure_video_initialized()
    try:
        display_id = lib.SDL_GetPrimaryDisplay()
        mode = lib.SDL_GetDesktopDisplayMode(display_id)
        if mode is None:
            raise OSError("SDL_GetDesktopDisplayMode returned null")
        width = int(mode.w)
        height = int(mode.h)
        if width <= 0 or height <= 0:
            raise OSError("invalid desktop display mode")
        return width, height
    except (AttributeError, OSError, TypeError, ValueError):
        return DESIGN_PIXEL_WIDTH, DESIGN_PIXEL_HEIGHT


def default_first_launch_client_size(layout: UILayout) -> tuple[int, int]:
    """Full desktop minus fixed inset per edge, clamped to the design minimum."""
    display_w, display_h = primary_desktop_pixel_size()
    min_w, min_h = clamp_window_pixels(layout, DESIGN_PIXEL_WIDTH, DESIGN_PIXEL_HEIGHT)
    inset = DISPLAY_INSET_PX * 2
    return (
        max(min_w, display_w - inset),
        max(min_h, display_h - inset),
    )


def centered_position(client_w: int, client_h: int) -> tuple[int, int]:
    """Center a client area on the primary desktop."""
    display_w, display_h = primary_desktop_pixel_size()
    return (
        max(0, (display_w - client_w) // 2),
        max(0, (display_h - client_h) // 2),
    )


def clamp_window_preferences(layout: UILayout, prefs: WindowPreferences) -> WindowPreferences:
    """Clamp stored client size to the supported minimum."""
    w, h = clamp_window_pixels(layout, prefs.client_width, prefs.client_height)
    if w == prefs.client_width and h == prefs.client_height:
        return prefs
    return attrs.evolve(prefs, client_width=w, client_height=h)


def window_from_dict(raw: dict[str, object], layout: UILayout) -> WindowPreferences:
    """Parse the settings ``window`` block with validation and clamping."""
    prefs = WindowPreferences(
        client_width=_as_int(raw.get("client_width"), DESIGN_PIXEL_WIDTH),
        client_height=_as_int(raw.get("client_height"), DESIGN_PIXEL_HEIGHT),
        x=_as_int(raw.get("x"), 0),
        y=_as_int(raw.get("y"), 0),
        maximized=_as_bool(raw.get("maximized"), False),
        fullscreen=_as_bool(raw.get("fullscreen"), False),
    )
    return clamp_window_preferences(layout, prefs)


def window_to_dict(prefs: WindowPreferences) -> dict[str, int | bool]:
    return {
        "client_width": prefs.client_width,
        "client_height": prefs.client_height,
        "x": prefs.x,
        "y": prefs.y,
        "maximized": prefs.maximized,
        "fullscreen": prefs.fullscreen,
    }


def get_sdl_window(context: tcod.context.Context) -> Window | None:
    return getattr(context, "sdl_window", None)


def capture_session_state(window: Window) -> WindowSessionState:
    width, height = window.size
    x, y = window.position
    maximized = bool(window.flags & WindowFlags.MAXIMIZED)
    return WindowSessionState(
        client_width=width,
        client_height=height,
        x=x,
        y=y,
        maximized=maximized,
    )


def sync_window_from_sdl(prefs: WindowPreferences, window: Window) -> WindowPreferences:
    """Update preferences from SDL when not fullscreen."""
    if window.fullscreen:
        return prefs
    maximized = bool(window.flags & WindowFlags.MAXIMIZED)
    updated = attrs.evolve(prefs, maximized=maximized)
    if maximized:
        return updated
    width, height = window.size
    x, y = window.position
    return attrs.evolve(
        updated,
        client_width=width,
        client_height=height,
        x=x,
        y=y,
    )


def apply_startup_window(
    context: tcod.context.Context,
    prefs: WindowPreferences,
    layout: UILayout,
) -> tuple[int, int]:
    """Restore position and mode after ``context.new``; return actual client size."""
    window = get_sdl_window(context)
    if window is None:
        return prefs.client_width, prefs.client_height

    pixel_w, pixel_h = enforce_minimum_window_size(
        context,
        layout,
        requested_w=prefs.client_width,
        requested_h=prefs.client_height,
    )

    if prefs.fullscreen:
        window.fullscreen = True
    else:
        window.position = (prefs.x, prefs.y)
        if prefs.maximized:
            window.maximize()
        else:
            window.size = (pixel_w, pixel_h)

    pixel_w, pixel_h = enforce_minimum_window_size(context, layout)
    return pixel_w, pixel_h


def restore_after_fullscreen(
    context: tcod.context.Context,
    layout: UILayout,
    prefs: WindowPreferences,
    snapshot: WindowSessionState | None,
) -> tuple[WindowPreferences, tuple[int, int]]:
    """Leave fullscreen and restore the last non-fullscreen session state."""
    window = get_sdl_window(context)
    if window is None:
        updated = attrs.evolve(prefs, fullscreen=False)
        return updated, (updated.client_width, updated.client_height)

    window.fullscreen = False
    source = snapshot if snapshot is not None else _preferences_as_session(prefs)
    updated = attrs.evolve(
        prefs,
        fullscreen=False,
        maximized=source.maximized,
        client_width=source.client_width,
        client_height=source.client_height,
        x=source.x,
        y=source.y,
    )
    if source.maximized:
        window.maximize()
    else:
        clamped_w, clamped_h = clamp_window_pixels(
            layout,
            source.client_width,
            source.client_height,
        )
        window.size = (clamped_w, clamped_h)
        window.position = (source.x, source.y)
        updated = attrs.evolve(updated, client_width=clamped_w, client_height=clamped_h)

    pixel_w, pixel_h = enforce_minimum_window_size(context, layout)
    return updated, (pixel_w, pixel_h)


def enter_fullscreen(
    window: Window,
    prefs: WindowPreferences,
    snapshot: WindowSessionState | None,
) -> tuple[WindowSessionState, WindowPreferences]:
    """Enter fullscreen, capturing a session snapshot when starting from windowed/maximized."""
    if snapshot is None:
        snapshot = capture_session_state(window)
    window.fullscreen = True
    updated = attrs.evolve(prefs, fullscreen=True)
    return snapshot, updated


def resize_app_console(
    app: App,
    pixel_w: int,
    pixel_h: int,
) -> tcod.console.Console:
    """Re-resolve layout and return a new root console for the given client pixels."""
    from src.ui.bootstrap import load_active_layout
    from src.ui.dynamic_layout import cells_from_pixels, resolve_dynamic_layout

    baseline = load_active_layout(app.settings)
    app.baseline_layout = baseline
    clamped_w, clamped_h = clamp_window_pixels(baseline, pixel_w, pixel_h)
    cols, rows = cells_from_pixels(baseline, clamped_w, clamped_h)
    layout = resolve_dynamic_layout(baseline, cols, rows)
    app.apply_ui_layout(layout)
    return tcod.console.Console(layout.root_cols, layout.root_rows, order="F")


def _preferences_as_session(prefs: WindowPreferences) -> WindowSessionState:
    return WindowSessionState(
        client_width=prefs.client_width,
        client_height=prefs.client_height,
        x=prefs.x,
        y=prefs.y,
        maximized=prefs.maximized,
    )


def _as_int(value: object, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return default


def _as_bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    return default