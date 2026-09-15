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
# Keep the title bar reachable after 4K toggles that leave the window off-screen.
FOUR_K_TOGGLE_MIN_X = 0
FOUR_K_TOGGLE_MIN_Y = 30
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
    # Preferred client size while 4K UI scaling is On (None until first enable).
    four_k_client_width: int | None = None
    four_k_client_height: int | None = None


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
    """Clamp stored normal client size to the supported minimum."""
    w, h = clamp_window_pixels(layout, prefs.client_width, prefs.client_height)
    if w == prefs.client_width and h == prefs.client_height:
        return prefs
    return attrs.evolve(prefs, client_width=w, client_height=h)


def has_four_k_client_size(prefs: WindowPreferences) -> bool:
    """True when a preferred 4K window size has been recorded."""
    return prefs.four_k_client_width is not None and prefs.four_k_client_height is not None


def clamp_four_k_toggle_position(x: int, y: int) -> tuple[int, int]:
    """Floor window position so the title bar stays reachable after a 4K toggle."""
    return max(FOUR_K_TOGGLE_MIN_X, x), max(FOUR_K_TOGGLE_MIN_Y, y)


def seed_four_k_client_size(
    prefs: WindowPreferences,
    width: int,
    height: int,
) -> WindowPreferences:
    """Record the preferred 4K client size (first enable or startup seed)."""
    return attrs.evolve(
        prefs,
        four_k_client_width=max(1, int(width)),
        four_k_client_height=max(1, int(height)),
    )


def ensure_four_k_size_seeded(prefs: WindowPreferences) -> WindowPreferences:
    """If 4K size is unset, seed it as 2× the normal client size."""
    if has_four_k_client_size(prefs):
        return prefs
    return seed_four_k_client_size(
        prefs,
        prefs.client_width * 2,
        prefs.client_height * 2,
    )


def resolve_active_client_size(
    prefs: WindowPreferences,
    *,
    four_k_scaling: bool,
) -> tuple[int, int]:
    """Client size for the active scaling mode (seeds 2× normal when 4K unset)."""
    if not four_k_scaling:
        return prefs.client_width, prefs.client_height
    if has_four_k_client_size(prefs):
        assert prefs.four_k_client_width is not None
        assert prefs.four_k_client_height is not None
        return prefs.four_k_client_width, prefs.four_k_client_height
    return prefs.client_width * 2, prefs.client_height * 2


def write_client_size(
    prefs: WindowPreferences,
    width: int,
    height: int,
    *,
    four_k_scaling: bool,
) -> WindowPreferences:
    """Write width/height into the size set for the given scaling mode."""
    if four_k_scaling:
        return seed_four_k_client_size(prefs, width, height)
    return attrs.evolve(prefs, client_width=width, client_height=height)


def window_from_dict(raw: dict[str, object], layout: UILayout) -> WindowPreferences:
    """Parse the settings ``window`` block with validation and clamping."""
    four_k_w = _optional_positive_int(raw.get("four_k_client_width"))
    four_k_h = _optional_positive_int(raw.get("four_k_client_height"))
    # Require both keys; a single missing/invalid value leaves 4K size unset.
    if four_k_w is None or four_k_h is None:
        four_k_w, four_k_h = None, None
    prefs = WindowPreferences(
        client_width=_as_int(raw.get("client_width"), DESIGN_PIXEL_WIDTH),
        client_height=_as_int(raw.get("client_height"), DESIGN_PIXEL_HEIGHT),
        x=_as_int(raw.get("x"), 0),
        y=_as_int(raw.get("y"), 0),
        maximized=_as_bool(raw.get("maximized"), False),
        fullscreen=_as_bool(raw.get("fullscreen"), False),
        four_k_client_width=four_k_w,
        four_k_client_height=four_k_h,
    )
    return clamp_window_preferences(layout, prefs)


def window_to_dict(prefs: WindowPreferences) -> dict[str, int | bool]:
    payload: dict[str, int | bool] = {
        "client_width": prefs.client_width,
        "client_height": prefs.client_height,
        "x": prefs.x,
        "y": prefs.y,
        "maximized": prefs.maximized,
        "fullscreen": prefs.fullscreen,
    }
    if has_four_k_client_size(prefs):
        assert prefs.four_k_client_width is not None
        assert prefs.four_k_client_height is not None
        payload["four_k_client_width"] = prefs.four_k_client_width
        payload["four_k_client_height"] = prefs.four_k_client_height
    return payload


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


