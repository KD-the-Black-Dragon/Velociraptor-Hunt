"""Full-screen credits page (main menu)."""

from __future__ import annotations

from enum import Enum, auto

import tcod.console
import tcod.event
from tcod.event import KeySym

from src.systems.render import MESSAGE_LOG_BACKGROUND
from src.text import cp437_safe
from src.ui.help_overlay import (
    HELP_BODY_FG,
    HELP_FOOTER_FG,
    HELP_OVERLAY_FOOTER,
    HELP_SECTION_FG,
    HELP_TITLE_FG,
    HelpTextLine,
)

CREDITS_TITLE = "Velociraptor Hunt"


class CreditsAction(Enum):
    """Outcome of credits screen input."""

    NONE = auto()
    BACK = auto()


def credits_display_lines() -> tuple[HelpTextLine, ...]:
    """Curated credits rows for proportional or CP437 rendering."""
    body = HELP_BODY_FG
    section = HELP_SECTION_FG
    return (
        HelpTextLine(CREDITS_TITLE, HELP_TITLE_FG),
        HelpTextLine("", body),
        HelpTextLine("Credits", section),
        HelpTextLine("K.D. — Curator of Voracious Beasts", body),
        HelpTextLine("", body),
        HelpTextLine("Links", section),
        HelpTextLine("patreon.com/KD_Dragon", body),
        HelpTextLine("furaffinity.net/user/kd", body),
        HelpTextLine("", body),
        HelpTextLine("Fonts", section),
        HelpTextLine("Source Sans 3 (data/fonts/SourceSans3-Regular.ttf)", body),
        HelpTextLine("Licensed under the SIL Open Font License 1.1", body),
        HelpTextLine("CP437 tile font via libtcod (map, sidebar, menu title)", body),
        HelpTextLine("", body),
        HelpTextLine("Libraries", section),
        HelpTextLine("Python 3.11+ — PSF License Agreement", body),
        HelpTextLine("libtcod / tcod (>=16.0) — BSD 3-Clause License", body),
        HelpTextLine("tcod-ecs (>=5.0) — MIT License", body),
        HelpTextLine("numpy (>=1.26) — BSD License", body),
        HelpTextLine("Pillow (>=10.0) — HPND License", body),
        HelpTextLine("attrs — MIT License (transitive dependency)", body),
    )


CREDITS_LINES: tuple[str, ...] = tuple(
    line.text for line in credits_display_lines() if line.text
)


def handle_credits_event(event: tcod.event.Event) -> CreditsAction:
    """Handle credits screen input."""
    if isinstance(event, tcod.event.KeyDown) and event.sym == KeySym.ESCAPE:
        return CreditsAction.BACK
    return CreditsAction.NONE


def render_credits_screen(console: tcod.console.Console) -> None:
    """Draw the full-screen credits page on the root console (CP437 fallback)."""
    console.clear(bg=MESSAGE_LOG_BACKGROUND)
    max_inner = max(1, console.width - 2)
    row_index = 0
    for line in credits_display_lines():
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