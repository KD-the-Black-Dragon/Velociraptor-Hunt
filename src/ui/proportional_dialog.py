"""Proportional (log font) dialog panels — narrative + multi-column inventory lists."""

from __future__ import annotations

import math

from PIL import Image, ImageDraw, ImageFont

from src.text import cp437_safe
from src.ui.inventory_list_layout import (
    COL_GAP as _CHAR_COL_GAP,
    choose_column_count,
)
from src.ui.layout import UILayout
from src.ui.menu_dialog import (
    DIALOG_BG,
    DIALOG_BORDER_FG,
    MENU_DIALOG_BODY_FG,
    MENU_DIALOG_ERROR_FG,
    MENU_DIALOG_HINT_FG,
)
from src.ui.log_font import LogFontState
from src.ui.proportional_log import (
    LOG_HORIZONTAL_PADDING_PX,
    LOG_VERTICAL_PADDING_PX,
    line_height_px,
    load_proportional_font,
    measure_text,
    wrap_log_text_pixels,
)

# Soft border thickness in pixels for the trial panel.
_BORDER_PX = 2
# Was 0.72 of root width; reduced to 80% of that for a narrower narrative column.
_MAX_PANEL_FRACTION_W = 0.72 * 0.8
_MAX_PANEL_FRACTION_H = 0.55
# Utilitarian lists need more width for 2–3 columns of letter+name rows.
_LIST_MAX_PANEL_FRACTION_W = 0.88
_LIST_MAX_PANEL_FRACTION_H = 0.72
DIALOG_FONT_SIZE_DELTA = 2
# Extra horizontal inset so body text sits farther from the side borders.
_DIALOG_H_PAD_PX = LOG_HORIZONTAL_PADDING_PX + 14
# Body line advance as a multiple of font line height: looser than tight single
# spacing, much tighter than a full blank row (``\\n\\n``).
_BODY_LINE_SPACING = 1.28
# Intentional paragraph blanks (empty wrap rows) as a fraction of line height.
_BODY_BLANK_SPACING = 0.5
DIGESTION_MODAL_FOOTER = "Press Enter"
LIST_MODAL_FOOTER = "Esc: close"
GAME_OVER_FOOTER = "Press Enter to return to menu"
GAME_OVER_TITLE = "GAME OVER"


def dialog_font_from_log_font(log_font: LogFontState) -> ImageFont.FreeTypeFont | None:
    """Log font sized +2 for narrative dialogs; falls back to the loaded log face."""
    if log_font.font is None:
        return None
    if log_font.font_path is not None:
        try:
            return load_proportional_font(
                log_font.font_path,
                size_px=log_font.font_size_px + DIALOG_FONT_SIZE_DELTA,
            )
        except (OSError, ValueError):
            return log_font.font
    return log_font.font


def root_console_pixel_size(layout: UILayout, console_w: int, console_h: int) -> tuple[int, int]:
    cell = layout.tile_px * layout.tile_scale
    return console_w * cell, console_h * cell


