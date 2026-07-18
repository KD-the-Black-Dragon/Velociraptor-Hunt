from __future__ import annotations

import string
from enum import Enum, auto

import attrs
import tcod.console
import tcod.event
from tcod.event import KeySym, Modifier


from src.input_handlers import MODAL_ADVANCE_KEYS
from src.text import cp437_safe

PLAYER_NAME_MAX_LENGTH = 24
ANONYMOUS_NAME = "Anonymous"

_PRINTABLE_ASCII = frozenset(
    ch for ch in string.printable if ch not in "\t\n\r\x0b\x0c"
)

_NAME_ENTRY_EXCLUDED_KEYS: frozenset[KeySym] = frozenset({
    KeySym.RETURN,
    KeySym.KP_ENTER,
    KeySym.ESCAPE,
    KeySym.BACKSPACE,
    KeySym.TAB,
    KeySym.DELETE,
})


class NameEntryAction(Enum):
    """Outcome of name-entry input handling."""

    NONE = auto()
    CONFIRM = auto()
    CANCEL = auto()


@attrs.define
class NameEntryState:
    """Single-line player display name buffer."""

    buffer: str = ""

    def append(self, char: str) -> None:
        if len(self.buffer) >= PLAYER_NAME_MAX_LENGTH:
            return
        self.buffer += char

    def backspace(self) -> None:
        if self.buffer:
            self.buffer = self.buffer[:-1]


def _char_from_keydown(event: tcod.event.KeyDown) -> str | None:
    """Map a KeyDown to a printable character (SDL does not emit TextInput by default)."""
    sym = event.sym
    if sym in _NAME_ENTRY_EXCLUDED_KEYS:
        return None
    if KeySym.A <= sym <= KeySym.Z:
        ch = chr(sym)
        if event.mod & Modifier.SHIFT:
            return ch.upper()
        return ch
    if KeySym.N0 <= sym <= KeySym.N9:
        return chr(sym)
    if 32 <= sym <= 126:
        ch = chr(sym)
        if ch in _PRINTABLE_ASCII:
            return ch
    return None


def resolve_display_name(raw: str) -> str:
    """Trim whitespace; empty becomes Anonymous."""
    trimmed = raw.strip()
    return trimmed if trimmed else ANONYMOUS_NAME


def handle_name_entry_event(
    state: NameEntryState,
    event: tcod.event.Event,
) -> NameEntryAction:
    """Process one event on the name entry screen."""
    if not isinstance(event, tcod.event.KeyDown):
        return NameEntryAction.NONE

    sym = event.sym
    if sym == KeySym.BACKSPACE:
        state.backspace()
    elif sym in MODAL_ADVANCE_KEYS:
        return NameEntryAction.CONFIRM
    elif sym == KeySym.ESCAPE:
        return NameEntryAction.CANCEL
    else:
        ch = _char_from_keydown(event)
        if ch is not None:
            state.append(ch)
    return NameEntryAction.NONE


def _centered_x(console: tcod.console.Console, text: str) -> int:
    return max(0, (console.width - len(text)) // 2)


def render_name_entry(console: tcod.console.Console, state: NameEntryState) -> None:
    """Draw the name entry prompt on a black screen."""
    console.clear()

    prompt = "Enter your name:"
    hint = "(Enter to confirm, Escape to cancel)"
    entry = f"> {state.buffer}_"

    prompt_y = console.height // 2 - 2
    console.print(_centered_x(console, prompt), prompt_y, cp437_safe(prompt), fg=(255, 220, 120))
    console.print(_centered_x(console, entry), prompt_y + 2, cp437_safe(entry), fg=(255, 255, 220))
    console.print(_centered_x(console, hint), prompt_y + 4, cp437_safe(hint), fg=(140, 140, 140))