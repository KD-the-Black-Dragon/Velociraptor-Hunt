"""Full-screen scrollable help overlay (F1, ?)."""

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
    is_help_open_key,
)
from src.systems.render import MESSAGE_LOG_BACKGROUND
from src.text import cp437_safe
from src.ui.log_overlay import (
    LogOverlayState,
    apply_line_scroll,
    apply_page_scroll,
    clamp_scroll_offset,
    handle_log_overlay_event,
)

# Credits / tutorial still use Esc-only footer via this name.
HELP_OVERLAY_FOOTER = "Esc: close"
HELP_OVERLAY_SCROLL_FOOTER = "Esc: close | Arrows: line | PgUp/PgDn: page"
HELP_TITLE_FG = (255, 255, 255)
HELP_SECTION_FG = (200, 220, 255)
HELP_BODY_FG = (192, 192, 192)
HELP_FOOTER_FG = (160, 160, 170)


@attrs.define(frozen=True)
class HelpTextLine:
    text: str
    fg: tuple[int, int, int]


def help_display_lines() -> tuple[HelpTextLine, ...]:
    """Curated help rows for proportional or CP437 rendering."""
    body = HELP_BODY_FG
    section = HELP_SECTION_FG
    return (
        HelpTextLine("Help", HELP_TITLE_FG),
        HelpTextLine("", body),
        HelpTextLine("Movement", section),
        HelpTextLine(
            "Arrows, numpad, or TYUGHJBNM (Y north, N south, G west, J east)",
            body,
        ),
        HelpTextLine("T/U/B/M diagonals", body),
        HelpTextLine(". or H or numpad5 - wait 1 turn", body),
        HelpTextLine("", body),
        HelpTextLine("Actions", section),
        HelpTextLine("i - inspect inventory", body),
        HelpTextLine("d - drop item", body),
        HelpTextLine("w - wield weapon", body),
        HelpTextLine("W - wear armor", body),
        HelpTextLine("q - quaff potion", body),
        HelpTextLine("v - evoke wand", body),
        HelpTextLine("f - throw best throwable", body),
        HelpTextLine("F - pick throwable to throw", body),
        HelpTextLine("x - examine tile", body),
        HelpTextLine(", - pickup on tile", body),
        HelpTextLine("5 - extended rest", body),
        HelpTextLine("` - autoexplore", body),
        HelpTextLine(
            "Ctrl + direction - force-attack adjacent tile without moving",
            body,
        ),
        HelpTextLine('1 - shout "Come here!" (good allies in view)', body),
        HelpTextLine(
            "Shift+D - dismiss ally (target good NPC)",
            body,
        ),
        HelpTextLine(
            "> (Shift + .), 0, or NumPad0 - descend stairs on '>'",
            body,
        ),
        HelpTextLine("", body),
        HelpTextLine("Meta", section),
        HelpTextLine("Ctrl+P - full message log", body),
        HelpTextLine("F1 or ? - this help", body),
        HelpTextLine("F10 - toggle 4K UI scaling", body),
        HelpTextLine("Ctrl+Q - quit to main menu", body),
    )


HELP_LINES: tuple[str, ...] = tuple(
    line.text for line in help_display_lines() if line.text
)


def help_line_count() -> int:
    return len(help_display_lines())


def visible_help_lines(
    *,
    scroll_offset: int,
    viewport_lines: int,
) -> tuple[HelpTextLine, ...]:
    """Slice help rows for the current scroll window."""
    lines = help_display_lines()
    offset = clamp_scroll_offset(
        scroll_offset,
        line_count=len(lines),
        viewport_lines=viewport_lines,
    )
    return lines[offset : offset + viewport_lines]


@attrs.define
class HelpOverlayState:
    """Scroll state for the full help overlay."""

    active: bool = False
    scroll_offset: int = 0
    # Last computed visible-row capacity (proportional-aware). Used for input.
    viewport_lines: int = 1

    def open(self, *, viewport_lines: int | None = None) -> None:
        self.active = True
        self.scroll_offset = 0
        if viewport_lines is not None:
            self.viewport_lines = max(1, viewport_lines)

    def close(self) -> None:
        self.active = False

    def toggle(self, *, viewport_lines: int | None = None) -> None:
        if self.active:
            self.close()
        else:
            self.open(viewport_lines=viewport_lines)


