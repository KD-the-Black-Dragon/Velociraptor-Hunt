"""Background selection after name entry (career start stub)."""

from __future__ import annotations

from enum import Enum, auto

import attrs
import tcod.event
from tcod.event import KeySym

from src.backgrounds import BackgroundDef, load_backgrounds
from src.ui.help_overlay import (
    HELP_BODY_FG,
    HELP_FOOTER_FG,
    HELP_SECTION_FG,
    HELP_TITLE_FG,
    HelpTextLine,
)

_NAV_UP = frozenset({KeySym.UP, KeySym.KP_8})
_NAV_DOWN = frozenset({KeySym.DOWN, KeySym.KP_2})
_CONFIRM = frozenset({KeySym.RETURN, KeySym.KP_ENTER})
_BACK = frozenset({KeySym.ESCAPE})


class BackgroundPickAction(Enum):
    NONE = auto()
    CONFIRM = auto()
    BACK = auto()


@attrs.define
class BackgroundPickState:
    highlight: int = 0
    options: tuple[BackgroundDef, ...] = ()

    def __attrs_post_init__(self) -> None:
        if not self.options:
            self.options = load_backgrounds().backgrounds

    @property
    def selected(self) -> BackgroundDef | None:
        if not self.options:
            return None
        i = max(0, min(self.highlight, len(self.options) - 1))
        return self.options[i]


def handle_background_pick_event(
    state: BackgroundPickState,
    event: tcod.event.Event,
) -> BackgroundPickAction:
    if not isinstance(event, tcod.event.KeyDown):
        return BackgroundPickAction.NONE
    sym = event.sym
    n = len(state.options)
    if n <= 0:
        return BackgroundPickAction.BACK
    if sym in _NAV_UP:
        state.highlight = (state.highlight - 1) % n
    elif sym in _NAV_DOWN:
        state.highlight = (state.highlight + 1) % n
    elif sym in _BACK:
        return BackgroundPickAction.BACK
    elif sym in _CONFIRM:
        return BackgroundPickAction.CONFIRM
    return BackgroundPickAction.NONE


def background_pick_lines(state: BackgroundPickState) -> tuple[HelpTextLine, ...]:
    lines: list[HelpTextLine] = [
        HelpTextLine("CHOOSE BACKGROUND", HELP_TITLE_FG),
        HelpTextLine(
            "Flavor and starting purse only for now — long-term goals later.",
            HELP_BODY_FG,
        ),
        HelpTextLine("", HELP_BODY_FG),
    ]
    for i, b in enumerate(state.options):
        marker = ">" if i == state.highlight else " "
        fg = HELP_SECTION_FG if i == state.highlight else HELP_BODY_FG
        gold = b.starting_gold_bonus
        gold_s = f"+{gold}g" if gold >= 0 else f"{gold}g"
        ren = f"  renown +{b.starting_renown}" if b.starting_renown else ""
        lines.append(HelpTextLine(f"{marker} {b.name}  ({gold_s}{ren})", fg))
        if i == state.highlight:
            lines.append(HelpTextLine(f"    {b.blurb}", HELP_FOOTER_FG))
            if b.note:
                lines.append(HelpTextLine(f"    {b.note}", HELP_FOOTER_FG))
    return tuple(lines)


def background_pick_footer() -> str:
    return "Up/Down: move  |  Enter: choose  |  Esc: back"
