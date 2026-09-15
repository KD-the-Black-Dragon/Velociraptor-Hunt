"""PR5: dedicated message log panel in layout region."""

from __future__ import annotations

from src.engine import GameEngine
from src.message_log import MessageLog
from src.systems.render import render_message_log, render_message_log_panel
from src.ui.regions import REGION_BACKGROUND

from tests.ui_test_helpers import (
    default_layout,
    make_console,
    make_region_bundle,
    message_log_rect,
    message_log_text,
    message_log_y,
    render_engine_frame,
)


def _cell_char(console, x: int, y: int) -> str:
    ch = int(console.rgba[x, y]["ch"])
    return chr(ch) if ch else " "


def test_play_regions_message_log_matches_layout() -> None:
    layout = default_layout()
    bundle = make_region_bundle(layout)
    expected = layout.region("message_log")
    placement = bundle.placement("message_log")
    assert placement.x == expected.x
    assert placement.y == expected.y
    assert placement.w == expected.w
    assert placement.h == expected.h


def test_message_log_console_matches_layout_region() -> None:
    layout = default_layout()
    bundle = make_region_bundle(layout)
    log_console = bundle.console("message_log")
    rect = layout.region("message_log")
    assert log_console.width == rect.w
    assert log_console.height == rect.h


def test_render_message_log_shows_configured_line_count() -> None:
    layout = default_layout()
    max_lines = layout.message_log_lines
    console = make_console(72, max_lines)
    messages = [f"line-{index}" for index in range(max_lines + 4)]
    render_message_log(console, messages, max_lines=max_lines)

    def row_text(y: int) -> str:
        return "".join(_cell_char(console, x, y) for x in range(console.width)).strip()

    assert row_text(0) == "line-4"
    assert row_text(max_lines - 1) == f"line-{max_lines + 3}"


def test_render_message_log_panel_fills_background() -> None:
    layout = default_layout()
    bundle = make_region_bundle(layout)
    log_console = bundle.console("message_log")
    render_message_log_panel(log_console, ["hello"], max_lines=layout.message_log_lines)
    rect = layout.region("message_log")
    bg = tuple(log_console.rgba[0, 0]["bg"][:3])
    assert bg == REGION_BACKGROUND
    assert _cell_char(log_console, 1, 0) == "h"


def test_engine_render_shows_messages_in_message_log_region() -> None:
    engine = GameEngine(player_name="Tester")
    engine.message_log = MessageLog()
    engine.message_log.add("region pipeline check")
    layout = engine.ui_layout
    console = render_engine_frame(engine)
    log_text = message_log_text(console, layout)
    assert "region pipeline check" in log_text
    assert "Tester" not in log_text


def test_message_log_starts_below_map_viewport() -> None:
    layout = default_layout()
    map_r = layout.region("map_viewport")
    log_r = layout.region("message_log")
    assert message_log_y(layout) == map_r.y + map_r.h
    assert log_r.h >= layout.message_log_lines