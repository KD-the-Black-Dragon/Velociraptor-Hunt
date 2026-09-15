"""Paginated Quick Start tutorial (first-run or Options → Tutorial)."""

from __future__ import annotations

from enum import Enum, auto

import attrs
import tcod.console
import tcod.event
from tcod.event import KeySym

from src.input_handlers import MODAL_ADVANCE_KEYS
from src.systems.render import MESSAGE_LOG_BACKGROUND
from src.text import cp437_safe
from src.ui.help_overlay import (
    HELP_BODY_FG,
    HELP_FOOTER_FG,
    HELP_SECTION_FG,
    HELP_TITLE_FG,
    HelpTextLine,
)

TUTORIAL_TITLE = "Quick Start"
TUTORIAL_REMINDER_TEXT = (
    "You can view the tutorial again anytime from Options → Tutorial."
)
TUTORIAL_FOOTER_NEXT = "Enter: next page"
TUTORIAL_FOOTER_CONTINUE = "Enter: continue"
TUTORIAL_FOOTER_OPTIONS = "Enter: next | Esc: back"

TUTORIAL_ACCENT_FG = (255, 200, 200)

PAGE_CONTENT = 0
PAGE_COMMANDS = 1
PAGE_REMINDER = 2


class TutorialAction(Enum):
    """Outcome of tutorial screen input."""

    NONE = auto()
    ADVANCE = auto()
    BACK = auto()


@attrs.define
class TutorialScreenState:
    """Current tutorial page and replay mode."""

    page_index: int = PAGE_CONTENT
    include_reminder: bool = True
    from_options: bool = False

    def reset(self, *, include_reminder: bool, from_options: bool) -> None:
        self.page_index = PAGE_CONTENT
        self.include_reminder = include_reminder
        self.from_options = from_options

    @property
    def last_page_index(self) -> int:
        if self.include_reminder:
            return PAGE_REMINDER
        return PAGE_COMMANDS

    def footer_text(self) -> str:
        if self.from_options:
            return TUTORIAL_FOOTER_OPTIONS
        if self.page_index >= self.last_page_index:
            return TUTORIAL_FOOTER_CONTINUE
        return TUTORIAL_FOOTER_NEXT


def tutorial_page_lines(page_index: int) -> tuple[HelpTextLine, ...]:
    """Lines for one tutorial page."""
    body = HELP_BODY_FG
    section = HELP_SECTION_FG
    accent = TUTORIAL_ACCENT_FG

    if page_index == PAGE_CONTENT:
        return (
            HelpTextLine(TUTORIAL_TITLE, HELP_TITLE_FG),
            HelpTextLine("", body),
            HelpTextLine("This is a dungeon role-playing game.", body),
            HelpTextLine("Your goal is to get as deep as possible.", body),
            HelpTextLine(
                "There are no shops, experience points, or levels.",
                body,
            ),
            HelpTextLine("", body),
            HelpTextLine("Common map symbols", section),
            HelpTextLine("@ - you", body),
            HelpTextLine("b - an enemy bat", body),
            HelpTextLine("! - potions", body),
            HelpTextLine("/ - wands", body),
            HelpTextLine(
                "Other letters and symbols represent more objects and creatures.",
                body,
            ),
            HelpTextLine("", body),
            HelpTextLine(
                "Everything is turn-based, and there is no time limit.",
                body,
            ),
            HelpTextLine("If your run ends, you start over.", body),
        )
    if page_index == PAGE_COMMANDS:
        return (
            HelpTextLine("Movement", section),
            HelpTextLine("The numpad is the best way to move.", body),
            HelpTextLine(
                "No numpad? TYUGHJBNM approximates it: Y up, G left, J right, N down.",
                accent,
            ),
            HelpTextLine(
                "Arrow keys cannot move diagonally, which hurts survival.",
                accent,
            ),
            HelpTextLine("Walk into a monster to attack in melee.", body),
            HelpTextLine("", body),
            HelpTextLine("Actions", section),
            HelpTextLine("F1 or ? to list all commands", accent),
            HelpTextLine("x to examine", body),
            HelpTextLine(". or h or numpad 5 to wait one turn", body),
            HelpTextLine("c to close a door", body),
            HelpTextLine(
                "q to (Q)uaff potions  |  v to e(v)oke wands",
                body,
            ),
            HelpTextLine(
                "w to (w)ield a weapon  |  Shift+W to (W)ear armor",
                body,
            ),
            HelpTextLine("f to fire ranged ammunition", body),
            HelpTextLine(
                "Shift+D to dismiss an ally you no longer want",
                body,
            ),
            HelpTextLine(
                "Press the 5 key on the number row (above T) to rest in isolated areas.",
                body,
            ),
            HelpTextLine("Shift+./ >, 0, or NumPad0 to descend stairs", body),
            HelpTextLine("Ctrl+Q to quit to the main menu", body),
            HelpTextLine("", body),
            HelpTextLine(
                "Find three runes per floor for permanent stat bonuses.",
                body,
            ),
            HelpTextLine(
                "Potions and wands are very powerful and single-use.",
                accent,
            ),
            HelpTextLine(
                "When you are vulnerable, monsters can vore you. "
                "If you are digested, the run ends.",
                accent,
            ),
            HelpTextLine("", body),
            HelpTextLine("Survival tips", section),
            HelpTextLine(
                "Fight in narrow halls, rest when isolated, "
                "and try to search for loot and runes.",
                body,
            ),
            HelpTextLine(
                "Use potions, wands, and ranged weapons when in trouble, "
                "or run downstairs (monsters will not follow).",
                body,
            ),
            HelpTextLine(
                "No, really. Use those potions and wands. "
                "Trying to melee everything will not succeed.",
                accent,
            ),
            HelpTextLine(
                "If the difficulty isn't right for you, change it in the Options.",
                body,
            ),
        )
    return (
        HelpTextLine(TUTORIAL_REMINDER_TEXT, body),
    )


def handle_tutorial_event(
    state: TutorialScreenState,
    event: tcod.event.Event,
) -> TutorialAction:
    """Handle tutorial page input."""
    if not isinstance(event, tcod.event.KeyDown):
        return TutorialAction.NONE

    sym = event.sym
    if state.from_options and sym == KeySym.ESCAPE:
        return TutorialAction.BACK
    if sym in MODAL_ADVANCE_KEYS:
        return TutorialAction.ADVANCE
    return TutorialAction.NONE


def render_tutorial_screen(
    console: tcod.console.Console,
    state: TutorialScreenState,
) -> None:
    """Draw the current tutorial page (CP437 fallback)."""
    console.clear(bg=MESSAGE_LOG_BACKGROUND)
    max_inner = max(1, console.width - 2)
    row_index = 0
    for line in tutorial_page_lines(state.page_index):
        if row_index >= console.height - 1:
            break
        if not line.text:
            row_index += 1
            continue
        safe = cp437_safe(line.text)[:max_inner]
        console.print(1, row_index, safe, fg=line.fg)
        row_index += 1

    footer = cp437_safe(state.footer_text())
    footer_x = max(1, (console.width - len(footer)) // 2)
    console.print(
        footer_x,
        console.height - 1,
        footer[: console.width - 2],
        fg=HELP_FOOTER_FG,
    )