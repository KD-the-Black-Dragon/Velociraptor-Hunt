"""Capital-Y gate before entering the Mods menu when a save exists."""

from __future__ import annotations

from enum import Enum, auto

import attrs
import tcod.console
import tcod.event
from tcod.event import KeySym, Modifier

from src.ui.menu_dialog import render_confirm_dialog

MODS_ENTER_PROMPT_LINES: tuple[str, ...] = (
    "Entering the Mods menu will delete your current saved game.",
    "The exact mod setup must stay the same for a run.",
    "Proceed? (Y/n)",
)
MODS_ENTER_INVALID = "Please type capital 'Y' or lowercase 'n' only."


class ModsEnterConfirmAction(Enum):
    NONE = auto()
    CONFIRM = auto()
    CANCEL = auto()


@attrs.define
class ModsEnterConfirmState:
    """Overlay on Options before opening Mods when an autosave exists."""

    error_message: str = ""


def handle_mods_enter_confirm_event(
    state: ModsEnterConfirmState,
    event: tcod.event.Event,
) -> ModsEnterConfirmAction:
    """Accept capital Y (confirm), lowercase n or Escape (cancel)."""
    if not isinstance(event, tcod.event.KeyDown):
        return ModsEnterConfirmAction.NONE

    sym = event.sym
    if sym == KeySym.ESCAPE:
        state.error_message = ""
        return ModsEnterConfirmAction.CANCEL

    if sym in (
        KeySym.LSHIFT,
        KeySym.RSHIFT,
        KeySym.LCTRL,
        KeySym.RCTRL,
        KeySym.LALT,
        KeySym.RALT,
        KeySym.CAPSLOCK,
    ):
        return ModsEnterConfirmAction.NONE

    shift = bool(event.mod & Modifier.SHIFT)
    if sym == KeySym.Y and shift:
        state.error_message = ""
        return ModsEnterConfirmAction.CONFIRM
    if sym == KeySym.N and not shift:
        state.error_message = ""
        return ModsEnterConfirmAction.CANCEL

    state.error_message = MODS_ENTER_INVALID
    return ModsEnterConfirmAction.NONE


def render_mods_enter_confirm(
    console: tcod.console.Console,
    state: ModsEnterConfirmState,
) -> None:
    """Draw the save-wipe warning with shared dialog chrome."""
    render_confirm_dialog(
        console,
        list(MODS_ENTER_PROMPT_LINES),
        error_message=state.error_message,
        band="center",
    )
