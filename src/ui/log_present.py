"""Present the play frame with a proportional message log composite."""

from __future__ import annotations

import tcod.console
import tcod.context
import tcod.render
import tcod.sdl.render

from src.message_log import LogEntry
from src.ui.layout import RegionRect, UILayout
from src.ui.log_font import LogFontState
from src.ui.credits_screen import credits_display_lines
from src.ui.help_overlay import (
    HELP_FOOTER_FG,
    HELP_OVERLAY_FOOTER,
    help_display_lines,
)
from src.ui.log_overlay import LOG_OVERLAY_FOOTER, LOG_OVERLAY_FOOTER_FG, LogOverlayState
from src.tutorial_prompt import (
    TutorialPromptState,
    render_proportional_tutorial_prompt_texture,
)
from src.ui.onboarding_notice import (
    ONBOARDING_NOTICE_FOOTER,
    onboarding_notice_lines,
)
from src.ui.proportional_log import (
    render_proportional_help_texture,
    render_proportional_log_texture,
    render_proportional_overlay_texture,
)
from src.ui.tutorial_screen import TutorialScreenState, tutorial_page_lines
from src.ui.vore_prefs_onboarding import (
    VorePrefsOnboardingState,
    render_proportional_vore_prefs_texture,
)
from src.settings_store import SettingsStore

_main_console_render: tcod.render.SDLConsoleRender | None = None


def clear_renderer(
    renderer: tcod.sdl.render.Renderer,
    clear_color: tuple[int, int, int],
) -> None:
    """Clear the SDL render target using the tcod 21+ draw_color API."""
    renderer.draw_color = (*clear_color, 255)
    renderer.clear()


