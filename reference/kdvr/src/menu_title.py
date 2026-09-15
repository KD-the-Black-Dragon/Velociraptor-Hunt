"""Title-screen logo (PNG) helpers for the main menu."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import Image

from src.constants import TITLE_LOGO_PATH

# Re-export for callers that import from menu_title.
__all__ = [
    "TITLE_LOGO_PATH",
    "TITLE_LOGO_WIDTH_FRAC",
    "TITLE_LOGO_MAX_HEIGHT_FRAC",
    "load_title_logo",
    "clear_title_logo_cache",
    "title_logo_dest_rect",
]

# Target logo width as a fraction of the console viewport width.
TITLE_LOGO_WIDTH_FRAC = 0.60
# Soft cap so the logo does not crowd the option list (fraction of viewport height).
TITLE_LOGO_MAX_HEIGHT_FRAC = 0.55
# Extra top/bottom padding inside the upper band above the menu options.
TITLE_LOGO_BAND_MARGIN_FRAC = 0.04


@lru_cache(maxsize=1)
def load_title_logo(*, path: Path | None = None) -> Image.Image:
    """Load and cache the title logo as RGBA (premultiplied-safe for SDL blit)."""
    logo_path = path if path is not None else TITLE_LOGO_PATH
    image = Image.open(logo_path)
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    return image


def clear_title_logo_cache() -> None:
    """Drop the cached logo image (tests / hot-reload)."""
    load_title_logo.cache_clear()


def title_logo_dest_rect(
    *,
    dest_x: int,
    dest_y: int,
    dest_w: int,
    dest_h: int,
    logo_w: int,
    logo_h: int,
    options_start_y: int,
    console_h: int,
    width_frac: float = TITLE_LOGO_WIDTH_FRAC,
    max_height_frac: float = TITLE_LOGO_MAX_HEIGHT_FRAC,
) -> tuple[int, int, int, int]:
    """Pixel dest rect for the logo in the upper band above menu options."""
    if logo_w <= 0 or logo_h <= 0 or dest_w <= 0 or dest_h <= 0 or console_h <= 0:
        return dest_x, dest_y, 0, 0

    options_frac = max(0.15, min(0.95, options_start_y / console_h))
    band_top = dest_y + int(dest_h * TITLE_LOGO_BAND_MARGIN_FRAC)
    band_bottom = dest_y + int(dest_h * options_frac) - int(
        dest_h * TITLE_LOGO_BAND_MARGIN_FRAC
    )
    band_h = max(1, band_bottom - band_top)

    max_w = max(1, int(dest_w * width_frac))
    max_h = max(1, min(band_h, int(dest_h * max_height_frac)))
    scale = min(max_w / logo_w, max_h / logo_h)
    out_w = max(1, int(logo_w * scale))
    out_h = max(1, int(logo_h * scale))

    x = dest_x + (dest_w - out_w) // 2
    y = band_top + max(0, (band_h - out_h) // 2)
    return x, y, out_w, out_h
