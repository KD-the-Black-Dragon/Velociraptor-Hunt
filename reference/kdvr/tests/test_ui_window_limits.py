"""Window client-area floor enforcement."""

from __future__ import annotations

import attrs

from src.ui.dynamic_layout import (
    DESIGN_PIXEL_HEIGHT,
    DESIGN_PIXEL_WIDTH,
    minimum_window_pixels,
)
from src.ui.layout import load_ui_layout
from src.ui.window_limits import enforce_minimum_window_size


class _FakeWindow:
    def __init__(self, width: int, height: int) -> None:
        self._size = (width, height)
        self.min_size = (0, 0)

    @property
    def size(self) -> tuple[int, int]:
        return self._size

    @size.setter
    def size(self, xy: tuple[int, int]) -> None:
        min_w, min_h = self.min_size
        self._size = (max(min_w, xy[0]), max(min_h, xy[1]))


class _FakeContext:
    def __init__(self, window: _FakeWindow | None) -> None:
        self.sdl_window = window


def test_enforce_minimum_window_size_clamps_requested_pixels() -> None:
    layout = load_ui_layout()
    window = _FakeWindow(1920, 1008)
    context = _FakeContext(window)

    clamped_w, clamped_h = enforce_minimum_window_size(
        context,
        layout,
        requested_w=800,
        requested_h=600,
    )

    assert clamped_w == DESIGN_PIXEL_WIDTH
    assert clamped_h == DESIGN_PIXEL_HEIGHT
    assert window.min_size == (DESIGN_PIXEL_WIDTH, DESIGN_PIXEL_HEIGHT)
    assert window.size == (DESIGN_PIXEL_WIDTH, DESIGN_PIXEL_HEIGHT)


def test_enforce_minimum_window_size_without_window_returns_clamped_values() -> None:
    layout = load_ui_layout()
    context = _FakeContext(None)

    clamped_w, clamped_h = enforce_minimum_window_size(
        context,
        layout,
        requested_w=640,
        requested_h=480,
    )

    assert clamped_w == DESIGN_PIXEL_WIDTH
    assert clamped_h == DESIGN_PIXEL_HEIGHT


def test_enforce_minimum_grows_window_for_four_k_tile_scale() -> None:
    """4K effective scale raises the pixel floor; small windows must grow to match."""
    layout = attrs.evolve(load_ui_layout(), tile_scale=4)
    min_w, min_h = minimum_window_pixels(layout)
    assert min_w == DESIGN_PIXEL_WIDTH * 2
    assert min_h == DESIGN_PIXEL_HEIGHT * 2

    window = _FakeWindow(1920, 1080)
    context = _FakeContext(window)
    out_w, out_h = enforce_minimum_window_size(context, layout)
    assert (out_w, out_h) == (min_w, min_h)
    assert window.size == (min_w, min_h)
    cell = layout.tile_px * layout.tile_scale
    assert (out_w // cell) * cell <= out_w
    assert (out_h // cell) * cell <= out_h
