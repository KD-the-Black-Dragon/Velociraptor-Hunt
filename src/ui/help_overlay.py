"""Full-screen help overlay (F1, ?)."""

from __future__ import annotations

import attrs
import tcod.console
import tcod.event
from tcod.event import KeySym

from src.input_handlers import is_ctrl_p, is_help_open_key
from src.systems.render import MESSAGE_LOG_BACKGROUND
from src.text import cp437_safe
from src.ui.log_overlay import LogOverlayState, handle_log_overlay_event

HELP_OVERLAY_FOOTER = "Esc: close"
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
            "> (Shift + .) - descend stairs when standing on '>' glyph",
            body,
        ),
        HelpTextLine("", body),
        HelpTextLine("Meta", section),
        HelpTextLine("Ctrl+P - full message log", body),
        HelpTextLine("F1 or ? - this help", body),
        HelpTextLine("Ctrl+Q - quit to main menu", body),
    )


HELP_LINES: tuple[str, ...] = tuple(
    line.text for line in help_display_lines() if line.text
)


@attrs.define
class HelpOverlayState:
    """Whether the help overlay is visible."""

    active: bool = False

    def open(self) -> None:
        self.active = True

    def close(self) -> None:
        self.active = False

    def toggle(self) -> None:
        if self.active:
            self.close()
        else:
            self.open()


def handle_help_overlay_event(
    help_state: HelpOverlayState,
    log_state: LogOverlayState,
    event: tcod.event.Event,
    *,
    log_line_count: int,
    log_viewport_lines: int,
) -> bool:
    """Handle help overlay input. Return True when the event is consumed."""
    if is_help_open_key(event):
        if help_state.active:
            help_state.close()
        else:
            log_state.close()
            help_state.open()
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

    return True


def render_help_overlay(console: tcod.console.Console) -> None:
    """Draw the full-screen help overlay on the root console (CP437 fallback)."""
    console.clear(bg=MESSAGE_LOG_BACKGROUND)
    max_inner = max(1, console.width - 2)
    row_index = 0
    for line in help_display_lines():
        if row_index >= console.height - 1:
            break
        if not line.text:
            row_index += 1
            continue
        safe = cp437_safe(line.text)[:max_inner]
        console.print(1, row_index, safe, fg=line.fg)
        row_index += 1

    footer = cp437_safe(HELP_OVERLAY_FOOTER)
    footer_x = max(1, (console.width - len(footer)) // 2)
    console.print(
        footer_x,
        console.height - 1,
        footer[: console.width - 2],
        fg=HELP_FOOTER_FG,
    )