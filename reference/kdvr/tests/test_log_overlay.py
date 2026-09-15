"""PR5: full message log overlay (Ctrl+P)."""

from __future__ import annotations

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.constants import MESSAGE_LOG_CAPACITY
from src.engine import GameEngine
from src.input_handlers import is_ctrl_p
from src.message_log import MessageLog
from src.ui.log_overlay import (
    LogOverlayState,
    apply_line_scroll,
    apply_page_scroll,
    build_overlay_display_lines,
    clamp_scroll_offset,
    handle_log_overlay_event,
    overlay_viewport_lines,
    scroll_offset_for_tail,
)
from tests.ui_test_helpers import default_layout, make_console, render_engine_frame


def _keydown(sym: KeySym, *, mod: Modifier = Modifier.NONE) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=mod)


def _ctrl_p_event() -> tcod.event.KeyDown:
    return _keydown(KeySym.P, mod=Modifier.LCTRL)


def test_message_log_capacity_is_100() -> None:
    log = MessageLog()
    assert log._messages.maxlen == MESSAGE_LOG_CAPACITY
    assert MESSAGE_LOG_CAPACITY == 100


def test_is_ctrl_p() -> None:
    assert is_ctrl_p(_ctrl_p_event())
    assert not is_ctrl_p(_keydown(KeySym.P))
    assert not is_ctrl_p(_keydown(KeySym.Q, mod=Modifier.CTRL))


def test_scroll_offset_for_tail() -> None:
    assert scroll_offset_for_tail(line_count=20, viewport_lines=8) == 12
    assert scroll_offset_for_tail(line_count=5, viewport_lines=8) == 0


def test_clamp_scroll_offset() -> None:
    assert clamp_scroll_offset(99, line_count=20, viewport_lines=8) == 12
    assert clamp_scroll_offset(-3, line_count=20, viewport_lines=8) == 0


def test_apply_line_and_page_scroll() -> None:
    offset = scroll_offset_for_tail(line_count=30, viewport_lines=10)
    assert apply_line_scroll(offset, -1, line_count=30, viewport_lines=10) == offset - 1
    assert apply_page_scroll(offset, -1, line_count=30, viewport_lines=10) == offset - 10


def test_ctrl_p_toggles_overlay() -> None:
    state = LogOverlayState()
    assert handle_log_overlay_event(
        state,
        _ctrl_p_event(),
        line_count=12,
        viewport_lines=8,
    )
    assert state.active
    assert handle_log_overlay_event(
        state,
        _ctrl_p_event(),
        line_count=12,
        viewport_lines=8,
    )
    assert not state.active


def test_overlay_opens_at_tail() -> None:
    state = LogOverlayState()
    handle_log_overlay_event(state, _ctrl_p_event(), line_count=25, viewport_lines=10)
    assert state.scroll_offset == 15


def test_escape_closes_overlay() -> None:
    state = LogOverlayState()
    state.open_at_tail(line_count=10, viewport_lines=5)
    assert handle_log_overlay_event(
        state,
        _keydown(KeySym.ESCAPE),
        line_count=10,
        viewport_lines=5,
    )
    assert not state.active


def test_overlay_scroll_up_moves_toward_older_lines() -> None:
    state = LogOverlayState()
    state.open_at_tail(line_count=20, viewport_lines=8)
    before = state.scroll_offset
    handle_log_overlay_event(
        state,
        _keydown(KeySym.UP),
        line_count=20,
        viewport_lines=8,
    )
    assert state.scroll_offset == before - 1


def test_engine_overlay_available_during_inventory_modal() -> None:
    from src.systems.item_modals import begin_inspect

    engine = GameEngine(player_name="Tester")
    engine.message_log.add("overlay during modal")
    assert engine.player is not None
    begin_inspect(engine.player, engine.inventory_modal, engine.message_log)
    assert engine.inventory_modal.active
    engine.handle_event(_ctrl_p_event())
    assert engine.log_overlay.active
    engine.handle_event(_keydown(KeySym.ESCAPE))
    assert not engine.log_overlay.active
    assert engine.inventory_modal.active


def test_engine_render_overlay_hides_map() -> None:
    engine = GameEngine(player_name="Tester")
    engine.message_log.add("full log line")
    engine.log_overlay.open_at_tail(
        line_count=len(
            build_overlay_display_lines(
                engine.message_log.entries(),
                layout=engine.ui_layout,
            )
        ),
        viewport_lines=overlay_viewport_lines(engine.ui_layout),
    )
    console = render_engine_frame(engine)
    layout = engine.ui_layout
    map_r = layout.region("map_viewport")
    ch = int(console.rgba[map_r.x, map_r.y]["ch"])
    assert ch == 0 or chr(ch) == " "
    overlay_text = "".join(
        chr(int(console.rgba[x, y]["ch"])) if int(console.rgba[x, y]["ch"]) else " "
        for y in range(layout.root_rows - 1)
        for x in range(layout.root_cols)
    )
    assert "full log line" in overlay_text