"""PR2: present_credits_frame proportional vs CP437 branch guards."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import tcod.console

from src.ui.layout import load_ui_layout
from src.ui.log_font import LogFontState, load_log_font_state
from src.ui.log_present import present_credits_frame


def _make_context(*, sdl_renderer: object | None) -> MagicMock:
    context = MagicMock()
    context.sdl_renderer = sdl_renderer
    return context


def test_present_credits_uses_proportional_when_font_enabled() -> None:
    layout = load_ui_layout()
    console = tcod.console.Console(layout.root_cols, layout.root_rows, order="F")
    log_font = load_log_font_state(tile_px=layout.tile_px, tile_scale=layout.tile_scale)
    if not log_font.enabled:
        return

    renderer = MagicMock()
    renderer.output_size = (layout.root_cols * 24, layout.root_rows * 24)
    context = _make_context(sdl_renderer=renderer)

    with patch(
        "src.ui.log_present.render_proportional_help_texture",
        return_value=MagicMock(),
    ) as mock_render:
        with patch("src.ui.log_present.clear_renderer"):
            present_credits_frame(
                context,
                console,
                layout=layout,
                log_font=log_font,
            )

    mock_render.assert_called_once()
    renderer.present.assert_called_once()
    context.present.assert_not_called()


def test_present_credits_falls_back_to_context_present_without_font() -> None:
    layout = load_ui_layout()
    console = tcod.console.Console(layout.root_cols, layout.root_rows, order="F")
    context = _make_context(sdl_renderer=MagicMock())

    with patch(
        "src.ui.log_present.render_proportional_help_texture",
    ) as mock_render:
        present_credits_frame(
            context,
            console,
            layout=layout,
            log_font=LogFontState(enabled=False),
        )

    mock_render.assert_not_called()
    context.present.assert_called_once()


def test_present_credits_falls_back_when_renderer_missing() -> None:
    layout = load_ui_layout()
    console = tcod.console.Console(layout.root_cols, layout.root_rows, order="F")
    log_font = load_log_font_state(tile_px=layout.tile_px, tile_scale=layout.tile_scale)
    context = _make_context(sdl_renderer=None)

    with patch(
        "src.ui.log_present.render_proportional_help_texture",
    ) as mock_render:
        present_credits_frame(
            context,
            console,
            layout=layout,
            log_font=log_font,
        )

    mock_render.assert_not_called()
    context.present.assert_called_once()