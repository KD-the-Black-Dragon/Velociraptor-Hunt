"""Pixel-accurate proportional rendering for the message log panel."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import tcod.sdl.render

from src.log_categories import MessageCategory
from src.log_markup import LogSegment
from src.message_log import LogEntry
from src.systems.render import MESSAGE_LOG_BACKGROUND, LogDisplayLine
from src.text import cp437_safe
from src.ui.layout import UILayout
from src.ui.log_overlay import clamp_scroll_offset

LOG_HORIZONTAL_PADDING_PX = 8
LOG_VERTICAL_PADDING_PX = 3


def log_panel_pixel_size(layout: UILayout) -> tuple[int, int]:
    """Message log region size in screen pixels (before integer window scale)."""
    rect = layout.region("message_log")
    cell = layout.tile_px * layout.tile_scale
    return rect.w * cell, rect.h * cell


def log_text_area_width_px(layout: UILayout) -> int:
    panel_w, _ = log_panel_pixel_size(layout)
    return max(1, panel_w - LOG_HORIZONTAL_PADDING_PX * 2)


def proportional_font_size_px(tile_px: int, tile_scale: int) -> int:
    """Pick a readable body size tuned for eight lines in the stock log panel."""
    cell = tile_px * tile_scale
    return max(12, int(cell * 0.80))


def load_proportional_font(path: Path | str, *, size_px: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size_px)


def line_height_px(font: ImageFont.FreeTypeFont) -> int:
    ascent, descent = font.getmetrics()
    return ascent + descent + 2


def proportional_lines_fit_in_panel(
    *,
    font: ImageFont.FreeTypeFont,
    layout: UILayout,
    line_count: int,
) -> bool:
    """Return True when ``line_count`` proportional rows fit in the log panel."""
    _, panel_h = log_panel_pixel_size(layout)
    needed = LOG_VERTICAL_PADDING_PX * 2 + line_height_px(font) * line_count
    return needed <= panel_h


def measure_text(font: ImageFont.FreeTypeFont, text: str) -> float:
    if not text:
        return 0.0
    return float(font.getlength(text))


def wrap_log_text_pixels(text: str, *, font: ImageFont.FreeTypeFont, max_width_px: int) -> list[str]:
    """Word-wrap plain text to a pixel width.

    Single newlines keep lines adjacent. Only blank source lines (``\\n\\n``)
    insert one empty row; consecutive blanks collapse to a single gap.
    """
    if not text:
        return []
    if max_width_px <= 0:
        return [text]
    lines: list[str] = []
    for segment in text.split("\n"):
        stripped = segment.strip()
        if not stripped:
            if lines and lines[-1] != "":
                lines.append("")
            continue
        lines.extend(_wrap_words_pixels(stripped, font=font, max_inner=max_width_px))
    return lines


def _wrap_words_pixels(
    text: str,
    *,
    font: ImageFont.FreeTypeFont,
    max_inner: int,
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if measure_text(font, candidate) <= max_inner:
            current = candidate
        elif current:
            lines.append(current)
            current = word
        else:
            lines.append(word)
            current = ""
    if current:
        lines.append(current)
    return lines


def wrap_log_segments_pixels(
    segments: tuple[LogSegment, ...],
    *,
    font: ImageFont.FreeTypeFont,
    max_width_px: int,
) -> list[tuple[LogSegment, ...]]:
    """Word-wrap colored segments to a pixel width without splitting words."""
    if not segments or max_width_px <= 0:
        return [segments]

    rows: list[tuple[LogSegment, ...]] = []

    def flush_row(parts: list[tuple[str, tuple[int, int, int]]]) -> None:
        if not parts:
            return
        coalesced: list[LogSegment] = []
        for word, fg in parts:
            prefix = "" if not coalesced else " "
            piece = prefix + word
            if coalesced and coalesced[-1].fg == fg:
                last = coalesced[-1]
                coalesced[-1] = LogSegment(text=last.text + piece, fg=fg)
            else:
                coalesced.append(LogSegment(text=piece, fg=fg))
        rows.append(tuple(coalesced))

    logical_lines: list[list[tuple[str, tuple[int, int, int]]]] = [[]]
    for segment in segments:
        parts = segment.text.split("\n")
        for line_index, line in enumerate(parts):
            if line_index > 0:
                logical_lines.append([])
            for word in line.split():
                if word:
                    logical_lines[-1].append((word, segment.fg))

    space_w = measure_text(font, " ")
    for line_words in logical_lines:
        row_parts: list[tuple[str, tuple[int, int, int]]] = []
        row_len = 0.0
        for word, fg in line_words:
            word_w = measure_text(font, word)
            extra = word_w + (space_w if row_parts else 0.0)
            if row_parts and row_len + extra > max_width_px:
                flush_row(row_parts)
                row_parts = [(word, fg)]
                row_len = word_w
            else:
                row_parts.append((word, fg))
                row_len += extra
        flush_row(row_parts)

    return rows or [segments]


def expand_log_entries_to_display_lines_pixels(
    messages: list[LogEntry] | list[str] | None,
    *,
    font: ImageFont.FreeTypeFont,
    width_limit_px: int,
) -> list[LogDisplayLine]:
    """Expand log entries into wrapped display lines using proportional metrics."""
    if not messages:
        return []
    display: list[LogDisplayLine] = []
    for entry in messages:
        if isinstance(entry, str):
            safe = cp437_safe(entry)
            for line in wrap_log_text_pixels(safe, font=font, max_width_px=width_limit_px):
                display.append(
                    LogDisplayLine(
                        segments=(
                            LogSegment(text=line, fg=MessageCategory.ROUTINE.fg),
                        )
                    )
                )
            continue
        for row in wrap_log_segments_pixels(
            entry.display_segments(),
            font=font,
            max_width_px=width_limit_px,
        ):
            if row:
                display.append(LogDisplayLine(segments=row))
    return display


def render_proportional_log_image(
    messages: list[LogEntry] | list[str] | None,
    *,
    font: ImageFont.FreeTypeFont,
    layout: UILayout,
    max_lines: int,
) -> Image.Image:
    """Rasterize the message log panel to an RGBA image."""
    panel_w, panel_h = log_panel_pixel_size(layout)
    image = Image.new("RGBA", (panel_w, panel_h), (*MESSAGE_LOG_BACKGROUND, 255))
    if not messages or max_lines <= 0:
        return image

    width_limit_px = log_text_area_width_px(layout)
    display_lines = expand_log_entries_to_display_lines_pixels(
        messages,
        font=font,
        width_limit_px=width_limit_px,
    )
    visible_lines = display_lines[-max_lines:]
    draw = ImageDraw.Draw(image)
    row_h = line_height_px(font)
    y = LOG_VERTICAL_PADDING_PX
    for line in visible_lines:
        if y + row_h > panel_h:
            break
        x = float(LOG_HORIZONTAL_PADDING_PX)
        for segment in line.segments:
            if not segment.text:
                continue
            draw.text(
                (x, y),
                segment.text,
                font=font,
                fill=(*segment.fg, 255),
            )
            x += measure_text(font, segment.text)
        y += row_h
    return image


def overlay_panel_pixel_size(layout: UILayout) -> tuple[int, int]:
    """Full root console size in screen pixels."""
    cell = layout.tile_px * layout.tile_scale
    return layout.root_cols * cell, layout.root_rows * cell


def overlay_text_area_width_px(layout: UILayout) -> int:
    panel_w, _ = overlay_panel_pixel_size(layout)
    return max(1, panel_w - LOG_HORIZONTAL_PADDING_PX * 2)


def render_proportional_overlay_image(
    messages: list[LogEntry] | list[str] | None,
    *,
    font: ImageFont.FreeTypeFont,
    layout: UILayout,
    scroll_offset: int,
    viewport_lines: int,
    footer_text: str,
    footer_fg: tuple[int, int, int],
) -> Image.Image:
    """Rasterize the full-screen log overlay with scroll."""
    panel_w, panel_h = overlay_panel_pixel_size(layout)
    image = Image.new("RGBA", (panel_w, panel_h), (*MESSAGE_LOG_BACKGROUND, 255))
    if not messages or viewport_lines <= 0:
        return image

    display_lines = expand_log_entries_to_display_lines_pixels(
        messages,
        font=font,
        width_limit_px=overlay_text_area_width_px(layout),
    )
    line_count = len(display_lines)
    offset = clamp_scroll_offset(
        scroll_offset,
        line_count=line_count,
        viewport_lines=viewport_lines,
    )
    visible_lines = display_lines[offset : offset + viewport_lines]
    draw = ImageDraw.Draw(image)
    row_h = line_height_px(font)
    y = LOG_VERTICAL_PADDING_PX
    for line in visible_lines:
        if y + row_h > panel_h - row_h:
            break
        x = float(LOG_HORIZONTAL_PADDING_PX)
        for segment in line.segments:
            if not segment.text:
                continue
            draw.text(
                (x, y),
                segment.text,
                font=font,
                fill=(*segment.fg, 255),
            )
            x += measure_text(font, segment.text)
        y += row_h

    footer_y = panel_h - row_h - LOG_VERTICAL_PADDING_PX
    footer_w = measure_text(font, footer_text)
    footer_x = max(LOG_HORIZONTAL_PADDING_PX, (panel_w - footer_w) / 2)
    draw.text(
        (footer_x, footer_y),
        footer_text,
        font=font,
        fill=(*footer_fg, 255),
    )
    return image


def render_proportional_help_image(
    lines: tuple["HelpTextLine", ...],
    *,
    font: ImageFont.FreeTypeFont,
    layout: UILayout,
    footer_text: str,
    footer_fg: tuple[int, int, int],
) -> Image.Image:
    """Rasterize the full-screen help overlay with the log proportional font."""
    panel_w, panel_h = overlay_panel_pixel_size(layout)
    image = Image.new("RGBA", (panel_w, panel_h), (*MESSAGE_LOG_BACKGROUND, 255))
    draw = ImageDraw.Draw(image)
    row_h = line_height_px(font)
    y = float(LOG_VERTICAL_PADDING_PX)
    footer_reserve = row_h + LOG_VERTICAL_PADDING_PX
    blank_advance = row_h * 0.45

    for entry in lines:
        if y + row_h > panel_h - footer_reserve:
            break
        if not entry.text:
            y += blank_advance
            continue
        draw.text(
            (float(LOG_HORIZONTAL_PADDING_PX), y),
            entry.text,
            font=font,
            fill=(*entry.fg, 255),
        )
        y += row_h

    footer_y = panel_h - row_h - LOG_VERTICAL_PADDING_PX
    footer_w = measure_text(font, footer_text)
    footer_x = max(LOG_HORIZONTAL_PADDING_PX, (panel_w - footer_w) / 2)
    draw.text(
        (footer_x, footer_y),
        footer_text,
        font=font,
        fill=(*footer_fg, 255),
    )
    return image


def render_proportional_help_texture(
    renderer: tcod.sdl.render.Renderer,
    lines: tuple["HelpTextLine", ...],
    *,
    font: ImageFont.FreeTypeFont,
    layout: UILayout,
    footer_text: str,
    footer_fg: tuple[int, int, int],
) -> tcod.sdl.render.Texture:
    """Upload the proportional help overlay as an SDL texture."""
    image = render_proportional_help_image(
        lines,
        font=font,
        layout=layout,
        footer_text=footer_text,
        footer_fg=footer_fg,
    )
    pixels = np.asarray(image, dtype=np.uint8)
    return renderer.upload_texture(pixels)


def render_proportional_overlay_texture(
    renderer: tcod.sdl.render.Renderer,
    messages: list[LogEntry] | list[str] | None,
    *,
    font: ImageFont.FreeTypeFont,
    layout: UILayout,
    scroll_offset: int,
    viewport_lines: int,
    footer_text: str,
    footer_fg: tuple[int, int, int],
) -> tcod.sdl.render.Texture:
    """Upload the full-screen proportional log overlay as an SDL texture."""
    image = render_proportional_overlay_image(
        messages,
        font=font,
        layout=layout,
        scroll_offset=scroll_offset,
        viewport_lines=viewport_lines,
        footer_text=footer_text,
        footer_fg=footer_fg,
    )
    pixels = np.asarray(image, dtype=np.uint8)
    return renderer.upload_texture(pixels)


def render_proportional_log_texture(
    renderer: tcod.sdl.render.Renderer,
    messages: list[LogEntry] | list[str] | None,
    *,
    font: ImageFont.FreeTypeFont,
    layout: UILayout,
    max_lines: int,
) -> tcod.sdl.render.Texture:
    """Upload the proportional log panel as an SDL texture."""
    image = render_proportional_log_image(
        messages,
        font=font,
        layout=layout,
        max_lines=max_lines,
    )
    pixels = np.asarray(image, dtype=np.uint8)
    return renderer.upload_texture(pixels)