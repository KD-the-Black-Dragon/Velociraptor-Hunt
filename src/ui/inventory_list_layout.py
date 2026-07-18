"""Multi-column inventory list layout (fill down, then next column)."""

from __future__ import annotations

import math

from src.ui.menu_dialog import wrap_text_words

# Prefer single column for short lists; up to 3 when many and width allows.
SHORT_LIST_MAX = 8
MEDIUM_LIST_MAX = 14
MIN_COL_WIDTH = 14
COL_GAP = 2

# Back-compat aliases for internal use.
_SHORT_LIST_MAX = SHORT_LIST_MAX
_MEDIUM_LIST_MAX = MEDIUM_LIST_MAX
_MIN_COL_WIDTH = MIN_COL_WIDTH
_COL_GAP = COL_GAP


def choose_column_count(
    item_count: int,
    *,
    available_width: int,
    min_col_width: int = MIN_COL_WIDTH,
    gap: int = COL_GAP,
) -> int:
    """Dynamic columns by item count and available character/pixel-cell width.

    - Few items → always 1 column
    - Medium → up to 2 if width allows
    - Many → up to 3 if width allows
    """
    if item_count <= 0:
        return 1
    if item_count <= _SHORT_LIST_MAX:
        return 1
    if available_width < min_col_width:
        return 1
    max_by_width = max(1, (available_width + gap) // (min_col_width + gap))
    max_by_width = min(3, max_by_width)
    if item_count <= _MEDIUM_LIST_MAX:
        return min(2, max_by_width)
    return max_by_width


def content_column_width(
    item_lines: list[str],
    *,
    cols: int,
    available_width: int,
    gap: int = COL_GAP,
) -> int:
    """Character width per column: fit longest label, capped so ``cols`` fit.

    Short names (e.g. ``a) dagger``) stay compact; long names can grow the
    panel up to ``available_width``. Does not stretch columns to fill the
    full available width when content is narrow.
    """
    if cols <= 1:
        natural = max((len(line) for line in item_lines), default=1)
        return min(max(1, natural), max(1, available_width))
    max_cap = max(1, (available_width - gap * (cols - 1)) // cols)
    natural = max((len(line) for line in item_lines), default=1)
    return min(max(1, natural), max_cap)


def format_multi_column_block(
    item_lines: list[str],
    *,
    available_width: int,
    min_col_width: int = _MIN_COL_WIDTH,
    gap: int = _COL_GAP,
) -> str:
    """Format item rows into 1–3 columns; fill down each column, then next.

    Each item may wrap within its cell width. Column width is content-sized
    (not stretched to fill the window).
    """
    if not item_lines:
        return ""
    cols = choose_column_count(
        len(item_lines),
        available_width=available_width,
        min_col_width=min_col_width,
        gap=gap,
    )
    if cols <= 1:
        col_w = content_column_width(
            item_lines, cols=1, available_width=available_width, gap=gap
        )
        wrapped: list[str] = []
        for line in item_lines:
            wrapped.extend(wrap_text_words(line, max_width=col_w))
        return "\n".join(wrapped)

    col_width = content_column_width(
        item_lines,
        cols=cols,
        available_width=available_width,
        gap=gap,
    )
    rows_per_col = math.ceil(len(item_lines) / cols)

    # columns[c] = list of display lines for that column (items stacked)
    columns: list[list[str]] = []
    for c in range(cols):
        chunk = item_lines[c * rows_per_col : (c + 1) * rows_per_col]
        col_lines: list[str] = []
        for item in chunk:
            for wrapped_line in wrap_text_words(item, max_width=col_width):
                col_lines.append(wrapped_line[:col_width])
        columns.append(col_lines)

    height = max((len(col) for col in columns), default=0)
    pad = " " * gap
    out_rows: list[str] = []
    for r in range(height):
        parts: list[str] = []
        for c in range(cols):
            cell = columns[c][r] if r < len(columns[c]) else ""
            parts.append(cell.ljust(col_width)[:col_width])
        out_rows.append(pad.join(parts).rstrip())
    return "\n".join(out_rows)


def join_list_modal(title: str, item_lines: list[str], footer: str, *, available_width: int) -> str:
    """Title + multi-column items + footer with blank lines between sections."""
    body = format_multi_column_block(item_lines, available_width=available_width)
    blocks = [title]
    if body:
        blocks.append(body)
    if footer:
        blocks.append(footer)
    return "\n\n".join(blocks)
