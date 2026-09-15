from __future__ import annotations

from enum import Enum, auto

import attrs
import tcod.console
import tcod.event
from tcod.event import KeySym, Modifier

from src.ui.menu_dialog import render_confirm_dialog

QUIT_PROMPT = "Do you want to quit? (Y/n)"
QUIT_INVALID_MESSAGE = "Please type capital 'Y' or lowercase 'n' only."


class QuitConfirmAction(Enum):
    """Outcome of quit-confirmation input."""

    NONE = auto()
    CONFIRM = auto()
    CANCEL = auto()


@attrs.define
class QuitConfirmState:
    """Active quit prompt overlay during gameplay."""

    error_message: str = ""


def handle_quit_confirm_event(
    state: QuitConfirmState,
    event: tcod.event.Event,
) -> QuitConfirmAction:
    """Accept only capital Y (confirm) or lowercase n (cancel)."""
    if not isinstance(event, tcod.event.KeyDown):
        return QuitConfirmAction.NONE

    sym = event.sym
    if sym in (
        KeySym.LSHIFT,
        KeySym.RSHIFT,
        KeySym.LCTRL,
        KeySym.RCTRL,
        KeySym.LALT,
        KeySym.RALT,
        KeySym.CAPSLOCK,
    ):
        return QuitConfirmAction.NONE

    shift = bool(event.mod & Modifier.SHIFT)
    if sym == KeySym.Y and shift:
        state.error_message = ""
        return QuitConfirmAction.CONFIRM
    if sym == KeySym.N and not shift:
        state.error_message = ""
        return QuitConfirmAction.CANCEL

    state.error_message = QUIT_INVALID_MESSAGE
    return QuitConfirmAction.NONE


def render_quit_confirm(
    console: tcod.console.Console,
    state: QuitConfirmState,
) -> None:
    """Draw quit confirmation with shared dialog chrome."""
    render_confirm_dialog(
        console,
        [QUIT_PROMPT],
        error_message=state.error_message,
        band="center",
    )
