"""Window sizing helpers for first launch and preference clamping."""

from __future__ import annotations

from unittest.mock import patch

from src.ui.dynamic_layout import DESIGN_PIXEL_HEIGHT, DESIGN_PIXEL_WIDTH
from src.ui.layout import load_ui_layout
from src.ui.window_state import (
    DISPLAY_INSET_PX,
    WindowPreferences,
    centered_position,
    clamp_window_preferences,
    default_first_launch_client_size,
    window_from_dict,
    window_to_dict,
)


def test_default_first_launch_client_size_uses_display_inset() -> None:
    layout = load_ui_layout("standard")
    with patch("src.ui.window_state.primary_desktop_pixel_size", return_value=(1920, 1080)):
        width, height = default_first_launch_client_size(layout)
    assert width == 1920 - DISPLAY_INSET_PX * 2
    assert height == 1080 - DISPLAY_INSET_PX * 2


def test_default_first_launch_client_size_clamps_to_minimum() -> None:
    layout = load_ui_layout("standard")
    with patch("src.ui.window_state.primary_desktop_pixel_size", return_value=(1366, 768)):
        width, height = default_first_launch_client_size(layout)
    assert width == DESIGN_PIXEL_WIDTH
    assert height == DESIGN_PIXEL_HEIGHT


def test_centered_position() -> None:
    with patch("src.ui.window_state.primary_desktop_pixel_size", return_value=(1920, 1080)):
        x, y = centered_position(1600, 900)
    assert x == (1920 - 1600) // 2
    assert y == (1080 - 900) // 2


def test_window_from_dict_clamps_small_sizes() -> None:
    layout = load_ui_layout("standard")
    prefs = window_from_dict(
        {
            "client_width": 800,
            "client_height": 600,
            "x": 10,
            "y": 20,
            "maximized": True,
            "fullscreen": False,
        },
        layout,
    )
    assert prefs.client_width == DESIGN_PIXEL_WIDTH
    assert prefs.client_height == DESIGN_PIXEL_HEIGHT
    assert prefs.x == 10
    assert prefs.y == 20
    assert prefs.maximized is True


def test_window_round_trip_dict() -> None:
    prefs = WindowPreferences(
        client_width=1600,
        client_height=900,
        x=40,
        y=50,
        maximized=True,
        fullscreen=False,
    )
    restored = window_from_dict(window_to_dict(prefs), load_ui_layout("standard"))
    assert restored == clamp_window_preferences(load_ui_layout("standard"), prefs)