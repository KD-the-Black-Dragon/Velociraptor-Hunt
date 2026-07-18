from __future__ import annotations

from enum import Enum, auto

import attrs
import tcod.console
import tcod.event
from tcod.event import KeySym, Modifier

from src.ui.menu_dialog import render_confirm_dialog

MACGUFFIN_VICTORY_INVALID = "Please type capital 'Y' or lowercase 'n' only."


class MacguffinVictoryConfirmAction(Enum):
    """Outcome of macguffin victory prompt input."""

    NONE = auto()
    CONFIRM = auto()
    CANCEL = auto()


@attrs.define
class MacguffinVictoryConfirmState:
    """Active macguffin victory prompt overlay during gameplay."""

    display_name: str = ""
    macguffin_id: str = ""
    score: int = 0
    error_message: str = ""

    @property
    def active(self) -> bool:
        return bool(self.macguffin_id)

    def open(self, *, macguffin_id: str, display_name: str, score: int) -> None:
        self.macguffin_id = macguffin_id
        self.display_name = display_name
        self.score = score
        self.error_message = ""

    def reset(self) -> None:
        self.macguffin_id = ""
        self.display_name = ""
        self.score = 0
        self.error_message = ""


def victory_prompt_lines(display_name: str) -> tuple[str, str]:
    return (
        f"You have found {display_name}!",
        "Would you like to end your run in victory? (Y/n)",
    )


def victory_prompt(display_name: str) -> str:
    first, second = victory_prompt_lines(display_name)
    return f"{first}\n\n{second}"


def handle_macguffin_victory_confirm_event(
    state: MacguffinVictoryConfirmState,
    event: tcod.event.Event,
) -> MacguffinVictoryConfirmAction:
    """Accept only capital Y (confirm) or lowercase n (cancel)."""
    if not isinstance(event, tcod.event.KeyDown):
        return MacguffinVictoryConfirmAction.NONE

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
        return MacguffinVictoryConfirmAction.NONE

    shift = bool(event.mod & Modifier.SHIFT)
    if sym == KeySym.Y and shift:
        state.error_message = ""
        return MacguffinVictoryConfirmAction.CONFIRM
    if sym == KeySym.N and not shift:
        state.error_message = ""
        return MacguffinVictoryConfirmAction.CANCEL

    state.error_message = MACGUFFIN_VICTORY_INVALID
    return MacguffinVictoryConfirmAction.NONE


def render_macguffin_victory_confirm(
    console: tcod.console.Console,
    state: MacguffinVictoryConfirmState,
) -> None:
    """Draw macguffin victory confirmation with shared dialog chrome."""
    first_line, second_line = victory_prompt_lines(state.display_name)
    render_confirm_dialog(
        console,
        [first_line, second_line],
        error_message=state.error_message,
        band="center",
    )