def handle_help_overlay_event(
    help_state: HelpOverlayState,
    log_state: LogOverlayState,
    event: tcod.event.Event,
    *,
    log_line_count: int,
    log_viewport_lines: int,
    help_viewport_lines: int | None = None,
) -> bool:
    """Handle help overlay input. Return True when the event is consumed."""
    viewport = (
        help_state.viewport_lines
        if help_viewport_lines is None
        else help_viewport_lines
    )
    viewport = max(1, viewport)
    help_state.viewport_lines = viewport
    line_count = help_line_count()

    if is_help_open_key(event):
        if help_state.active:
            help_state.close()
        else:
            log_state.close()
            help_state.open(viewport_lines=viewport)
        return True

    if not help_state.active:
        return False

    if not isinstance(event, tcod.event.KeyDown):
        return True

    if event.sym == KeySym.ESCAPE:
        help_state.close()
        return True

    if is_ctrl_p(event):
        help_state.close()
        return handle_log_overlay_event(
            log_state,
            event,
            line_count=log_line_count,
            viewport_lines=log_viewport_lines,
        )

    sym = event.sym
    if sym in LOG_OVERLAY_LINE_UP_KEYS:
        help_state.scroll_offset = apply_line_scroll(
            help_state.scroll_offset,
            -1,
            line_count=line_count,
            viewport_lines=viewport,
        )
        return True
    if sym in LOG_OVERLAY_LINE_DOWN_KEYS:
        help_state.scroll_offset = apply_line_scroll(
            help_state.scroll_offset,
            1,
            line_count=line_count,
            viewport_lines=viewport,
        )
        return True
    if sym in LOG_OVERLAY_PAGE_UP_KEYS:
        help_state.scroll_offset = apply_page_scroll(
            help_state.scroll_offset,
            -1,
            line_count=line_count,
            viewport_lines=viewport,
        )
        return True
    if sym in LOG_OVERLAY_PAGE_DOWN_KEYS:
        help_state.scroll_offset = apply_page_scroll(
            help_state.scroll_offset,
            1,
            line_count=line_count,
            viewport_lines=viewport,
        )
        return True

    return True


def render_help_overlay(
    console: tcod.console.Console,
    state: HelpOverlayState | None = None,
    *,
    viewport_lines: int | None = None,
) -> None:
    """Draw the full-screen help overlay on the root console (CP437 fallback)."""
    console.clear(bg=MESSAGE_LOG_BACKGROUND)
    if viewport_lines is None:
        if state is not None and state.viewport_lines > 1:
            viewport_lines = state.viewport_lines
        else:
            viewport_lines = max(1, console.height - 1)
    viewport_lines = max(1, viewport_lines)
    offset = 0 if state is None else state.scroll_offset
    if state is not None:
        state.viewport_lines = viewport_lines
        state.scroll_offset = clamp_scroll_offset(
            state.scroll_offset,
            line_count=help_line_count(),
            viewport_lines=viewport_lines,
        )
        offset = state.scroll_offset
    visible = visible_help_lines(
        scroll_offset=offset,
        viewport_lines=viewport_lines,
    )
    max_inner = max(1, console.width - 2)
    row_index = 0
    for line in visible:
        if row_index >= viewport_lines:
            break
        if not line.text:
            row_index += 1
            continue
        safe = cp437_safe(line.text)[:max_inner]
        console.print(1, row_index, safe, fg=line.fg)
        row_index += 1

    footer = cp437_safe(HELP_OVERLAY_SCROLL_FOOTER)
    footer_x = max(1, (console.width - len(footer)) // 2)
    console.print(
        footer_x,
        console.height - 1,
        footer[: console.width - 2],
        fg=HELP_FOOTER_FG,
    )
