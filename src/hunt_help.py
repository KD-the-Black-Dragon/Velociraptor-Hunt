"""In-hunt help overlay (F1 / ?)."""

from __future__ import annotations

import tcod.console
import tcod.event
from tcod.event import KeySym

from src.input_handlers import is_help_open_key
from src.text import cp437_safe
from src.ui.help_overlay import (
    HELP_BODY_FG,
    HELP_FOOTER_FG,
    HELP_OVERLAY_FOOTER,
    HELP_SECTION_FG,
    HELP_TITLE_FG,
    HelpTextLine,
)
from src.systems.render import MESSAGE_LOG_BACKGROUND


def hunt_help_lines(*, training: bool = False) -> tuple[HelpTextLine, ...]:
    body = HELP_BODY_FG
    section = HELP_SECTION_FG
    lines = (
        HelpTextLine("Velociraptor Hunt", HELP_TITLE_FG),
        HelpTextLine("", body),
        HelpTextLine("Tank (numpad; letter cluster TYUGHJBNM / arrows)", section),
        HelpTextLine("8 / Y / Up - forward", body),
        HelpTextLine("2 / N / Down - back", body),
        HelpTextLine("7 / T / Home - rotate 45 left", body),
        HelpTextLine("9 / U / PageUp - rotate 45 right", body),
        HelpTextLine("4 / G / Left - rotate 90 left", body),
        HelpTextLine("6 / J / Right - rotate 90 right", body),
        HelpTextLine("Ctrl+4 / Ctrl+6 (or Ctrl+G / Ctrl+J) - sidestep", body),
        HelpTextLine(". / H / numpad 5 - wait", body),
        HelpTextLine("", body),
        HelpTextLine("Gait and aim", section),
        HelpTextLine("Q - quick (holds fatigue)", body),
        HelpTextLine("W - walk (recovers fatigue)", body),
        HelpTextLine("R - run (adds fatigue)", body),
        HelpTextLine("S - sneak (recovers fatigue)", body),
        HelpTextLine("A - pick a visible tile to aim; A again - deep aim", body),
        HelpTextLine("Ctrl+7 / Ctrl+9 - yaw aim (about 1/3 of the cone)", body),
        HelpTextLine("7/9/4/6 while aimed - drop aim and turn to that 45", body),
        HelpTextLine("D - stand down (drop aim; facing snaps to 45)", body),
        HelpTextLine("F - targeting; fire along facing; F or Enter fires; Esc aborts", body),
        HelpTextLine("The dart flies along the shot, then lands", body),
        HelpTextLine("", body),
        HelpTextLine("Meta", section),
        HelpTextLine("F1 or ? - this help", body),
        HelpTextLine("Esc - leave the hunt (or close this help)", body),
    )
    if training:
        lines = lines + (
            HelpTextLine("", body),
            HelpTextLine("Training", section),
            HelpTextLine("F2 - dummy commands and weapon", body),
        )
    return lines


def render_hunt_help(console: tcod.console.Console, *, training: bool = False) -> None:
    console.clear(bg=MESSAGE_LOG_BACKGROUND)
    max_inner = max(1, console.width - 2)
    row = 0
    for line in hunt_help_lines(training=training):
        if row >= console.height - 1:
            break
        if not line.text:
            row += 1
            continue
        console.print(1, row, cp437_safe(line.text)[:max_inner], fg=line.fg)
        row += 1
    footer = cp437_safe(HELP_OVERLAY_FOOTER)
    footer_x = max(1, (console.width - len(footer)) // 2)
    console.print(
        footer_x,
        console.height - 1,
        footer[: console.width - 2],
        fg=HELP_FOOTER_FG,
    )


def help_toggle_event(event: tcod.event.Event, *, help_open: bool) -> bool | None:
    """True = open, False = close, None = not a help key / not dismissing."""
    if help_open:
        if not isinstance(event, tcod.event.KeyDown):
            return None
        if event.sym == KeySym.ESCAPE or is_help_open_key(event):
            return False
        return None
    if is_help_open_key(event):
        return True
    return None
