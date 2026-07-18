from __future__ import annotations

from enum import Enum, auto

import tcod.console
import tcod.event
from tcod.event import KeySym

from src.input_handlers import MODAL_ADVANCE_KEYS
from src.text import cp437_safe

STUB_MESSAGE = "Coming soon"


class StubAction(Enum):
    """Outcome of stub screen input."""

    NONE = auto()
    BACK = auto()


def handle_stub_event(event: tcod.event.Event) -> StubAction:
    """Escape or Enter returns to the main menu."""
    if not isinstance(event, tcod.event.KeyDown):
        return StubAction.NONE
    if event.sym == KeySym.ESCAPE or event.sym in MODAL_ADVANCE_KEYS:
        return StubAction.BACK
    return StubAction.NONE


def _centered_x(console: tcod.console.Console, text: str) -> int:
    return max(0, (console.width - len(text)) // 2)


def render_stub_screen(console: tcod.console.Console, *, title: str) -> None:
    """Draw a minimal placeholder screen with a coming-soon line."""
    console.clear()
    center_y = console.height // 2
    console.print(
        _centered_x(console, title),
        center_y - 3,
        cp437_safe(title),
        fg=(255, 220, 120),
    )
    console.print(
        _centered_x(console, STUB_MESSAGE),
        center_y,
        cp437_safe(STUB_MESSAGE),
        fg=(200, 200, 200),
    )
    hint = "(Escape or Enter to back)"
    console.print(
        _centered_x(console, hint),
        center_y + 3,
        cp437_safe(hint),
        fg=(100, 100, 100),
    )