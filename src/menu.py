from __future__ import annotations

from enum import Enum, auto

import attrs
import tcod.console
import tcod.event
from tcod.event import KeySym, Modifier

from src.input_handlers import MODAL_ADVANCE_KEYS
from src.menu_title import TITLE_BANNER_HEIGHT, render_title_banner

_ALL_MENU_OPTION_LABELS: tuple[str, ...] = (
    "New Game",
    "Load Game",
    "Past Runs",
    "Options",
    "Credits",
    "Exit",
)

MENU_LINE_WIDTH = max(len(f"> {option}") for option in _ALL_MENU_OPTION_LABELS)

_MENU_NAV_UP: frozenset[KeySym] = frozenset({
    KeySym.UP,
    KeySym.KP_8,
})

_MENU_NAV_DOWN: frozenset[KeySym] = frozenset({
    KeySym.DOWN,
    KeySym.KP_2,
})


def build_menu_options(
    *,
    load_available: bool,
    past_runs_available: bool = False,
) -> tuple[str, ...]:
    """Build visible main-menu options (conditional Load Game and Past Runs)."""
    options: list[str] = ["New Game"]
    if load_available:
        options.append("Load Game")
    if past_runs_available:
        options.append("Past Runs")
    options.extend(["Options", "Credits", "Exit"])
    return tuple(options)


class MenuAction(Enum):
    """Outcome of main-menu input handling."""

    NONE = auto()
    NEW_GAME = auto()
    LOAD_GAME = auto()
    PAST_RUNS = auto()
    OPTIONS = auto()
    CREDITS = auto()
    EXIT = auto()


@attrs.define
class MainMenuState:
    """Highlight index for the root main menu."""

    options: tuple[str, ...] = attrs.field(
        factory=lambda: build_menu_options(load_available=True),
    )
    highlight: int = 0

    def move_up(self) -> None:
        self.highlight = (self.highlight - 1) % len(self.options)

    def move_down(self) -> None:
        self.highlight = (self.highlight + 1) % len(self.options)

    @property
    def highlighted_option(self) -> str:
        return self.options[self.highlight]


def is_ctrl_q(event: tcod.event.Event) -> bool:
    """True when the event is Ctrl+Q."""
    return (
        isinstance(event, tcod.event.KeyDown)
        and event.sym == KeySym.Q
        and bool(event.mod & Modifier.CTRL)
    )


def is_ctrl_s(event: tcod.event.Event) -> bool:
    """True when the event is Ctrl+S."""
    return (
        isinstance(event, tcod.event.KeyDown)
        and event.sym == KeySym.S
        and bool(event.mod & Modifier.CTRL)
    )


def is_ctrl_g(event: tcod.event.Event) -> bool:
    """True when the event is Ctrl+G."""
    return (
        isinstance(event, tcod.event.KeyDown)
        and event.sym == KeySym.G
        and bool(event.mod & Modifier.CTRL)
    )


def is_ctrl_b(event: tcod.event.Event) -> bool:
    """True when the event is Ctrl+B."""
    return (
        isinstance(event, tcod.event.KeyDown)
        and event.sym == KeySym.B
        and bool(event.mod & Modifier.CTRL)
    )


def handle_main_menu_event(
    state: MainMenuState,
    event: tcod.event.Event,
) -> MenuAction:
    """Process one event on the main menu. Ctrl+Q is a no-op (returns NONE)."""
    if not isinstance(event, tcod.event.KeyDown):
        return MenuAction.NONE

    sym = event.sym
    if sym in _MENU_NAV_UP:
        state.move_up()
    elif sym in _MENU_NAV_DOWN:
        state.move_down()
    elif sym in MODAL_ADVANCE_KEYS:
        option = state.highlighted_option
        if option == "New Game":
            return MenuAction.NEW_GAME
        if option == "Load Game":
            return MenuAction.LOAD_GAME
        if option == "Past Runs":
            return MenuAction.PAST_RUNS
        if option == "Options":
            return MenuAction.OPTIONS
        if option == "Credits":
            return MenuAction.CREDITS
        if option == "Exit":
            return MenuAction.EXIT
    return MenuAction.NONE


def _menu_block_x(console: tcod.console.Console) -> int:
    """Left column for the options block so every row shares one anchor."""
    return max(0, (console.width - MENU_LINE_WIDTH) // 2)


def render_main_menu(console: tcod.console.Console, state: MainMenuState) -> None:
    """Draw the minimalist black title screen with centered title and bottom options."""
    console.clear()

    options_start_y = console.height - len(state.options) - 3
    title_y = max(2, (options_start_y - TITLE_BANNER_HEIGHT) // 2)
    render_title_banner(console, y=title_y, width=console.width)
    menu_x = _menu_block_x(console)
    for index, option in enumerate(state.options):
        prefix = "> " if index == state.highlight else "  "
        line = f"{prefix}{option}"
        fg = (255, 255, 220) if index == state.highlight else (140, 140, 140)
        console.print(menu_x, options_start_y + index, line, fg=fg)