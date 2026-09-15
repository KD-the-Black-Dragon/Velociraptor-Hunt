from __future__ import annotations

import tcod.console

from src.constants import SCREEN_WIDTH
from src.text import cp437_safe

# FIGlet-style "standard" block for VELOCIRAPTOR (HUNT is drawn under the banner).
TITLE_BANNER_LINES: tuple[str, ...] = (
    " __     _______ _     ___   ____ ___ ____      _    ____ _____ ___  ____  ",
    " \\ \\   / / ____| |   / _ \\ / ___|_ _|  _ \\    / \\  |  _ \\_   _/ _ \\|  _ \\ ",
    "  \\ \\ / /|  _| | |  | | | | |    | || |_) |  / _ \\ | |_) || || | | | |_) |",
    "   \\ V / | |___| |__| |_| | |___ | ||  _ <  / ___ \\|  __/ | || |_| |  _ < ",
    "    \\_/  |_____|_____\\___/ \\____|___|_| \\_\\/_/   \\_\\_|    |_| \\___/|_| \\_\\",
)

TITLE_BANNER_HEIGHT = len(TITLE_BANNER_LINES)
TITLE_BANNER_WIDTH = max(len(line) for line in TITLE_BANNER_LINES)

# Per-row horizontal nudge (negative = shift left). Mostly aligned; light tune for visual center.
TITLE_BANNER_X_OFFSETS: tuple[int, ...] = (
    0,
    0,
    0,
    0,
    0,
)

# Horizontal position of each row relative to the banner block left edge.
# Tuned at 80 columns; keeps FIGlet rows aligned when the window width changes.
_REFERENCE_CENTER_WIDTH = 80


def _banner_line_x_offsets() -> tuple[int, ...]:
    block_left = (_REFERENCE_CENTER_WIDTH - TITLE_BANNER_WIDTH) // 2
    offsets: list[int] = []
    for row_offset, line in enumerate(TITLE_BANNER_LINES):
        text = line.rstrip()
        if not text:
            offsets.append(0)
            continue
        line_x = (
            (_REFERENCE_CENTER_WIDTH - len(text)) // 2
            + TITLE_BANNER_X_OFFSETS[row_offset]
        )
        offsets.append(line_x - block_left)
    return tuple(offsets)


TITLE_BANNER_LINE_X = _banner_line_x_offsets()


def render_title_banner(
    console: tcod.console.Console,
    *,
    y: int,
    width: int | None = None,
    fg: tuple[int, int, int] = (255, 220, 120),
) -> None:
    """Draw the large ASCII title banner centered at the given top row."""
    center_width = width if width is not None else SCREEN_WIDTH
    anchor_x = max(0, (center_width - TITLE_BANNER_WIDTH) // 2)
    for row_offset, line in enumerate(TITLE_BANNER_LINES):
        text = cp437_safe(line.rstrip())
        if not text:
            continue
        x = max(0, anchor_x + TITLE_BANNER_LINE_X[row_offset])
        console.print(x, y + row_offset, text, fg=fg)
