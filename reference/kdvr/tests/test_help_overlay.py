"""PR6: help overlay (F1, ?)."""

from __future__ import annotations

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.engine import GameEngine
from src.input_handlers import is_help_open_key
from src.systems.item_modals import begin_inspect
from src.ui.help_overlay import (
    HELP_LINES,
    HelpOverlayState,
    handle_help_overlay_event,
    render_help_overlay,
)
from src.ui.log_overlay import LogOverlayState
from tests.ui_test_helpers import make_console, render_engine_frame


def _keydown(sym: KeySym, *, mod: Modifier = Modifier.NONE) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=mod)


def test_help_content_excludes_debug_keys() -> None:
    text = "\n".join(HELP_LINES).lower()
    for forbidden in ("f2", "f3", "f4", "debug", " press r ", " press s "):
        assert forbidden not in text


def test_help_content_includes_come_here() -> None:
    text = "\n".join(HELP_LINES)
    assert '1 - shout "Come here!"' in text


def test_help_content_includes_meta_bindings() -> None:
    text = "\n".join(HELP_LINES)
    assert "Ctrl+P - full message log" in text
    assert "5 - extended rest" in text
    assert "F1 or ? - this help" in text
    assert "F10 - toggle 4K UI scaling" in text


def test_help_content_uses_hyphen_key_format() -> None:
    text = "\n".join(HELP_LINES)
    assert "i - inspect inventory" in text
    assert "w - wield weapon" in text
    assert ". or H or numpad5 - wait 1 turn" in text
    assert "> (Shift + .), 0, or NumPad0 - descend stairs on '>'" in text


def test_wait_is_under_movement_section() -> None:
    from src.ui.help_overlay import help_display_lines

    lines = [line.text for line in help_display_lines()]
    movement_index = lines.index("Movement")
    actions_index = lines.index("Actions")
    wait_index = lines.index(". or H or numpad5 - wait 1 turn")
    assert movement_index < wait_index < actions_index


def test_is_help_open_key() -> None:
    assert is_help_open_key(_keydown(KeySym.F1))
    assert is_help_open_key(_keydown(KeySym.QUESTION))
    assert is_help_open_key(_keydown(KeySym.SLASH, mod=Modifier.SHIFT))
    assert not is_help_open_key(_keydown(KeySym.SLASH))
    assert not is_help_open_key(_keydown(KeySym.P))


def test_f1_opens_help_and_closes_log() -> None:
    help_state = HelpOverlayState()
    log_state = LogOverlayState()
    log_state.open_at_tail(line_count=10, viewport_lines=5)
    assert handle_help_overlay_event(
        help_state,
        log_state,
        _keydown(KeySym.F1),
        log_line_count=10,
        log_viewport_lines=5,
    )
    assert help_state.active
    assert not log_state.active


def test_escape_closes_help() -> None:
    help_state = HelpOverlayState()
    log_state = LogOverlayState()
    help_state.open()
    assert handle_help_overlay_event(
        help_state,
        log_state,
        _keydown(KeySym.ESCAPE),
        log_line_count=0,
        log_viewport_lines=5,
    )
    assert not help_state.active


def test_ctrl_p_from_help_opens_log() -> None:
    from src.input_handlers import is_ctrl_p

    help_state = HelpOverlayState()
    log_state = LogOverlayState()
    help_state.open()
    event = _keydown(KeySym.P, mod=Modifier.LCTRL)
    assert is_ctrl_p(event)
    assert handle_help_overlay_event(
        help_state,
        log_state,
        event,
        log_line_count=12,
        log_viewport_lines=8,
    )
    assert not help_state.active
    assert log_state.active


def test_engine_help_available_during_inventory_modal() -> None:
    engine = GameEngine(player_name="Tester")
    assert engine.player is not None
    begin_inspect(engine.player, engine.inventory_modal, engine.message_log)
    engine.handle_event(_keydown(KeySym.F1))
    assert engine.help_overlay.active
    engine.handle_event(_keydown(KeySym.ESCAPE))
    assert not engine.help_overlay.active
    assert engine.inventory_modal.active


