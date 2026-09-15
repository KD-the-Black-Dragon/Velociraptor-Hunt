"""New-game overwrite confirmation overlay (when a save slot exists)."""

from __future__ import annotations

from enum import Enum, auto

import attrs
import tcod.console
import tcod.event
from tcod.event import KeySym, Modifier

from src.ui.menu_dialog import render_confirm_dialog

NEW_GAME_OVERWRITE_PROMPT = (
    "A saved hunt exists and will be abandoned. Proceed? (Y/n)"
)
NEW_GAME_OVERWRITE_INVALID = "Please type capital 'Y' or lowercase 'n' only."


class NewGameConfirmAction(Enum):
    """Outcome of new-game overwrite confirmation input."""

    NONE = auto()
    CONFIRM = auto()
    CANCEL = auto()


@attrs.define
class NewGameConfirmState:
    """Active overwrite prompt overlay on the main menu."""

    error_message: str = ""


def handle_new_game_confirm_event(
    state: NewGameConfirmState,
    event: tcod.event.Event,
) -> NewGameConfirmAction:
    """Accept capital Y (confirm), lowercase n (cancel), or Escape (cancel)."""
    if not isinstance(event, tcod.event.KeyDown):
        return NewGameConfirmAction.NONE

    sym = event.sym
    if sym == KeySym.ESCAPE:
        state.error_message = ""
        return NewGameConfirmAction.CANCEL

    if sym in (
        KeySym.LSHIFT,
        KeySym.RSHIFT,
        KeySym.LCTRL,
        KeySym.RCTRL,
        KeySym.LALT,
        KeySym.RALT,
        KeySym.CAPSLOCK,
    ):
        return NewGameConfirmAction.NONE

    shift = bool(event.mod & Modifier.SHIFT)
    if sym == KeySym.Y and shift:
        state.error_message = ""
        return NewGameConfirmAction.CONFIRM
    if sym == KeySym.N and not shift:
        state.error_message = ""
        return NewGameConfirmAction.CANCEL

    state.error_message = NEW_GAME_OVERWRITE_INVALID
    return NewGameConfirmAction.NONE


def render_new_game_confirm(
    console: tcod.console.Console,
    state: NewGameConfirmState,
) -> None:
    """Draw overwrite confirmation in the lower menu band with dialog chrome."""
    render_confirm_dialog(
        console,
        [NEW_GAME_OVERWRITE_PROMPT],
        error_message=state.error_message,
        band="lower",
    )
