"""Depth entry screen for the secret depth-jump new-game flow."""

from __future__ import annotations

from enum import Enum, auto

import attrs
import tcod.console
import tcod.event
from tcod.event import KeySym

from src.data.depth_jump_start_loader import default_depth_jump_start_config
from src.input_handlers import MODAL_ADVANCE_KEYS
from src.text import cp437_safe

DEPTH_ENTRY_INVALID = "Please input an integer from 1 to 20"


class DepthEntryAction(Enum):
    """Outcome of depth-entry input handling."""

    NONE = auto()
    CONFIRM = auto()
    CANCEL = auto()


@attrs.define
class DepthEntryState:
    """Single-line depth buffer for depth-jump starts."""

    buffer: str = ""
    error_message: str = ""

    def append_digit(self, digit: str) -> None:
        if len(self.buffer) >= 2:
            return
        self.buffer += digit

    def backspace(self) -> None:
        if self.buffer:
            self.buffer = self.buffer[:-1]
        self.error_message = ""


def parse_depth_value(raw: str, *, max_depth: int) -> int | None:
    """Return parsed depth when in ``[1, max_depth]``; else ``None``."""
    stripped = raw.strip()
    if not stripped.isdigit():
        return None
    value = int(stripped)
    if value < 1 or value > max_depth:
        return None
    return value


def handle_depth_entry_event(
    state: DepthEntryState,
    event: tcod.event.Event,
    *,
    max_depth: int | None = None,
) -> DepthEntryAction:
    """Process one event on the depth entry screen."""
    if not isinstance(event, tcod.event.KeyDown):
        return DepthEntryAction.NONE

    cap = max_depth if max_depth is not None else default_depth_jump_start_config().max_target_depth
    sym = event.sym
    if sym == KeySym.BACKSPACE:
        state.backspace()
    elif sym in MODAL_ADVANCE_KEYS:
        if parse_depth_value(state.buffer, max_depth=cap) is None:
            state.error_message = DEPTH_ENTRY_INVALID
            return DepthEntryAction.NONE
        state.error_message = ""
        return DepthEntryAction.CONFIRM
    elif sym == KeySym.ESCAPE:
        state.error_message = ""
        return DepthEntryAction.CANCEL
    elif KeySym.N0 <= sym <= KeySym.N9:
        state.append_digit(chr(sym))
        state.error_message = ""
    elif KeySym.KP_0 <= sym <= KeySym.KP_9:
        state.append_digit(chr(ord("0") + (sym - KeySym.KP_0)))
        state.error_message = ""
    return DepthEntryAction.NONE


def _centered_x(console: tcod.console.Console, text: str) -> int:
    return max(0, (console.width - len(text)) // 2)


def render_depth_entry(console: tcod.console.Console, state: DepthEntryState) -> None:
    """Draw the depth entry prompt on a black screen."""
    console.clear()
    cap = default_depth_jump_start_config().max_target_depth
    prompt = f"Enter starting depth (1-{cap}):"
    hint = "(Enter to confirm, Escape to cancel)"
    entry = f"> {state.buffer}_"

    prompt_y = console.height // 2 - 2
    console.print(_centered_x(console, prompt), prompt_y, cp437_safe(prompt), fg=(255, 220, 120))
    console.print(_centered_x(console, entry), prompt_y + 2, cp437_safe(entry), fg=(255, 255, 220))
    console.print(_centered_x(console, hint), prompt_y + 4, cp437_safe(hint), fg=(140, 140, 140))
    if state.error_message:
        console.print(
            _centered_x(console, state.error_message),
            prompt_y + 6,
            cp437_safe(state.error_message),
            fg=(255, 120, 120),
        )