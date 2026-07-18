"""Live client pixel reads for layout/console sizing."""

from __future__ import annotations

from unittest.mock import MagicMock

import tcod.context

from src.ui.layout import load_ui_layout
from src.ui.window_limits import client_pixels_from_context


def test_client_pixels_from_context_reads_live_window_size() -> None:
    layout = load_ui_layout("standard")
    context = MagicMock(spec=tcod.context.Context)
    window = MagicMock()
    window.size = (1920, 1080)
    context.sdl_window = window

    assert client_pixels_from_context(context, layout) == (1920, 1080)