def test_engine_render_help_hides_map() -> None:
    engine = GameEngine(player_name="Tester")
    engine.help_overlay.open()
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
    assert "Help" in overlay_text
    assert "Ctrl+P" in overlay_text


def test_render_help_overlay_draws_footer() -> None:
    console = make_console()
    render_help_overlay(console)
    footer_row = console.height - 1
    text = "".join(
        chr(int(console.rgba[x, footer_row]["ch"]))
        if int(console.rgba[x, footer_row]["ch"])
        else " "
        for x in range(console.width)
    )
    assert "Esc: close" in text
    assert "PgUp/PgDn" in text


def test_help_scroll_line_and_page() -> None:
    help_state = HelpOverlayState()
    log_state = LogOverlayState()
    help_state.open()
    assert help_state.scroll_offset == 0

    assert handle_help_overlay_event(
        help_state,
        log_state,
        _keydown(KeySym.DOWN),
        log_line_count=0,
        log_viewport_lines=5,
        help_viewport_lines=5,
    )
    assert help_state.scroll_offset == 1

    assert handle_help_overlay_event(
        help_state,
        log_state,
        _keydown(KeySym.PAGEDOWN),
        log_line_count=0,
        log_viewport_lines=5,
        help_viewport_lines=5,
    )
    assert help_state.scroll_offset == 6

    assert handle_help_overlay_event(
        help_state,
        log_state,
        _keydown(KeySym.UP),
        log_line_count=0,
        log_viewport_lines=5,
        help_viewport_lines=5,
    )
    assert help_state.scroll_offset == 5


def test_help_scroll_reveals_cutoff_meta_on_short_console() -> None:
    """Short console cuts Meta; scrolling brings Ctrl+P into view."""
    help_state = HelpOverlayState()
    help_state.open(viewport_lines=11)
    short = make_console(width=80, height=12)
    render_help_overlay(short, help_state, viewport_lines=11)
    body = "".join(
        chr(int(short.rgba[x, y]["ch"])) if int(short.rgba[x, y]["ch"]) else " "
        for y in range(short.height - 1)
        for x in range(short.width)
    )
    assert "Ctrl+P" not in body

    for _ in range(10):
        handle_help_overlay_event(
            help_state,
            LogOverlayState(),
            _keydown(KeySym.PAGEDOWN),
            log_line_count=0,
            log_viewport_lines=11,
            help_viewport_lines=11,
        )
    render_help_overlay(short, help_state, viewport_lines=11)
    body = "".join(
        chr(int(short.rgba[x, y]["ch"])) if int(short.rgba[x, y]["ch"]) else " "
        for y in range(short.height - 1)
        for x in range(short.width)
    )
    assert "Ctrl+P" in body


def test_help_viewport_uses_proportional_capacity_when_console_fits() -> None:
    """Regression: prop font clips while console row count still fits all lines."""
    from src.ui.bootstrap import layout_for_preset
    from src.ui.dynamic_layout import cells_from_pixels, minimum_window_pixels, resolve_dynamic_layout
    from src.ui.help_overlay import help_line_count
    from src.ui.log_overlay import overlay_viewport_lines
    from src.ui.proportional_log import help_overlay_viewport_lines

    base = layout_for_preset("standard")
    mw, mh = minimum_window_pixels(base)
    cols, rows = cells_from_pixels(base, mw, mh)
    layout = resolve_dynamic_layout(base, cols, rows)

    console_vp = overlay_viewport_lines(layout)
    prop_vp = help_overlay_viewport_lines(layout)
    total = help_line_count()
    assert console_vp >= total
    assert prop_vp < total

    help_state = HelpOverlayState()
    help_state.open(viewport_lines=prop_vp)
    handle_help_overlay_event(
        help_state,
        LogOverlayState(),
        _keydown(KeySym.DOWN),
        log_line_count=0,
        log_viewport_lines=console_vp,
        help_viewport_lines=prop_vp,
    )
    assert help_state.scroll_offset == 1