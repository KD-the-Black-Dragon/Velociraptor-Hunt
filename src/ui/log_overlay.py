"""Full-screen scrollable message log overlay (Ctrl+P)."""

from __future__ import annotations

import attrs
import tcod.console
import tcod.event
from tcod.event import KeySym

from src.input_handlers import (
    LOG_OVERLAY_LINE_DOWN_KEYS,
    LOG_OVERLAY_LINE_UP_KEYS,
    LOG_OVERLAY_PAGE_DOWN_KEYS,
    LOG_OVERLAY_PAGE_UP_KEYS,
    is_ctrl_p,
)
from src.message_log import LogEntry
from src.systems.render import (
    MESSAGE_LOG_BACKGROUND,
    LogDisplayLine,
    expand_log_entries_to_display_lines,
)
from src.text import cp437_safe
from src.ui.layout import UILayout

LOG_OVERLAY_FOOTER = "Esc: close | Arrows: line | PgUp/PgDn: page"
LOG_OVERLAY_FOOTER_FG = (160, 160, 170)


def clamp_scroll_offset(
    offset: int,
    *,
    line_count: int,
    viewport_lines: int,
) -> int:
    """Clamp the first visible wrapped line index."""
    if line_count <= 0 or viewport_lines <= 0:
        return 0
    max_offset = max(0, line_count - viewport_lines)
    return max(0, min(offset, max_offset))


def scroll_offset_for_tail(*, line_count: int, viewport_lines: int) -> int:
    """Scroll position that shows the newest lines at the bottom."""
    return clamp_scroll_offset(
        line_count,
        line_count=line_count,
        viewport_lines=viewport_lines,
    )


def apply_line_scroll(
    offset: int,
    delta: int,
    *,
    line_count: int,
    viewport_lines: int,
) -> int:
    return clamp_scroll_offset(
        offset + delta,
        line_count=line_count,
        viewport_lines=viewport_lines,
    )


def apply_page_scroll(
    offset: int,
    delta: int,
    *,
    line_count: int,
    viewport_lines: int,
) -> int:
    return clamp_scroll_offset(
        offset + delta * viewport_lines,
        line_count=line_count,
        viewport_lines=viewport_lines,
    )


def overlay_text_width(layout: UILayout) -> int:
    return max(1, layout.root_cols - 2)


def overlay_viewport_lines(layout: UILayout) -> int:
    """Visible wrapped lines excluding the footer row."""
    return max(1, layout.root_rows - 1)


def build_overlay_display_lines(
    entries: list[LogEntry],
    *,
    layout: UILayout,
) -> list[LogDisplayLine]:
    return expand_log_entries_to_display_lines(
        entries,
        width_limit=overlay_text_width(layout),
    )


@attrs.define
class LogOverlayState:
    """Scroll state for the full log overlay."""

    active: bool = False
    scroll_offset: int = 0

    def open_at_tail(self, *, line_count: int, viewport_lines: int) -> None:
        self.active = True
        self.scroll_offset = scroll_offset_for_tail(
            line_count=line_count,
            viewport_lines=viewport_lines,
        )

    def close(self) -> None:
        self.active = False

    def toggle(
        self,
        *,
        line_count: int,
        viewport_lines: int,
    ) -> None:
        if self.active:
            self.close()
            return
        self.open_at_tail(line_count=line_count, viewport_lines=viewport_lines)


def handle_log_overlay_event(
    state: LogOverlayState,
    event: tcod.event.Event,
    *,
    line_count: int,
    viewport_lines: int,
) -> bool:
    """Handle overlay input. Return True when the event is consumed."""
    if is_ctrl_p(event):
        state.toggle(line_count=line_count, viewport_lines=viewport_lines)
        return True
    if not state.active:
        return False
    if not isinstance(event, tcod.event.KeyDown):
        return True

    sym = event.sym
    if sym == KeySym.ESCAPE:
        state.close()
        return True
    if sym in LOG_OVERLAY_LINE_UP_KEYS:
        state.scroll_offset = apply_line_scroll(
            state.scroll_offset,
            -1,
            line_count=line_count,
            viewport_lines=viewport_lines,
        )
        return True
    if sym in LOG_OVERLAY_LINE_DOWN_KEYS:
        state.scroll_offset = apply_line_scroll(
            state.scroll_offset,
            1,
            line_count=line_count,
            viewport_lines=viewport_lines,
        )
        return True
    if sym in LOG_OVERLAY_PAGE_UP_KEYS:
        state.scroll_offset = apply_page_scroll(
            state.scroll_offset,
            -1,
            line_count=line_count,
            viewport_lines=viewport_lines,
        )
        return True
    if sym in LOG_OVERLAY_PAGE_DOWN_KEYS:
        state.scroll_offset = apply_page_scroll(
            state.scroll_offset,
            1,
            line_count=line_count,
            viewport_lines=viewport_lines,
        )
        return True
    return True


def render_log_overlay(
    console: tcod.console.Console,
    entries: list[LogEntry],
    state: LogOverlayState,
    *,
    layout: UILayout,
) -> None:
    """Draw the full-screen log overlay on the root console."""
    console.clear(bg=MESSAGE_LOG_BACKGROUND)
    display_lines = build_overlay_display_lines(entries, layout=layout)
    line_count = len(display_lines)
    viewport_lines = overlay_viewport_lines(layout)
    state.scroll_offset = clamp_scroll_offset(
        state.scroll_offset,
        line_count=line_count,
        viewport_lines=viewport_lines,
    )
    visible = display_lines[
        state.scroll_offset : state.scroll_offset + viewport_lines
    ]
    width_limit = overlay_text_width(layout)
    for row_index, line in enumerate(visible):
        x = 1
        for segment in line.segments:
            remaining = width_limit - (x - 1)
            if remaining <= 0:
                break
            clipped = segment.text[:remaining]
            if not clipped:
                continue
            console.print(x, row_index, clipped, fg=segment.fg)
            x += len(clipped)

    footer = cp437_safe(LOG_OVERLAY_FOOTER)
    footer_x = max(1, (console.width - len(footer)) // 2)
    console.print(
        footer_x,
        console.height - 1,
        footer[: console.width - 2],
        fg=LOG_OVERLAY_FOOTER_FG,
    )