def sync_window_from_sdl(
    prefs: WindowPreferences,
    window: Window,
    *,
    four_k_scaling: bool = False,
) -> WindowPreferences:
    """Update preferences from SDL when not fullscreen.

    Live client size writes into the active scaling set only: 4K On →
    ``four_k_client_*``; Off → ``client_*``. Position ``x``/``y`` are shared.
    """
    if window.fullscreen:
        return prefs
    maximized = bool(window.flags & WindowFlags.MAXIMIZED)
    updated = attrs.evolve(prefs, maximized=maximized)
    if maximized:
        return updated
    width, height = window.size
    x, y = window.position
    updated = write_client_size(
        updated,
        width,
        height,
        four_k_scaling=four_k_scaling,
    )
    return attrs.evolve(updated, x=x, y=y)


def apply_startup_window(
    context: tcod.context.Context,
    prefs: WindowPreferences,
    layout: UILayout,
    *,
    four_k_scaling: bool = False,
) -> tuple[int, int]:
    """Restore position and mode after ``context.new``; return actual client size."""
    window = get_sdl_window(context)
    active_w, active_h = resolve_active_client_size(prefs, four_k_scaling=four_k_scaling)
    if window is None:
        return active_w, active_h

    pixel_w, pixel_h = enforce_minimum_window_size(
        context,
        layout,
        requested_w=active_w,
        requested_h=active_h,
    )

    if prefs.fullscreen:
        window.fullscreen = True
    else:
        window.position = (prefs.x, prefs.y)
        if prefs.maximized:
            window.maximize()
        else:
            window.size = (pixel_w, pixel_h)

    pixel_w, pixel_h = enforce_minimum_window_size(
        context,
        layout,
        requested_w=pixel_w,
        requested_h=pixel_h,
    )
    return pixel_w, pixel_h


def apply_four_k_toggle_geometry(
    context: tcod.context.Context,
    prefs: WindowPreferences,
    layout: UILayout,
    *,
    outgoing_four_k: bool,
    incoming_four_k: bool,
) -> tuple[WindowPreferences, tuple[int, int]]:
    """Remember the outgoing size set, then apply the incoming set + position clamp.

    Fullscreen and maximized skip size swap and position apply (layout reload
    still happens in the caller). Enabling 4K never mutates normal ``client_*``
    except via the outgoing sync when leaving Off (refreshing the normal set).
    """
    window = get_sdl_window(context)
    if window is None:
        target_w, target_h = resolve_active_client_size(
            prefs,
            four_k_scaling=incoming_four_k,
        )
        if incoming_four_k and not has_four_k_client_size(prefs):
            prefs = ensure_four_k_size_seeded(prefs)
            target_w, target_h = resolve_active_client_size(
                prefs,
                four_k_scaling=True,
            )
        return prefs, (target_w, target_h)

    if window.fullscreen:
        return prefs, (int(window.size[0]), int(window.size[1]))

    # Capture the size the user had under the outgoing mode.
    prefs = sync_window_from_sdl(
        prefs,
        window,
        four_k_scaling=outgoing_four_k,
    )

    if bool(window.flags & WindowFlags.MAXIMIZED):
        return prefs, (int(window.size[0]), int(window.size[1]))

    if incoming_four_k and not has_four_k_client_size(prefs):
        live_w, live_h = window.size
        prefs = seed_four_k_client_size(prefs, int(live_w) * 2, int(live_h) * 2)

    target_w, target_h = resolve_active_client_size(
        prefs,
        four_k_scaling=incoming_four_k,
    )
    clamped_w, clamped_h = clamp_window_pixels(layout, target_w, target_h)
    prefs = write_client_size(
        prefs,
        clamped_w,
        clamped_h,
        four_k_scaling=incoming_four_k,
    )
    window.size = (clamped_w, clamped_h)

    x, y = clamp_four_k_toggle_position(prefs.x, prefs.y)
    window.position = (x, y)
    prefs = attrs.evolve(prefs, x=x, y=y)
    return prefs, (clamped_w, clamped_h)


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
        # Same title-bar recovery floors as the 4K UI scaling toggle.
        x, y = clamp_four_k_toggle_position(source.x, source.y)
        window.size = (clamped_w, clamped_h)
        window.position = (x, y)
        updated = attrs.evolve(
            updated,
            client_width=clamped_w,
            client_height=clamped_h,
            x=x,
            y=y,
        )

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
    from src.ui.dynamic_layout import cell_pixel_size, resolve_dynamic_layout

    baseline = load_active_layout(app.settings)
    app.baseline_layout = baseline
    # Use the actual client pixels (do not inflate to the design floor). Inflating
    # builds a console larger than the window and present clips to the top-left.
    cell_px = cell_pixel_size(baseline)
    cols = max(1, int(pixel_w) // cell_px)
    rows = max(1, int(pixel_h) // cell_px)
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


def _optional_positive_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, float):
        as_int = int(value)
        return as_int if as_int > 0 else None
    return None


def _as_bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    return default