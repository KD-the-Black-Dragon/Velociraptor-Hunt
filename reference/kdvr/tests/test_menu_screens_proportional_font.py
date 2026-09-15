"""Options / Mods / Past Runs use the readable proportional font when available."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import tcod.console

from src.options_menu import OptionsMenuState
from src.mods.menu import ModsMenuState
from src.settings_store import SettingsStore
from src.ui.layout import load_ui_layout
from src.ui.log_font import LogFontState, load_log_font_state
from src.ui.log_present import (
    present_mods_frame,
    present_options_frame,
    present_past_runs_frame,
)
from src.ui.past_runs_screen import PastRunsScreenState


def _make_context(*, sdl_renderer: object | None) -> MagicMock:
    context = MagicMock()
    context.sdl_renderer = sdl_renderer
    return context


def _layout_console_font():
    layout = load_ui_layout()
    console = tcod.console.Console(layout.root_cols, layout.root_rows, order="F")
    log_font = load_log_font_state(tile_px=layout.tile_px, tile_scale=layout.tile_scale)
    return layout, console, log_font


def test_present_options_uses_proportional_when_font_enabled() -> None:
    layout, console, log_font = _layout_console_font()
    if not log_font.enabled:
        return
    renderer = MagicMock()
    renderer.output_size = (layout.root_cols * 24, layout.root_rows * 24)
    context = _make_context(sdl_renderer=renderer)
    with patch(
        "src.ui.log_present.render_proportional_options_texture",
        return_value=MagicMock(),
    ) as mock_render:
        with patch("src.ui.log_present.clear_renderer"):
            present_options_frame(
                context,
                console,
                layout=layout,
                options=OptionsMenuState(),
                settings=SettingsStore.load(),
                log_font=log_font,
            )
    mock_render.assert_called_once()
    context.present.assert_not_called()


def test_present_mods_uses_proportional_when_font_enabled() -> None:
    layout, console, log_font = _layout_console_font()
    if not log_font.enabled:
        return
    renderer = MagicMock()
    renderer.output_size = (layout.root_cols * 24, layout.root_rows * 24)
    context = _make_context(sdl_renderer=renderer)
    with patch(
        "src.ui.log_present.render_proportional_mods_texture",
        return_value=MagicMock(),
    ) as mock_render:
        with patch("src.ui.log_present.clear_renderer"):
            present_mods_frame(
                context,
                console,
                layout=layout,
                mods_menu=ModsMenuState(),
                log_font=log_font,
            )
    mock_render.assert_called_once()
    context.present.assert_not_called()


def test_present_past_runs_uses_proportional_when_font_enabled() -> None:
    layout, console, log_font = _layout_console_font()
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
            present_past_runs_frame(
                context,
                console,
                layout=layout,
                records=[],
                past_runs_screen=PastRunsScreenState(),
                log_font=log_font,
            )
    mock_render.assert_called_once()
    context.present.assert_not_called()


def test_present_options_falls_back_without_font() -> None:
    layout, console, _ = _layout_console_font()
    context = _make_context(sdl_renderer=MagicMock())
    with patch("src.ui.log_present.render_proportional_options_texture") as mock_render:
        present_options_frame(
            context,
            console,
            layout=layout,
            options=OptionsMenuState(),
            settings=SettingsStore.load(),
            log_font=LogFontState(enabled=False),
        )
    mock_render.assert_not_called()
    context.present.assert_called_once()
