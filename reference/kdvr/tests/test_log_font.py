"""PR4: proportional TTF font for the message log region."""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest

from src.ui.log_font import LOG_FONT_PATH, load_log_font_state, reset_log_font_warnings
from src.ui.log_present import compute_console_viewport, log_region_dest_rect
from src.ui.proportional_log import (
    load_proportional_font,
    measure_text,
    proportional_font_size_px,
    proportional_lines_fit_in_panel,
    wrap_log_segments_pixels,
    wrap_log_text_pixels,
)
from tests.ui_test_helpers import default_layout, make_console, message_log_text, render_engine_frame


def test_bundled_log_font_exists() -> None:
    assert LOG_FONT_PATH.is_file(), f"expected bundled log font at {LOG_FONT_PATH}"


def test_load_log_font_state_loads_proportional_font() -> None:
    layout = default_layout()
    state = load_log_font_state(tile_px=layout.tile_px, tile_scale=layout.tile_scale)
    assert state.enabled is True
    assert state.font is not None
    assert state.font_size_px == 19


def test_stock_layout_fits_eight_proportional_log_lines() -> None:
    layout = default_layout()
    font = load_proportional_font(
        LOG_FONT_PATH,
        size_px=proportional_font_size_px(layout.tile_px, layout.tile_scale),
    )
    assert proportional_lines_fit_in_panel(
        font=font,
        layout=layout,
        line_count=layout.message_log_lines,
    )


def test_load_log_font_state_missing_path_falls_back(tmp_path: Path) -> None:
    reset_log_font_warnings()
    missing = tmp_path / "missing.ttf"
    state = load_log_font_state(tile_px=12, tile_scale=2, font_path=missing)
    assert state.enabled is False
    assert state.font is None


def test_load_log_font_state_warns_once(tmp_path: Path) -> None:
    reset_log_font_warnings()
    missing = tmp_path / "missing.ttf"
    with warnings.catch_warnings(record=True) as first_pass:
        warnings.simplefilter("always")
        load_log_font_state(tile_px=12, tile_scale=2, font_path=missing)
    assert len(first_pass) == 1
    assert "message log TTF not found" in str(first_pass[0].message)

    with warnings.catch_warnings(record=True) as second_pass:
        warnings.simplefilter("always")
        load_log_font_state(tile_px=12, tile_scale=2, font_path=missing)
    assert len(second_pass) == 0


def test_proportional_font_has_variable_glyph_widths() -> None:
    font = load_proportional_font(LOG_FONT_PATH, size_px=16)
    assert measure_text(font, "iii") < measure_text(font, "WWW")


def test_wrap_log_text_pixels_uses_glyph_widths() -> None:
    font = load_proportional_font(LOG_FONT_PATH, size_px=16)
    narrow_width = int(measure_text(font, "WWWWWW"))
    lines = wrap_log_text_pixels(
        "iii WWWWWWW",
        font=font,
        max_width_px=narrow_width,
    )
    assert len(lines) >= 2


def test_wrap_log_segments_pixels_preserves_colors() -> None:
    from src.log_markup import LogSegment

    font = load_proportional_font(LOG_FONT_PATH, size_px=16)
    narrow_width = int(measure_text(font, "magic glows"))
    rows = wrap_log_segments_pixels(
        (
            LogSegment(text="plain ", fg=(192, 192, 192)),
            LogSegment(text="magic glows", fg=(100, 220, 255)),
        ),
        font=font,
        max_width_px=narrow_width,
    )
    assert len(rows) >= 2
    assert rows[0][0].fg == (192, 192, 192)
    assert rows[-1][-1].fg == (100, 220, 255)


def test_compute_console_viewport_integer_scaling() -> None:
    layout = default_layout()
    console = make_console()
    scale, dest_x, dest_y, dest_w, dest_h = compute_console_viewport(
        (layout.root_cols * layout.tile_px * layout.tile_scale * 2,
         layout.root_rows * layout.tile_px * layout.tile_scale * 2),
        console,
        layout,
        integer_scaling=True,
        align=(0, 0),
    )
    assert scale == 2
    assert dest_x == 0
    assert dest_y == 0
    assert dest_w == console.width * layout.tile_px * layout.tile_scale * 2
    assert dest_h == console.height * layout.tile_px * layout.tile_scale * 2


def test_clear_renderer_sets_draw_color_before_clear() -> None:
    from src.ui.log_present import clear_renderer

    events: list[tuple[int, int, int, int] | None] = []

    class _FakeRenderer:
        @property
        def draw_color(self) -> tuple[int, int, int, int]:
            return events[-1] if events else (0, 0, 0, 0)

        @draw_color.setter
        def draw_color(self, value: tuple[int, int, int, int]) -> None:
            events.append(value)

        def clear(self) -> None:
            events.append(None)

    clear_renderer(_FakeRenderer(), (12, 34, 56))
    assert events[0] == (12, 34, 56, 255)
    assert events[1] is None


def test_log_region_dest_rect_aligns_with_layout() -> None:
    layout = default_layout()
    log_rect = layout.region("message_log")
    cell = layout.tile_px * layout.tile_scale
    dest = log_region_dest_rect(
        log_rect,
        layout=layout,
        scale=2,
        dest_x=0,
        dest_y=0,
    )
    assert dest == (
        float(log_rect.x * cell * 2),
        float(log_rect.y * cell * 2),
        float(log_rect.w * cell * 2),
        float(log_rect.h * cell * 2),
    )


def test_engine_render_blits_log_by_default() -> None:
    from src.engine import GameEngine
    from src.message_log import MessageLog

    engine = GameEngine(player_name="Tester")
    engine.message_log = MessageLog()
    engine.message_log.add("cp437 log blit check")
    console = render_engine_frame(engine)
    assert "cp437 log blit check" in message_log_text(console, engine.ui_layout)


def test_engine_render_can_skip_log_blit() -> None:
    from src.engine import GameEngine
    from src.message_log import MessageLog

    engine = GameEngine(player_name="Tester")
    engine.message_log = MessageLog()
    engine.message_log.add("proportional composite path")
    console = make_console()
    engine.render(console, blit_message_log=False)
    assert engine.play_log_console is not None
    assert "proportional composite path" not in message_log_text(console, engine.ui_layout)
    log_console = engine.play_log_console
    ch = int(log_console.rgba[1, 0]["ch"])
    assert chr(ch) == "p"