def _draw_dialog_panel_lines(
    body_lines: list[str],
    *,
    font: ImageFont.FreeTypeFont,
    layout: UILayout,
    console_w: int,
    console_h: int,
    footer_text: str = "",
    body_fg: tuple[int, int, int] = MENU_DIALOG_BODY_FG,
    footer_fg: tuple[int, int, int] = MENU_DIALOG_HINT_FG,
    error_line_indices: frozenset[int] | None = None,
    error_fg: tuple[int, int, int] = MENU_DIALOG_ERROR_FG,
    max_panel_fraction_w: float = _MAX_PANEL_FRACTION_W,
    max_panel_fraction_h: float = _MAX_PANEL_FRACTION_H,
    # Narrative (digestion): extra top inset. Confirms: center content in box.
    body_vcenter: bool = False,
    extra_top_pad_lines: float = 1.0,
    min_content_lines: float = 4.0,
) -> Image.Image:
    """Shared chrome + spaced body lines + optional footer."""
    root_w, root_h = root_console_pixel_size(layout, console_w, console_h)
    max_panel_w = max(120, int(root_w * max_panel_fraction_w))
    max_panel_h = max(80, int(root_h * max_panel_fraction_h))

    if not body_lines:
        body_lines = [""]

    row_h = line_height_px(font)
    content_advance = row_h * _BODY_LINE_SPACING
    blank_advance = row_h * _BODY_BLANK_SPACING
    footer_lines = [footer_text] if footer_text else []
    top_text_pad = row_h * extra_top_pad_lines
    body_h = sum(blank_advance if not line else content_advance for line in body_lines)
    footer_block = (row_h * 0.35 + row_h * len(footer_lines)) if footer_lines else 0.0
    # ceil so float line advances never clip the last row (was dropping error text).
    needed_h = int(
        math.ceil(
            LOG_VERTICAL_PADDING_PX * 2
            + _BORDER_PX * 2
            + top_text_pad
            + body_h
            + footer_block
            + 1  # safety pixel against float rounding
        )
    )
    min_h = int(math.ceil(row_h * min_content_lines)) if min_content_lines > 0 else 0
    panel_h = min(max_panel_h, max(needed_h, min_h))
    content_w = 0.0
    for line in body_lines:
        content_w = max(content_w, measure_text(font, line))
    for line in footer_lines:
        content_w = max(content_w, measure_text(font, line))
    panel_w = min(
        max_panel_w,
        max(int(math.ceil(content_w)) + _DIALOG_H_PAD_PX * 2 + _BORDER_PX * 2, 160),
    )

    image = Image.new("RGBA", (panel_w, panel_h), (*DIALOG_BG, 255))
    draw = ImageDraw.Draw(image)
    for i in range(_BORDER_PX):
        draw.rectangle(
            [i, i, panel_w - 1 - i, panel_h - 1 - i],
            outline=(*DIALOG_BORDER_FG, 255),
        )

    text_area_w = panel_w - _DIALOG_H_PAD_PX * 2 - _BORDER_PX * 2
    bottom_reserve = LOG_VERTICAL_PADDING_PX + _BORDER_PX + (
        row_h if footer_lines else 0
    )
    if body_vcenter:
        # Center the body block between top border pad and footer/bottom pad.
        available = panel_h - LOG_VERTICAL_PADDING_PX * 2 - _BORDER_PX * 2 - footer_block
        y = float(
            LOG_VERTICAL_PADDING_PX
            + _BORDER_PX
            + max(0.0, (available - body_h) / 2)
        )
    else:
        y = float(LOG_VERTICAL_PADDING_PX + _BORDER_PX + top_text_pad)

    error_set = error_line_indices if error_line_indices is not None else frozenset()
    for index, line in enumerate(body_lines):
        advance = blank_advance if not line else content_advance
        # Only skip when the baseline itself is past the usable area.
        if y >= panel_h - bottom_reserve:
            break
        if line:
            tw = measure_text(font, line)
            x = _BORDER_PX + _DIALOG_H_PAD_PX + max(0.0, (text_area_w - tw) / 2)
            fg = error_fg if index in error_set else body_fg
            draw.text((x, y), line, font=font, fill=(*fg, 255))
        y += advance

    if footer_lines:
        footer = footer_lines[0]
        tw = measure_text(font, footer)
        x = _BORDER_PX + _DIALOG_H_PAD_PX + max(0.0, (text_area_w - tw) / 2)
        footer_y = panel_h - LOG_VERTICAL_PADDING_PX - _BORDER_PX - row_h
        draw.text((x, footer_y), footer, font=font, fill=(*footer_fg, 255))

    return image


