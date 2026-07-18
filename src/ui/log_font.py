"""Proportional TTF font for the message log region (PR4)."""

from __future__ import annotations

import warnings
from pathlib import Path

import attrs
from PIL import ImageFont

from src.constants import DATA_DIR
from src.ui.proportional_log import load_proportional_font, proportional_font_size_px

LOG_FONT_PATH = DATA_DIR / "fonts" / "SourceSans3-Regular.ttf"

_warned_fallback = False


def _warn_fallback_once(message: str) -> None:
    global _warned_fallback
    if _warned_fallback:
        return
    _warned_fallback = True
    warnings.warn(message, stacklevel=3)


@attrs.define
class LogFontState:
    """Resources for proportional message-log rendering."""

    enabled: bool = False
    tile_px: int = 12
    tile_scale: int = 2
    font_size_px: int = 16
    font_path: Path | None = None
    font: ImageFont.FreeTypeFont | None = None


def load_log_font_state(
    *,
    tile_px: int,
    tile_scale: int = 2,
    font_path: Path | str | None = None,
) -> LogFontState:
    """Load the proportional log font; fall back to CP437 when unavailable."""
    path = Path(font_path) if font_path is not None else LOG_FONT_PATH
    font_size_px = proportional_font_size_px(tile_px, tile_scale)
    if not path.is_file():
        _warn_fallback_once(
            f"message log TTF not found at {path}; using CP437 for the log panel",
        )
        return LogFontState(
            enabled=False,
            tile_px=tile_px,
            tile_scale=tile_scale,
            font_size_px=font_size_px,
        )

    try:
        font = load_proportional_font(path, size_px=font_size_px)
    except (OSError, ValueError) as exc:
        _warn_fallback_once(
            f"failed to load message log TTF ({path}): {exc}; using CP437",
        )
        return LogFontState(
            enabled=False,
            tile_px=tile_px,
            tile_scale=tile_scale,
            font_size_px=font_size_px,
        )

    return LogFontState(
        enabled=True,
        tile_px=tile_px,
        tile_scale=tile_scale,
        font_size_px=font_size_px,
        font_path=path,
        font=font,
    )


def reset_log_font_warnings() -> None:
    """Clear the one-shot fallback warning flag (for tests)."""
    global _warned_fallback
    _warned_fallback = False