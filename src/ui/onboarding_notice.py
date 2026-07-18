"""Full-screen onboarding notice (Enter to continue)."""

from __future__ import annotations

from enum import Enum, auto

import tcod.console
import tcod.event
from tcod.event import KeySym

from src.input_handlers import MODAL_ADVANCE_KEYS
from src.systems.render import MESSAGE_LOG_BACKGROUND
from src.text import cp437_safe
from src.ui.help_overlay import HELP_BODY_FG, HELP_FOOTER_FG, HelpTextLine

ONBOARDING_NOTICE_FOOTER = "Enter: continue"
NOTICE_BODY_FG = HELP_BODY_FG
NOTICE_FOOTER_FG = HELP_FOOTER_FG

ONBOARDING_ALL_SET_LINES: tuple[str, ...] = (
    "You're all set!",
    "",
    "Good luck. :)",
)


class OnboardingNoticeAction(Enum):
    """Outcome of onboarding notice input."""

    NONE = auto()
    CONTINUE = auto()


def handle_onboarding_notice_event(event: tcod.event.Event) -> OnboardingNoticeAction:
    """Advance on Enter only."""
    if isinstance(event, tcod.event.KeyDown) and event.sym in MODAL_ADVANCE_KEYS:
        return OnboardingNoticeAction.CONTINUE
    return OnboardingNoticeAction.NONE


def onboarding_notice_lines(messages: tuple[str, ...]) -> tuple[HelpTextLine, ...]:
    """Build proportional lines for a centered notice."""
    return tuple(HelpTextLine(line, NOTICE_BODY_FG) for line in messages)


def render_onboarding_notice(
    console: tcod.console.Console,
    messages: tuple[str, ...],
) -> None:
    """Draw a full-screen notice (CP437 fallback)."""
    console.clear(bg=MESSAGE_LOG_BACKGROUND)
    start_y = max(1, (console.height - len(messages)) // 2 - 1)
    for row_offset, message in enumerate(messages):
        safe = cp437_safe(message)
        x = max(1, (console.width - len(safe)) // 2)
        y = start_y + row_offset
        console.print(x, y, safe[: console.width - 2], fg=NOTICE_BODY_FG)
    footer = cp437_safe(ONBOARDING_NOTICE_FOOTER)
    footer_x = max(1, (console.width - len(footer)) // 2)
    console.print(
        footer_x,
        console.height - 1,
        footer[: console.width - 2],
        fg=NOTICE_FOOTER_FG,
    )