def render_proportional_dialog_image(
    body_text: str,
    *,
    font: ImageFont.FreeTypeFont,
    layout: UILayout,
    console_w: int,
    console_h: int,
    footer_text: str = DIGESTION_MODAL_FOOTER,
    body_fg: tuple[int, int, int] = MENU_DIALOG_BODY_FG,
    footer_fg: tuple[int, int, int] = MENU_DIALOG_HINT_FG,
) -> Image.Image:
    """Rasterize a centered dialog: chrome + wrapped body + footer (whole panel log font)."""
    root_w, _root_h = root_console_pixel_size(layout, console_w, console_h)
    max_panel_w = max(120, int(root_w * _MAX_PANEL_FRACTION_W))
    text_max_w = max(40, max_panel_w - _DIALOG_H_PAD_PX * 2 - _BORDER_PX * 2)
    plain = cp437_safe(body_text)
    body_lines = wrap_log_text_pixels(plain, font=font, max_width_px=text_max_w)
    return _draw_dialog_panel_lines(
        body_lines,
        font=font,
        layout=layout,
        console_w=console_w,
        console_h=console_h,
        footer_text=footer_text,
        body_fg=body_fg,
        footer_fg=footer_fg,
        body_vcenter=False,
        extra_top_pad_lines=1.0,
        min_content_lines=4.0,
    )


def render_proportional_confirm_image(
    body_paragraphs: list[str] | tuple[str, ...],
    *,
    font: ImageFont.FreeTypeFont,
    layout: UILayout,
    console_w: int,
    console_h: int,
    error_message: str = "",
    footer_text: str = "",
    body_fg: tuple[int, int, int] = MENU_DIALOG_BODY_FG,
    error_fg: tuple[int, int, int] = MENU_DIALOG_ERROR_FG,
    footer_fg: tuple[int, int, int] = MENU_DIALOG_HINT_FG,
) -> Image.Image:
    """Y/n-style confirm: whole panel log font; error line in error color.

    Content is vertically centered in a content-hugging box (no tall empty pad).
    """
    root_w, _root_h = root_console_pixel_size(layout, console_w, console_h)
    max_panel_w = max(120, int(root_w * _MAX_PANEL_FRACTION_W))
    text_max_w = max(40, max_panel_w - _DIALOG_H_PAD_PX * 2 - _BORDER_PX * 2)

    body_lines: list[str] = []
    for index, paragraph in enumerate(body_paragraphs):
        if index > 0:
            body_lines.append("")
        body_lines.extend(
            wrap_log_text_pixels(cp437_safe(paragraph), font=font, max_width_px=text_max_w)
        )
    error_indices: set[int] = set()
    if error_message:
        body_lines.append("")
        start = len(body_lines)
        err_lines = wrap_log_text_pixels(
            cp437_safe(error_message), font=font, max_width_px=text_max_w
        )
        body_lines.extend(err_lines)
        # Color only non-empty error lines (not the spacer blank).
        for i in range(start, len(body_lines)):
            if body_lines[i]:
                error_indices.add(i)

    return _draw_dialog_panel_lines(
        body_lines,
        font=font,
        layout=layout,
        console_w=console_w,
        console_h=console_h,
        footer_text=footer_text,
        body_fg=body_fg,
        footer_fg=footer_fg,
        error_line_indices=frozenset(error_indices),
        error_fg=error_fg,
        # Slightly taller cap so multi-paragraph mods prompt + error fit.
        max_panel_fraction_h=0.72,
        body_vcenter=True,
        extra_top_pad_lines=0.0,
        min_content_lines=0.0,
    )


def game_over_body_paragraphs(
    *,
    player_name: str,
    ending_line: str,
    monsters_defeated: int,
    runes_collected: int,
    depth: int,
    include_title: bool = True,
) -> list[str]:
    """Game-over panel lines.

    When *include_title* is True (proportional path with screen haze), the
    title sits in the same golden-bordered panel above the veil so it is not
    dimmed with the world behind.
    """
    lines: list[str] = []
    if include_title:
        lines.append(GAME_OVER_TITLE)
    lines.extend(
        [
            player_name,
            ending_line,
            f"Monsters defeated: {monsters_defeated}",
            f"Runes collected: {runes_collected}",
            f"Depth: {depth}",
        ]
    )
    return lines


