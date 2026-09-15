"""Proportional hunt thought log in the lower-right panel."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

import tcod.console
import tcod.context
import tcod.sdl.render

from src.message_log import LogEntry
from src.systems.render import MESSAGE_LOG_BACKGROUND
from src.ui.layout import UILayout
from src.ui.proportional_log import (
    LOG_HORIZONTAL_PADDING_PX,
    LOG_VERTICAL_PADDING_PX,
    expand_log_entries_to_display_lines_pixels,
    line_height_px,
    measure_text,
)
from src.ui.log_present import compute_console_viewport
from src.hunt_panel import hunt_log_tile_rect


def render_hunt_log_image(
    messages: list[LogEntry],
    *,
    font: ImageFont.FreeTypeFont,
    width_px: int,
    height_px: int,
    max_lines: int,
) -> Image.Image:
    image = Image.new("RGBA", (max(1, width_px), max(1, height_px)), (*MESSAGE_LOG_BACKGROUND, 255))
    if not messages or max_lines <= 0:
        return image
    width_limit = max(1, width_px - LOG_HORIZONTAL_PADDING_PX * 2)
    display = expand_log_entries_to_display_lines_pixels(
        messages, font=font, width_limit_px=width_limit,
    )
    visible = display[-max_lines:]
    draw = ImageDraw.Draw(image)
    row_h = line_height_px(font)
    y = LOG_VERTICAL_PADDING_PX
    for line in visible:
        if y + row_h > height_px:
            break
        x = float(LOG_HORIZONTAL_PADDING_PX)
        for segment in line.segments:
            if not segment.text:
                continue
            draw.text((x, y), segment.text, font=font, fill=(*segment.fg, 255))
            x += measure_text(font, segment.text)
        y += row_h
    return image


def present_hunt_with_log(
    context: tcod.context.Context,
    console: tcod.console.Console,
    *,
    log_entries: list[LogEntry],
    font: ImageFont.FreeTypeFont,
    layout: UILayout,
    integer_scaling: bool = True,
) -> None:
    renderer = context.sdl_renderer
    if renderer is None:
        context.present(console, integer_scaling=integer_scaling, align=(0, 0))
        return
    import numpy as np
    import tcod.render

    scale, dest_x, dest_y, dest_w, dest_h = compute_console_viewport(
        renderer.output_size,
        console,
        layout,
        integer_scaling=integer_scaling,
        align=(0, 0),
    )
    renderer.clear()
    atlas = context.sdl_atlas
    if atlas is None:
        context.present(console, integer_scaling=integer_scaling, align=(0, 0))
        return
    main_tex = tcod.render.SDLConsoleRender(atlas).render(console)
    renderer.copy(main_tex, dest=(dest_x, dest_y, dest_w, dest_h))
    tx, ty, tw, th = hunt_log_tile_rect(console.width, console.height)
    cell = layout.tile_px * layout.tile_scale * scale
    px = int(dest_x + tx * cell)
    py = int(dest_y + ty * cell)
    pw = max(8, int(tw * cell))
    ph = max(8, int(th * cell))
    max_lines = max(3, ph // max(1, line_height_px(font)))
    image = render_hunt_log_image(
        log_entries, font=font, width_px=pw, height_px=ph, max_lines=max_lines,
    )
    tex = renderer.upload_texture(np.asarray(image, dtype=np.uint8))
    try:
        tex.blend_mode = tcod.sdl.render.BlendMode.BLEND
    except (AttributeError, TypeError):
        pass
    renderer.copy(tex, dest=(px, py, pw, ph))
    renderer.present()