def compute_console_viewport(
    output_size: tuple[int, int],
    console: tcod.console.Console,
    layout: UILayout,
    *,
    integer_scaling: bool,
    align: tuple[float, float],
) -> tuple[int, int, int, int, int]:
    """Return scale, dest_x, dest_y, dest_w, dest_h for integer-scaled console blit."""
    out_w, out_h = output_size
    cell = layout.tile_px * layout.tile_scale
    base_w = console.width * cell
    base_h = console.height * cell
    if integer_scaling:
        scale = min(out_w // base_w, out_h // base_h)
        scale = max(1, scale)
    else:
        scale = 1
    dest_w = base_w * scale
    dest_h = base_h * scale
    dest_x = int((out_w - dest_w) * align[0])
    dest_y = int((out_h - dest_h) * align[1])
    return scale, dest_x, dest_y, dest_w, dest_h


def log_region_dest_rect(
    log_rect: RegionRect,
    *,
    layout: UILayout,
    scale: int,
    dest_x: int,
    dest_y: int,
) -> tuple[float, float, float, float]:
    """Pixel destination rect for the message log panel."""
    cell = layout.tile_px * layout.tile_scale
    return (
        float(dest_x + log_rect.x * cell * scale),
        float(dest_y + log_rect.y * cell * scale),
        float(log_rect.w * cell * scale),
        float(log_rect.h * cell * scale),
    )


def present_play_with_proportional_log(
    context: tcod.context.Context,
    console: tcod.console.Console,
    *,
    layout: UILayout,
    log_entries: list[LogEntry],
    log_font: LogFontState,
    max_lines: int,
    haze_alpha: int = 0,
    integer_scaling: bool = True,
    align: tuple[float, float] = (0, 0),
    clear_color: tuple[int, int, int] = (0, 0, 0),
) -> None:
    """Present CP437 chrome and composite a proportional TTF message log."""
    present_with_dialog_overlay(
        context,
        console,
        layout=layout,
        dialog_img=None,
        log_font=log_font,
        log_entries=log_entries,
        max_lines=max_lines,
        haze_alpha=haze_alpha,
        integer_scaling=integer_scaling,
        align=align,
        clear_color=clear_color,
    )


def present_help_overlay_frame(
    context: tcod.context.Context,
    console: tcod.console.Console,
    *,
    layout: UILayout,
    log_font: LogFontState | None = None,
    integer_scaling: bool = True,
    align: tuple[float, float] = (0, 0),
    clear_color: tuple[int, int, int] = (0, 0, 0),
) -> None:
    """Present the full-screen help overlay."""
    use_proportional = log_font is not None and log_font.enabled and log_font.font is not None
    renderer = context.sdl_renderer
    if use_proportional and renderer is not None:
        scale, dest_x, dest_y, dest_w, dest_h = compute_console_viewport(
            renderer.output_size,
            console,
            layout,
            integer_scaling=integer_scaling,
            align=align,
        )
        clear_renderer(renderer, clear_color)
        help_tex = render_proportional_help_texture(
            renderer,
            help_display_lines(),
            font=log_font.font,
            layout=layout,
            footer_text=HELP_OVERLAY_FOOTER,
            footer_fg=HELP_FOOTER_FG,
        )
        renderer.copy(help_tex, dest=(dest_x, dest_y, dest_w, dest_h))
        renderer.present()
        return

    context.present(
        console,
        integer_scaling=integer_scaling,
        align=align,
        clear_color=clear_color,
    )


def _present_help_style_frame(
    context: tcod.context.Context,
    console: tcod.console.Console,
    *,
    layout: UILayout,
    lines: tuple,
    footer_text: str,
    log_font: LogFontState | None,
    integer_scaling: bool,
    align: tuple[float, float],
    clear_color: tuple[int, int, int],
) -> None:
    use_proportional = log_font is not None and log_font.enabled and log_font.font is not None
    renderer = context.sdl_renderer
    if use_proportional and renderer is not None:
        scale, dest_x, dest_y, dest_w, dest_h = compute_console_viewport(
            renderer.output_size,
            console,
            layout,
            integer_scaling=integer_scaling,
            align=align,
        )
        clear_renderer(renderer, clear_color)
        tex = render_proportional_help_texture(
            renderer,
            lines,
            font=log_font.font,
            layout=layout,
            footer_text=footer_text,
            footer_fg=HELP_FOOTER_FG,
        )
        renderer.copy(tex, dest=(dest_x, dest_y, dest_w, dest_h))
        renderer.present()
        return
    context.present(
        console,
        integer_scaling=integer_scaling,
        align=align,
        clear_color=clear_color,
    )


def present_tutorial_prompt_frame(
    context: tcod.context.Context,
    console: tcod.console.Console,
    *,
    layout: UILayout,
    prompt_state: TutorialPromptState,
    log_font: LogFontState | None = None,
    integer_scaling: bool = True,
    align: tuple[float, float] = (0, 0),
    clear_color: tuple[int, int, int] = (0, 0, 0),
) -> None:
    """Present the first-run tutorial prompt."""
    use_proportional = log_font is not None and log_font.enabled and log_font.font is not None
    renderer = context.sdl_renderer
    if use_proportional and renderer is not None:
        scale, dest_x, dest_y, dest_w, dest_h = compute_console_viewport(
            renderer.output_size,
            console,
            layout,
            integer_scaling=integer_scaling,
            align=align,
        )
        clear_renderer(renderer, clear_color)
        prompt_tex = render_proportional_tutorial_prompt_texture(
            renderer,
            prompt_state,
            font=log_font.font,
            layout=layout,
        )
        renderer.copy(prompt_tex, dest=(dest_x, dest_y, dest_w, dest_h))
        renderer.present()
        return
    context.present(
        console,
        integer_scaling=integer_scaling,
        align=align,
        clear_color=clear_color,
    )


def present_tutorial_page_frame(
    context: tcod.context.Context,
    console: tcod.console.Console,
    *,
    layout: UILayout,
    state: TutorialScreenState,
    log_font: LogFontState | None = None,
    integer_scaling: bool = True,
    align: tuple[float, float] = (0, 0),
    clear_color: tuple[int, int, int] = (0, 0, 0),
) -> None:
    """Present one paginated tutorial page."""
    _present_help_style_frame(
        context,
        console,
        layout=layout,
        lines=tutorial_page_lines(state.page_index),
        footer_text=state.footer_text(),
        log_font=log_font,
        integer_scaling=integer_scaling,
        align=align,
        clear_color=clear_color,
    )


def present_onboarding_notice_frame(
    context: tcod.context.Context,
    console: tcod.console.Console,
    *,
    layout: UILayout,
    messages: tuple[str, ...],
    log_font: LogFontState | None = None,
    integer_scaling: bool = True,
    align: tuple[float, float] = (0, 0),
    clear_color: tuple[int, int, int] = (0, 0, 0),
) -> None:
    """Present a full-screen onboarding notice."""
    _present_help_style_frame(
        context,
        console,
        layout=layout,
        lines=onboarding_notice_lines(messages),
        footer_text=ONBOARDING_NOTICE_FOOTER,
        log_font=log_font,
        integer_scaling=integer_scaling,
        align=align,
        clear_color=clear_color,
    )


def present_vore_prefs_onboarding_frame(
    context: tcod.context.Context,
    console: tcod.console.Console,
    *,
    layout: UILayout,
    state: VorePrefsOnboardingState,
    settings: SettingsStore,
    log_font: LogFontState | None = None,
    integer_scaling: bool = True,
    align: tuple[float, float] = (0, 0),
    clear_color: tuple[int, int, int] = (0, 0, 0),
) -> None:
    """Present the first-run vore preferences screen."""
    use_proportional = log_font is not None and log_font.enabled and log_font.font is not None
    renderer = context.sdl_renderer
    if use_proportional and renderer is not None:
        scale, dest_x, dest_y, dest_w, dest_h = compute_console_viewport(
            renderer.output_size,
            console,
            layout,
            integer_scaling=integer_scaling,
            align=align,
        )
        clear_renderer(renderer, clear_color)
        tex = render_proportional_vore_prefs_texture(
            renderer,
            state,
            settings=settings,
            font=log_font.font,
            layout=layout,
        )
        renderer.copy(tex, dest=(dest_x, dest_y, dest_w, dest_h))
        renderer.present()
        return
    context.present(
        console,
        integer_scaling=integer_scaling,
        align=align,
        clear_color=clear_color,
    )


def present_credits_frame(
    context: tcod.context.Context,
    console: tcod.console.Console,
    *,
    layout: UILayout,
    log_font: LogFontState | None = None,
    integer_scaling: bool = True,
    align: tuple[float, float] = (0, 0),
    clear_color: tuple[int, int, int] = (0, 0, 0),
) -> None:
    """Present the full-screen credits page."""
    use_proportional = log_font is not None and log_font.enabled and log_font.font is not None
    renderer = context.sdl_renderer
    if use_proportional and renderer is not None:
        scale, dest_x, dest_y, dest_w, dest_h = compute_console_viewport(
            renderer.output_size,
            console,
            layout,
            integer_scaling=integer_scaling,
            align=align,
        )
        clear_renderer(renderer, clear_color)
        credits_tex = render_proportional_help_texture(
            renderer,
            credits_display_lines(),
            font=log_font.font,
            layout=layout,
            footer_text=HELP_OVERLAY_FOOTER,
            footer_fg=HELP_FOOTER_FG,
        )
        renderer.copy(credits_tex, dest=(dest_x, dest_y, dest_w, dest_h))
        renderer.present()
        return

    context.present(
        console,
        integer_scaling=integer_scaling,
        align=align,
        clear_color=clear_color,
    )


def present_downtime_frame(
    context: tcod.context.Context,
    console: tcod.console.Console,
    *,
    layout: UILayout,
    lines: tuple,
    footer_text: str,
    log_font: LogFontState | None = None,
    dialog_img: object | None = None,
    integer_scaling: bool = True,
    align: tuple[float, float] = (0, 0),
    clear_color: tuple[int, int, int] = (0, 0, 0),
) -> None:
    """Present the downtime hub with the proportional log font when available."""
    use_proportional = log_font is not None and log_font.enabled and log_font.font is not None
    renderer = context.sdl_renderer
    if use_proportional and renderer is not None:
        import numpy as np

        scale, dest_x, dest_y, dest_w, dest_h = compute_console_viewport(
            renderer.output_size,
            console,
            layout,
            integer_scaling=integer_scaling,
            align=align,
        )
        clear_renderer(renderer, clear_color)
        hub_tex = render_proportional_help_texture(
            renderer,
            lines,
            font=log_font.font,
            layout=layout,
            footer_text=footer_text,
            footer_fg=HELP_FOOTER_FG,
        )
        renderer.copy(hub_tex, dest=(dest_x, dest_y, dest_w, dest_h))
        if dialog_img is not None:
            dialog_tex = renderer.upload_texture(np.asarray(dialog_img, dtype=np.uint8))
            try:
                dialog_tex.blend_mode = tcod.sdl.render.BlendMode.BLEND
            except (AttributeError, TypeError):
                pass
            dw, dh = dialog_img.size  # type: ignore[attr-defined]
            dest = _dialog_dest_rect(
                dest_x=dest_x,
                dest_y=dest_y,
                dest_w=dest_w,
                dest_h=dest_h,
                dialog_w=dw,
                dialog_h=dh,
                scale=scale,
                band="center",
            )
            renderer.copy(dialog_tex, dest=dest)
        renderer.present()
        return

    # Fallback: CP437 already drawn on console in App.render.
    if dialog_img is not None:
        present_with_dialog_overlay(
            context,
            console,
            layout=layout,
            dialog_img=dialog_img,
            integer_scaling=integer_scaling,
            align=align,
            clear_color=clear_color,
        )
        return
    context.present(
        console,
        integer_scaling=integer_scaling,
        align=align,
        clear_color=clear_color,
    )


def _draw_help_lines_on_image(
    draw: object,
    lines: tuple,
    *,
    font: object,
    panel_w: int,
    panel_h: int,
    pad_x: int,
    pad_y: int,
    row_h: int,
    blank_advance: float,
    max_y: float | None = None,
) -> None:
    """Draw HelpTextLine-like entries into a PIL Draw context."""
    y = float(pad_y)
    limit = float(panel_h - pad_y) if max_y is None else max_y
    for entry in lines:
        if y + row_h > limit:
            break
        text = getattr(entry, "text", "") or ""
        if not text:
            y += blank_advance
            continue
        fg = getattr(entry, "fg", (220, 220, 220))
        draw.text(  # type: ignore[attr-defined]
            (float(pad_x), y),
            text,
            font=font,
            fill=(*fg, 255),
        )
        y += row_h


def present_match_frame(
    context: tcod.context.Context,
    console: tcod.console.Console,
    *,
    layout: UILayout,
    session: object,
    log_font: LogFontState | None = None,
    dialog_img: object | None = None,
    integer_scaling: bool = True,
    align: tuple[float, float] = (0, 0),
    clear_color: tuple[int, int, int] = (0, 0, 0),
) -> None:
    """Match present: tile map/glyphs only; all other text uses the log font.

    Fight layout: status right of map, action log bottom, reaction modal low-right.
    *session* is a ``MatchSession`` (typed loosely to avoid import cycles).
    """
    from src.match_hud_layout import match_hud_bands, region_pixel_size
    from src.match_session import (
        AbilityUiMode,
        MatchPhase,
        match_footer_text,
        match_fullscreen_text_lines,
        match_log_lines,
        match_low_right_crisis_lines,
        match_status_lines,
        match_swallow_narrative_text,
        match_swallow_options_line,
        render_match_cp437_fallback,
    )
    from src.systems.render import MESSAGE_LOG_BACKGROUND
    from src.ui.proportional_log import (
        LOG_HORIZONTAL_PADDING_PX,
        LOG_VERTICAL_PADDING_PX,
        line_height_px,
        measure_text,
        overlay_panel_pixel_size,
    )

    use_proportional = log_font is not None and log_font.enabled and log_font.font is not None
    renderer = context.sdl_renderer
    phase = session.phase
    ability_ui = session.ability_ui
    text_only = phase is MatchPhase.RECAP or ability_ui is AbilityUiMode.FULL_LIST

    if not use_proportional or renderer is None:
        render_match_cp437_fallback(console, session)
        if dialog_img is not None:
            present_with_dialog_overlay(
                context,
                console,
                layout=layout,
                dialog_img=dialog_img,
                integer_scaling=integer_scaling,
                align=align,
                clear_color=clear_color,
            )
        else:
            context.present(
                console,
                integer_scaling=integer_scaling,
                align=align,
                clear_color=clear_color,
            )
        return

    import numpy as np
    from PIL import Image, ImageDraw

    global _main_console_render

    scale, dest_x, dest_y, dest_w, dest_h = compute_console_viewport(
        renderer.output_size,
        console,
        layout,
        integer_scaling=integer_scaling,
        align=align,
    )
    clear_renderer(renderer, clear_color)
    footer = match_footer_text(session)
    font = log_font.font
    row_h = line_height_px(font)
    blank_advance = row_h * 0.45
    pad_x = LOG_HORIZONTAL_PADDING_PX
    pad_y = LOG_VERTICAL_PADDING_PX
    panel_w, panel_h = overlay_panel_pixel_size(layout)
    crisis_bg = (48, 28, 32)
    crisis_border = (220, 100, 90)

    if text_only:
        lines = match_fullscreen_text_lines(session)
        hub_tex = render_proportional_help_texture(
            renderer,
            lines,
            font=font,
            layout=layout,
            footer_text=footer,
            footer_fg=HELP_FOOTER_FG,
        )
        renderer.copy(hub_tex, dest=(dest_x, dest_y, dest_w, dest_h))
    else:
        # Fight: tile map top-left; regional log-font chrome (status / log / crisis).
        main_atlas = context.sdl_atlas
        if main_atlas is not None:
            if _main_console_render is None or _main_console_render.atlas is not main_atlas:
                _main_console_render = tcod.render.SDLConsoleRender(main_atlas)
            main_tex = _main_console_render.render(console)
            renderer.copy(main_tex, dest=(dest_x, dest_y, dest_w, dest_h))

        swallow_narrative = match_swallow_narrative_text(session)
        if swallow_narrative is not None:
            # Centered modal (prior size) over dimmed fight; narrative top of modal,
            # options bottom — not full-screen fill.
            from src.ui.proportional_log import wrap_log_text_pixels

            cell_px = layout.tile_px * layout.tile_scale
            # Dim the arena under the modal
            dim = Image.new("RGBA", (panel_w, panel_h), (0, 0, 0, 140))
            dim_tex = renderer.upload_texture(np.asarray(dim, dtype=np.uint8))
            try:
                dim_tex.blend_mode = tcod.sdl.render.BlendMode.BLEND
            except (AttributeError, TypeError):
                pass
            renderer.copy(dim_tex, dest=(dest_x, dest_y, dest_w, dest_h))

            modal_w = min(max(cell_px * 40, panel_w * 2 // 3), panel_w - 2 * pad_x)
            # Compact height: top pad + ~3 narrative lines + options + secondary
            modal_h = min(
                panel_h - 2 * pad_y,
                int(row_h * 8 + pad_y * 4),
            )
            modal_h = max(modal_h, int(row_h * 6 + pad_y * 3))
            modal_img = Image.new("RGBA", (modal_w, modal_h), (*crisis_bg, 255))
            mdraw = ImageDraw.Draw(modal_img)
            mdraw.rectangle(
                [0, 0, modal_w - 1, modal_h - 1],
                outline=(*crisis_border, 255),
                width=max(2, cell_px // 6),
            )
            inner_pad_x = pad_x + 6
            top_pad = pad_y + 10  # keep narrative off the border
            max_text_w = max(1, modal_w - inner_pad_x * 2)
            wrapped = wrap_log_text_pixels(
                swallow_narrative, font=font, max_width_px=max_text_w
            )
            y = float(top_pad)
            for line in wrapped[:4]:
                tw = measure_text(font, line)
                mdraw.text(
                    (max(inner_pad_x, (modal_w - tw) / 2), y),
                    line,
                    font=font,
                    fill=(235, 210, 205, 255),
                )
                y += row_h
            options = match_swallow_options_line()
            ow = measure_text(font, options)
            opt_y = modal_h - row_h - pad_y - 6
            mdraw.text(
                (max(inner_pad_x, (modal_w - ow) / 2), opt_y),
                options,
                font=font,
                fill=(*HELP_FOOTER_FG, 255),
            )
            modal_tex = renderer.upload_texture(np.asarray(modal_img, dtype=np.uint8))
            try:
                modal_tex.blend_mode = tcod.sdl.render.BlendMode.BLEND
            except (AttributeError, TypeError):
                pass
            mx = dest_x + int((dest_w - modal_w * scale) / 2)
            my = dest_y + int((dest_h - modal_h * scale) / 2)
            renderer.copy(
                modal_tex,
                dest=(mx, my, modal_w * scale, modal_h * scale),
            )
        else:
            crisis_lines = match_low_right_crisis_lines(session)
            bands = match_hud_bands(
                map_w=int(session.game_map.width),
                map_h=int(session.game_map.height),
                root_w=console.width,
                root_h=console.height,
                reaction_active=crisis_lines is not None,
            )
            composed = Image.new("RGBA", (panel_w, panel_h), (0, 0, 0, 0))
            cell = layout.tile_px * layout.tile_scale

            def _paste_band(
                region: object,
                lines: tuple,
                *,
                bg: tuple[int, int, int],
                border: tuple[int, int, int] | None = None,
            ) -> None:
                nonlocal composed
                from src.ui.layout import RegionRect

                assert isinstance(region, RegionRect)
                bw, bh = region_pixel_size(region, layout=layout)
                if bw < 1 or bh < 1:
                    return
                band_img = Image.new("RGBA", (bw, bh), (*bg, 255))
                draw = ImageDraw.Draw(band_img)
                if border is not None:
                    draw.rectangle(
                        [0, 0, bw - 1, bh - 1],
                        outline=(*border, 255),
                        width=max(1, cell // 8),
                    )
                _draw_help_lines_on_image(
                    draw,
                    lines,
                    font=font,
                    panel_w=bw,
                    panel_h=bh,
                    pad_x=pad_x,
                    pad_y=pad_y,
                    row_h=row_h,
                    blank_advance=blank_advance,
                )
                px = region.x * cell
                py = region.y * cell
                composed.paste(band_img, (px, py))

            # Status — right of map
            _paste_band(bands.status, match_status_lines(session), bg=MESSAGE_LOG_BACKGROUND)
            # Action log — bottom
            _paste_band(bands.log, match_log_lines(session), bg=MESSAGE_LOG_BACKGROUND)
            # Reaction / grapple crisis modal — low-right
            if crisis_lines is not None and bands.reaction is not None:
                _paste_band(
                    bands.reaction,
                    crisis_lines,
                    bg=crisis_bg,
                    border=crisis_border,
                )

            # Footer keys along bottom edge
            footer_layer = Image.new("RGBA", (panel_w, panel_h), (0, 0, 0, 0))
            fdraw = ImageDraw.Draw(footer_layer)
            footer_y = panel_h - row_h - LOG_VERTICAL_PADDING_PX
            fdraw.rectangle(
                [0, footer_y - 2, panel_w, panel_h],
                fill=(*MESSAGE_LOG_BACKGROUND, 230),
            )
            footer_w = measure_text(font, footer)
            footer_x = max(pad_x, (panel_w - footer_w) / 2)
            fdraw.text(
                (footer_x, footer_y),
                footer,
                font=font,
                fill=(*HELP_FOOTER_FG, 255),
            )
            composed = Image.alpha_composite(composed, footer_layer)

            hud_tex = renderer.upload_texture(np.asarray(composed, dtype=np.uint8))
            try:
                hud_tex.blend_mode = tcod.sdl.render.BlendMode.BLEND
            except (AttributeError, TypeError):
                pass
            renderer.copy(hud_tex, dest=(dest_x, dest_y, dest_w, dest_h))

    if dialog_img is not None:
        dialog_tex = renderer.upload_texture(np.asarray(dialog_img, dtype=np.uint8))
        try:
            dialog_tex.blend_mode = tcod.sdl.render.BlendMode.BLEND
        except (AttributeError, TypeError):
            pass
        dw, dh = dialog_img.size  # type: ignore[attr-defined]
        dest = _dialog_dest_rect(
            dest_x=dest_x,
            dest_y=dest_y,
            dest_w=dest_w,
            dest_h=dest_h,
            dialog_w=dw,
            dialog_h=dh,
            scale=scale,
            band="center",
        )
        renderer.copy(dialog_tex, dest=dest)
    renderer.present()


def present_log_overlay_frame(
    context: tcod.context.Context,
    console: tcod.console.Console,
    *,
    layout: UILayout,
    log_entries: list[LogEntry],
    log_overlay: LogOverlayState,
    log_font: LogFontState | None = None,
    viewport_lines: int,
    integer_scaling: bool = True,
    align: tuple[float, float] = (0, 0),
    clear_color: tuple[int, int, int] = (0, 0, 0),
) -> None:
    """Present the full-screen log overlay."""
    use_proportional = log_font is not None and log_font.enabled and log_font.font is not None
    renderer = context.sdl_renderer
    if use_proportional and renderer is not None:
        scale, dest_x, dest_y, dest_w, dest_h = compute_console_viewport(
            renderer.output_size,
            console,
            layout,
            integer_scaling=integer_scaling,
            align=align,
        )
        clear_renderer(renderer, clear_color)
        log_tex = render_proportional_overlay_texture(
            renderer,
            log_entries,
            font=log_font.font,
            layout=layout,
            scroll_offset=log_overlay.scroll_offset,
            viewport_lines=viewport_lines,
            footer_text=LOG_OVERLAY_FOOTER,
            footer_fg=LOG_OVERLAY_FOOTER_FG,
        )
        renderer.copy(log_tex, dest=(dest_x, dest_y, dest_w, dest_h))
        renderer.present()
        return

    context.present(
        console,
        integer_scaling=integer_scaling,
        align=align,
        clear_color=clear_color,
    )


# Full veil under digestion completion / game over (and at max digestion strikes).
SCREEN_HAZE_MAX_ALPHA = 150
# Progressive darkening while stunned at 0 HP and digestion strikes accumulate.
DIGESTION_HAZE_MAX_STRIKES = 5


def digestion_haze_alpha(strike_count: int) -> int:
    """Alpha 0..SCREEN_HAZE_MAX_ALPHA from digestion strikes (caps at 5)."""
    if strike_count <= 0:
        return 0
    t = min(int(strike_count), DIGESTION_HAZE_MAX_STRIKES) / DIGESTION_HAZE_MAX_STRIKES
    return int(round(SCREEN_HAZE_MAX_ALPHA * t))


def _dialog_dest_rect(
    *,
    dest_x: int,
    dest_y: int,
    dest_w: int,
    dest_h: int,
    dialog_w: int,
    dialog_h: int,
    scale: int,
    band: str = "center",
) -> tuple[int, int, int, int]:
    dest_dw = dialog_w * scale
    dest_dh = dialog_h * scale
    dx = dest_x + (dest_w - dest_dw) // 2
    if band == "lower":
        # Match menu lower-band feel (below title logo).
        dy = dest_y + (dest_h - dest_dh) // 2 + dest_h // 8
        max_dy = dest_y + dest_h - dest_dh - max(4 * scale, 4)
        dy = min(dy, max_dy)
        dy = max(dest_y, dy)
    else:
        dy = dest_y + (dest_h - dest_dh) // 2
    return dx, dy, dest_dw, dest_dh


def _copy_screen_haze(
    renderer: tcod.sdl.render.Renderer,
    *,
    dest_x: int,
    dest_y: int,
    dest_w: int,
    dest_h: int,
    alpha: int,
) -> None:
    """Dim the full console viewport (map, sidebar, log)."""
    if alpha <= 0:
        return
    import numpy as np

    a = max(0, min(255, int(alpha)))
    haze = np.zeros((1, 1, 4), dtype=np.uint8)
    haze[0, 0] = (0, 0, 0, a)
    haze_tex = renderer.upload_texture(haze)
    try:
        haze_tex.blend_mode = tcod.sdl.render.BlendMode.BLEND
    except (AttributeError, TypeError):
        pass
    renderer.copy(haze_tex, dest=(dest_x, dest_y, dest_w, dest_h))


def present_with_dialog_overlay(
    context: tcod.context.Context,
    console: tcod.console.Console,
    *,
    layout: UILayout,
    dialog_img: object | None = None,
    log_font: LogFontState | None = None,
    log_entries: list[LogEntry] | None = None,
    max_lines: int = 0,
    band: str = "center",
    haze_alpha: int = 0,
    integer_scaling: bool = True,
    align: tuple[float, float] = (0, 0),
    clear_color: tuple[int, int, int] = (0, 0, 0),
) -> None:
    """Present console (+ optional log / haze / dialog image overlay)."""
    global _main_console_render

    renderer = context.sdl_renderer
    main_atlas = context.sdl_atlas
    if renderer is None or main_atlas is None:
        context.present(
            console,
            integer_scaling=integer_scaling,
            align=align,
            clear_color=clear_color,
        )
        return

    use_log = (
        log_font is not None
        and log_font.enabled
        and log_font.font is not None
        and log_entries is not None
        and max_lines > 0
    )
    if dialog_img is None and haze_alpha <= 0 and not use_log:
        context.present(
            console,
            integer_scaling=integer_scaling,
            align=align,
            clear_color=clear_color,
        )
        return

    import numpy as np

    if _main_console_render is None or _main_console_render.atlas is not main_atlas:
        _main_console_render = tcod.render.SDLConsoleRender(main_atlas)

    scale, dest_x, dest_y, dest_w, dest_h = compute_console_viewport(
        renderer.output_size,
        console,
        layout,
        integer_scaling=integer_scaling,
        align=align,
    )

    clear_renderer(renderer, clear_color)

    main_tex = _main_console_render.render(console)
    renderer.copy(main_tex, dest=(dest_x, dest_y, dest_w, dest_h))

    if use_log:
        log_tex = render_proportional_log_texture(
            renderer,
            log_entries,
            font=log_font.font,
            layout=layout,
            max_lines=max_lines,
        )
        log_dest = log_region_dest_rect(
            layout.region("message_log"),
            layout=layout,
            scale=scale,
            dest_x=dest_x,
            dest_y=dest_y,
        )
        renderer.copy(log_tex, dest=log_dest)

    if haze_alpha > 0:
        _copy_screen_haze(
            renderer,
            dest_x=dest_x,
            dest_y=dest_y,
            dest_w=dest_w,
            dest_h=dest_h,
            alpha=haze_alpha,
        )

    if dialog_img is not None:
        dialog_tex = renderer.upload_texture(np.asarray(dialog_img, dtype=np.uint8))
        try:
            dialog_tex.blend_mode = tcod.sdl.render.BlendMode.BLEND
        except (AttributeError, TypeError):
            pass
        dw, dh = dialog_img.size  # type: ignore[attr-defined]
        dest = _dialog_dest_rect(
            dest_x=dest_x,
            dest_y=dest_y,
            dest_w=dest_w,
            dest_h=dest_h,
            dialog_w=dw,
            dialog_h=dh,
            scale=scale,
            band=band,
        )
        renderer.copy(dialog_tex, dest=dest)
    renderer.present()


def present_play_with_dialog_overlay(
    context: tcod.context.Context,
    console: tcod.console.Console,
    *,
    layout: UILayout,
    log_entries: list[LogEntry],
    log_font: LogFontState,
    max_lines: int,
    dialog_img: object | None = None,
    band: str = "center",
    haze_alpha: int = 0,
    integer_scaling: bool = True,
    align: tuple[float, float] = (0, 0),
    clear_color: tuple[int, int, int] = (0, 0, 0),
) -> None:
    """Present play chrome + proportional log + optional dialog / haze."""
    if log_font.font is None or not log_font.enabled:
        context.present(
            console,
            integer_scaling=integer_scaling,
            align=align,
            clear_color=clear_color,
        )
        return
    present_with_dialog_overlay(
        context,
        console,
        layout=layout,
        dialog_img=dialog_img,
        log_font=log_font,
        log_entries=log_entries,
        max_lines=max_lines,
        band=band,
        haze_alpha=haze_alpha,
        integer_scaling=integer_scaling,
        align=align,
        clear_color=clear_color,
    )


def present_play_with_digestion_dialog(
    context: tcod.context.Context,
    console: tcod.console.Console,
    *,
    layout: UILayout,
    log_entries: list[LogEntry],
    log_font: LogFontState,
    max_lines: int,
    dialog_text: str,
    footer_text: str | None = None,
    haze_alpha: int = 0,
    integer_scaling: bool = True,
    align: tuple[float, float] = (0, 0),
    clear_color: tuple[int, int, int] = (0, 0, 0),
) -> None:
    """Present play chrome + proportional log + narrative dialog (digestion model).

    Used for digestion, vore, and examine description. Default footer is
    ``Press Enter``; pass another footer (e.g. ``Esc: close``) when needed.
    *haze_alpha*: dim the world under the panel (0–SCREEN_HAZE_MAX_ALPHA).
    """
    if log_font.font is None or not log_font.enabled:
        context.present(
            console,
            integer_scaling=integer_scaling,
            align=align,
            clear_color=clear_color,
        )
        return

    from src.ui.proportional_dialog import (
        DIGESTION_MODAL_FOOTER,
        dialog_font_from_log_font,
        render_proportional_dialog_image,
    )

    dialog_font = dialog_font_from_log_font(log_font)
    if dialog_font is None:
        context.present(
            console,
            integer_scaling=integer_scaling,
            align=align,
            clear_color=clear_color,
        )
        return

    dialog_img = render_proportional_dialog_image(
        dialog_text,
        font=dialog_font,
        layout=layout,
        console_w=console.width,
        console_h=console.height,
        footer_text=DIGESTION_MODAL_FOOTER if footer_text is None else footer_text,
    )
    present_play_with_dialog_overlay(
        context,
        console,
        layout=layout,
        log_entries=log_entries,
        log_font=log_font,
        max_lines=max_lines,
        dialog_img=dialog_img,
        haze_alpha=haze_alpha,
        integer_scaling=integer_scaling,
        align=align,
        clear_color=clear_color,
    )


def present_frame(
    context: tcod.context.Context,
    console: tcod.console.Console,
    *,
    layout: UILayout | None = None,
    log_entries: list[LogEntry] | None = None,
    log_font: LogFontState | None = None,
    max_lines: int = 0,
    haze_alpha: int = 0,
    integer_scaling: bool = True,
    align: tuple[float, float] = (0, 0),
    clear_color: tuple[int, int, int] = (0, 0, 0),
) -> None:
    """Present a frame, compositing the proportional log when enabled."""
    use_proportional_log = (
        log_font is not None
        and log_font.enabled
        and layout is not None
        and log_entries is not None
        and max_lines > 0
    )
    if use_proportional_log:
        present_play_with_proportional_log(
            context,
            console,
            layout=layout,
            log_entries=log_entries,
            log_font=log_font,
            max_lines=max_lines,
            haze_alpha=haze_alpha,
            integer_scaling=integer_scaling,
            align=align,
            clear_color=clear_color,
        )
        return
    if haze_alpha > 0 and layout is not None:
        present_with_dialog_overlay(
            context,
            console,
            layout=layout,
            dialog_img=None,
            haze_alpha=haze_alpha,
            integer_scaling=integer_scaling,
            align=align,
            clear_color=clear_color,
        )
        return

    context.present(
        console,
        integer_scaling=integer_scaling,
        align=align,
        clear_color=clear_color,
    )