def _avg_char_width_px(font: ImageFont.FreeTypeFont) -> float:
    sample = "abcdefghijklmnopqrstuvwxyz) "
    return max(1.0, measure_text(font, sample) / len(sample))


def _content_col_width_px(
    item_lines: list[str],
    *,
    font: ImageFont.FreeTypeFont,
    cols: int,
    text_max_w: int,
    gap_px: int,
) -> int:
    """Pixel column width from longest label, capped so columns fit — not stretched."""
    if not item_lines:
        return max(1, text_max_w)
    natural = max(measure_text(font, cp437_safe(line)) for line in item_lines)
    if cols <= 1:
        return max(1, min(int(math.ceil(natural)), text_max_w))
    max_cap = max(1, (text_max_w - gap_px * (cols - 1)) // cols)
    return max(1, min(int(math.ceil(natural)), max_cap))


def _layout_list_columns(
    item_lines: list[str],
    *,
    font: ImageFont.FreeTypeFont,
    text_max_w: int,
) -> tuple[int, int, int, list[list[str]]]:
    """Return (cols, col_width_px, gap_px, columns of display lines) fill-down then next.

    Column width is content-sized (short names stay compact).
    """
    avg = _avg_char_width_px(font)
    available_chars = max(1, int(text_max_w / avg))
    cols = choose_column_count(len(item_lines), available_width=available_chars)
    gap_px = max(8, int(avg * _CHAR_COL_GAP)) if cols > 1 else 0
    col_width_px = _content_col_width_px(
        item_lines,
        font=font,
        cols=cols,
        text_max_w=text_max_w,
        gap_px=gap_px,
    )

    if cols <= 1:
        wrapped: list[str] = []
        for line in item_lines:
            wrapped.extend(
                wrap_log_text_pixels(
                    cp437_safe(line), font=font, max_width_px=col_width_px
                )
            )
        # Tighten further to actual wrapped lines (no forced full width).
        if wrapped:
            col_width_px = max(
                1,
                int(math.ceil(max(measure_text(font, ln) for ln in wrapped))),
            )
        return 1, col_width_px, 0, [wrapped]

    rows_per_col = math.ceil(len(item_lines) / cols)
    columns: list[list[str]] = []
    for c in range(cols):
        chunk = item_lines[c * rows_per_col : (c + 1) * rows_per_col]
        col_lines: list[str] = []
        for item in chunk:
            col_lines.extend(
                wrap_log_text_pixels(
                    cp437_safe(item), font=font, max_width_px=col_width_px
                )
            )
        columns.append(col_lines)
    # Tighten col width to actual ink after wrap (equal columns for alignment).
    actual = 0.0
    for col in columns:
        for ln in col:
            actual = max(actual, measure_text(font, ln))
    if actual > 0:
        col_width_px = max(1, min(col_width_px, int(math.ceil(actual))))
    return cols, col_width_px, gap_px, columns


def render_proportional_list_dialog_image(
    title: str,
    item_lines: list[str],
    *,
    font: ImageFont.FreeTypeFont,
    layout: UILayout,
    console_w: int,
    console_h: int,
    footer_text: str = LIST_MODAL_FOOTER,
    body_fg: tuple[int, int, int] = MENU_DIALOG_BODY_FG,
    footer_fg: tuple[int, int, int] = MENU_DIALOG_HINT_FG,
    title_fg: tuple[int, int, int] = MENU_DIALOG_BODY_FG,
) -> Image.Image:
    """Rasterize multi-column inventory/pickup list (digestion dialog font).

    Panel width hugs content (short labels stay compact across 1–3 columns).
    """
    root_w, root_h = root_console_pixel_size(layout, console_w, console_h)
    max_panel_w = max(160, int(root_w * _LIST_MAX_PANEL_FRACTION_W))
    max_panel_h = max(100, int(root_h * _LIST_MAX_PANEL_FRACTION_H))
    text_max_w = max(40, max_panel_w - _DIALOG_H_PAD_PX * 2 - _BORDER_PX * 2)

    cols, col_width_px, gap_px, columns = _layout_list_columns(
        item_lines, font=font, text_max_w=text_max_w
    )
    body_height_lines = max((len(col) for col in columns), default=0)
    body_content_w = float(col_width_px * cols + gap_px * max(0, cols - 1))

    # Title/footer wrap to body width first so a short list stays skinny;
    # long titles still grow the panel via content_w below.
    title_wrap_w = max(40, int(math.ceil(body_content_w)) if item_lines else text_max_w)
    title_wrap_w = min(text_max_w, max(title_wrap_w, int(measure_text(font, cp437_safe(title)) or 40)))
    title_lines = wrap_log_text_pixels(
        cp437_safe(title), font=font, max_width_px=title_wrap_w
    ) or [""]
    footer_lines = [footer_text] if footer_text else []
    row_h = line_height_px(font)
    top_text_pad = row_h
    section_gap = row_h // 2
    needed_h = (
        LOG_VERTICAL_PADDING_PX * 2
        + _BORDER_PX * 2
        + top_text_pad
        + row_h * len(title_lines)
        + section_gap
        + row_h * body_height_lines
        + section_gap
        + row_h * len(footer_lines)
    )
    panel_h = min(max_panel_h, max(needed_h, row_h * 5))

    content_w = body_content_w
    for line in title_lines:
        content_w = max(content_w, measure_text(font, line))
    for line in footer_lines:
        content_w = max(content_w, measure_text(font, line))
    # Hug content; only a modest floor so chrome doesn't look broken.
    panel_w = min(
        max_panel_w,
        max(int(math.ceil(content_w)) + _DIALOG_H_PAD_PX * 2 + _BORDER_PX * 2, 120),
    )
    text_area_w = panel_w - _DIALOG_H_PAD_PX * 2 - _BORDER_PX * 2

    image = Image.new("RGBA", (panel_w, panel_h), (*DIALOG_BG, 255))
    draw = ImageDraw.Draw(image)
    for i in range(_BORDER_PX):
        draw.rectangle(
            [i, i, panel_w - 1 - i, panel_h - 1 - i],
            outline=(*DIALOG_BORDER_FG, 255),
        )

    y = float(LOG_VERTICAL_PADDING_PX + _BORDER_PX + top_text_pad)
    base_x = float(_BORDER_PX + _DIALOG_H_PAD_PX)

    for line in title_lines:
        tw = measure_text(font, line)
        x = base_x + max(0.0, (text_area_w - tw) / 2)
        draw.text((x, y), line, font=font, fill=(*title_fg, 255))
        y += row_h
    y += section_gap

    footer_reserve = row_h * len(footer_lines) + section_gap
    body_bottom = panel_h - LOG_VERTICAL_PADDING_PX - _BORDER_PX - footer_reserve

    if cols <= 1:
        for line in columns[0] if columns else []:
            if y + row_h > body_bottom:
                break
            draw.text((base_x, y), line, font=font, fill=(*body_fg, 255))
            y += row_h
    else:
        for r in range(body_height_lines):
            if y + row_h > body_bottom:
                break
            for c in range(cols):
                if r >= len(columns[c]):
                    continue
                cell = columns[c][r]
                x = base_x + c * (col_width_px + gap_px)
                draw.text((x, y), cell, font=font, fill=(*body_fg, 255))
            y += row_h

    if footer_lines:
        y = max(y + section_gap, body_bottom)
        footer = footer_lines[0]
        tw = measure_text(font, footer)
        x = base_x + max(0.0, (text_area_w - tw) / 2)
        footer_y = min(y, panel_h - LOG_VERTICAL_PADDING_PX - _BORDER_PX - row_h)
        draw.text((x, footer_y), footer, font=font, fill=(*footer_fg, 255))

    return image
