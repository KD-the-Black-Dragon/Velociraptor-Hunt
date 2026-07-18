"""Shared layout + chrome for menu/play confirmation dialogs and notices."""

from __future__ import annotations

from typing import Literal

import tcod.console

from src.text import cp437_safe

# Lower band (below title logo), matching mod-mismatch notice placement.
MENU_DIALOG_BAND_OFFSET = 6
MENU_DIALOG_BODY_FG = (255, 220, 120)
MENU_DIALOG_ERROR_FG = (255, 160, 120)
MENU_DIALOG_HINT_FG = (140, 140, 140)
DIALOG_BG = (25, 20, 45)
DIALOG_BORDER_FG = (180, 160, 120)
DIALOG_PAD_X = 2
DIALOG_PAD_Y = 1


def wrap_text_words(text: str, *, max_width: int) -> list[str]:
    """Word-wrap a single paragraph to ``max_width`` character columns."""
    if max_width < 1:
        max_width = 1
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            while len(word) > max_width:
                lines.append(word[:max_width])
                word = word[max_width:]
            current = word
    if current:
        lines.append(current)
    return lines


def wrap_dialog_text(text: str, *, max_width: int) -> list[str]:
    """Wrap multi-line dialog text; preserve blank lines between paragraphs."""
    if not text:
        return []
    out: list[str] = []
    for paragraph in text.split("\n"):
        stripped = paragraph.strip()
        if not stripped:
            out.append("")
            continue
        out.extend(wrap_text_words(stripped, max_width=max_width))
    return out


def menu_dialog_max_width(console_width: int) -> int:
    """Max text columns inside the dialog (room for padding + border)."""
    # console - 4 margin - 2 border - 2*pad_x
    return min(70, max(16, console_width - 4 - 2 - 2 * DIALOG_PAD_X))


def menu_dialog_start_y(console_height: int, line_count: int) -> int:
    """Lower-band start row for **text** (inside pad), clamped on-screen."""
    preferred = console_height // 2 + MENU_DIALOG_BAND_OFFSET
    max_start = max(1 + DIALOG_PAD_Y, console_height - max(line_count, 1) - 1 - DIALOG_PAD_Y)
    return max(1 + DIALOG_PAD_Y, min(preferred, max_start))


def _dialog_box_geometry(
    console: tcod.console.Console,
    lines: list[str],
    *,
    band: Literal["lower", "center"],
) -> tuple[int, int, int, int, int]:
    """Return box_x, box_y, box_w, box_h, text_start_y."""
    inner_w = max((len(cp437_safe(line)) for line in lines), default=1)
    inner_w = min(inner_w, menu_dialog_max_width(console.width))
    box_w = min(console.width - 2, inner_w + 2 + 2 * DIALOG_PAD_X)
    box_h = min(console.height - 2, len(lines) + 2 + 2 * DIALOG_PAD_Y)
    box_x = max(1, (console.width - box_w) // 2)

    if band == "lower":
        text_y = menu_dialog_start_y(console.height, len(lines))
        box_y = max(1, text_y - DIALOG_PAD_Y - 1)
        # Keep box fully on-screen
        if box_y + box_h >= console.height:
            box_y = max(1, console.height - box_h - 1)
        text_y = box_y + 1 + DIALOG_PAD_Y
    else:
        box_y = max(1, (console.height - box_h) // 2)
        text_y = box_y + 1 + DIALOG_PAD_Y

    return box_x, box_y, box_w, box_h, text_y


def _draw_dialog_chrome(
    console: tcod.console.Console,
    box_x: int,
    box_y: int,
    box_w: int,
    box_h: int,
) -> None:
    """Filled panel with a simple frame border."""
    if box_w < 3 or box_h < 3:
        console.draw_rect(box_x, box_y, max(1, box_w), max(1, box_h), ch=ord(" "), fg=DIALOG_BORDER_FG, bg=DIALOG_BG)
        return
    try:
        console.draw_frame(
            box_x,
            box_y,
            box_w,
            box_h,
            fg=DIALOG_BORDER_FG,
            bg=DIALOG_BG,
        )
    except (AttributeError, TypeError):
        console.draw_rect(box_x, box_y, box_w, box_h, ch=ord(" "), fg=DIALOG_BORDER_FG, bg=DIALOG_BG)
        # Corners / edges with ASCII
        for x in range(box_x, box_x + box_w):
            console.print(x, box_y, "-", fg=DIALOG_BORDER_FG, bg=DIALOG_BG)
            console.print(x, box_y + box_h - 1, "-", fg=DIALOG_BORDER_FG, bg=DIALOG_BG)
        for y in range(box_y, box_y + box_h):
            console.print(box_x, y, "|", fg=DIALOG_BORDER_FG, bg=DIALOG_BG)
            console.print(box_x + box_w - 1, y, "|", fg=DIALOG_BORDER_FG, bg=DIALOG_BG)
        console.print(box_x, box_y, "+", fg=DIALOG_BORDER_FG, bg=DIALOG_BG)
        console.print(box_x + box_w - 1, box_y, "+", fg=DIALOG_BORDER_FG, bg=DIALOG_BG)
        console.print(box_x, box_y + box_h - 1, "+", fg=DIALOG_BORDER_FG, bg=DIALOG_BG)
        console.print(box_x + box_w - 1, box_y + box_h - 1, "+", fg=DIALOG_BORDER_FG, bg=DIALOG_BG)


def render_menu_dialog_lines(
    console: tcod.console.Console,
    lines: list[str],
    *,
    body_fg: tuple[int, int, int] = MENU_DIALOG_BODY_FG,
    error_line_index: int | None = None,
    error_fg: tuple[int, int, int] = MENU_DIALOG_ERROR_FG,
    hint_line_index: int | None = None,
    hint_fg: tuple[int, int, int] = MENU_DIALOG_HINT_FG,
    band: Literal["lower", "center"] = "lower",
) -> None:
    """Draw a chrome panel with centered lines (lower band or vertical center)."""
    if not lines:
        return
    box_x, box_y, box_w, box_h, text_y = _dialog_box_geometry(console, lines, band=band)
    _draw_dialog_chrome(console, box_x, box_y, box_w, box_h)

    inner_w = box_w - 2 - 2 * DIALOG_PAD_X
    for index, line in enumerate(lines):
        safe = cp437_safe(line)[: max(0, inner_w)]
        x = box_x + 1 + DIALOG_PAD_X + max(0, (inner_w - len(safe)) // 2)
        if error_line_index is not None and index == error_line_index:
            fg = error_fg
        elif hint_line_index is not None and index == hint_line_index:
            fg = hint_fg
        else:
            fg = body_fg
        y = text_y + index
        if 0 <= y < console.height and 0 <= x < console.width:
            console.print(x, y, safe, fg=fg, bg=DIALOG_BG)


def render_confirm_dialog(
    console: tcod.console.Console,
    body_lines: list[str] | tuple[str, ...],
    *,
    error_message: str = "",
    band: Literal["lower", "center"] = "center",
) -> None:
    """Convenience: wrap body (+ optional error) and render with chrome."""
    max_width = menu_dialog_max_width(console.width)
    lines: list[str] = []
    for index, raw in enumerate(body_lines):
        if index > 0:
            lines.append("")
        lines.extend(wrap_dialog_text(raw, max_width=max_width))
    error_index: int | None = None
    if error_message:
        lines.append("")
        error_lines = wrap_dialog_text(error_message, max_width=max_width)
        error_index = len(lines)
        lines.extend(error_lines)
    render_menu_dialog_lines(
        console,
        lines,
        error_line_index=error_index,
        band=band,
    )
