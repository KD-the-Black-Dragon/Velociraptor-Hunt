"""Options → Mods submenu: list, toggle enable, reorder load order."""

from __future__ import annotations

from enum import Enum, auto
from pathlib import Path

import attrs
import tcod.console
import tcod.event
from tcod.event import KeySym

from src.input_handlers import MODAL_ADVANCE_KEYS
from src.mods.discovery import discover_mods
from src.mods.state import ModInfo, write_mod_state
from src.text import cp437_safe

_NAV_UP: frozenset[KeySym] = frozenset({KeySym.UP, KeySym.KP_8})
_NAV_DOWN: frozenset[KeySym] = frozenset({KeySym.DOWN, KeySym.KP_2})
_TOGGLE: frozenset[KeySym] = frozenset({
    KeySym.LEFT,
    KeySym.RIGHT,
    KeySym.KP_4,
    KeySym.KP_6,
})
_REORDER_UP: frozenset[KeySym] = frozenset({KeySym.PAGEUP, KeySym.KP_9})
_REORDER_DOWN: frozenset[KeySym] = frozenset({KeySym.PAGEDOWN, KeySym.KP_3})


class ModsMenuAction(Enum):
    NONE = auto()
    BACK = auto()


@attrs.define
class ModsMenuState:
    """Highlight + discovered mods for the Mods submenu."""

    mods: list[ModInfo] = attrs.Factory(list)
    highlight: int = 0
    mods_root: Path | None = None

    def refresh(self) -> None:
        """Re-scan disk and clamp highlight."""
        self.mods = list(discover_mods(self.mods_root))
        if not self.mods:
            self.highlight = 0
            return
        self.highlight = max(0, min(self.highlight, len(self.mods) - 1))

    def move_up(self) -> None:
        if not self.mods:
            return
        self.highlight = (self.highlight - 1) % len(self.mods)

    def move_down(self) -> None:
        if not self.mods:
            return
        self.highlight = (self.highlight + 1) % len(self.mods)

    def toggle_highlighted(self) -> None:
        if not self.mods:
            return
        mod = self.mods[self.highlight]
        write_mod_state(mod.path, enabled=not mod.enabled, order=mod.order)
        self.refresh()

    def reorder_highlighted(self, delta: int) -> None:
        """Move highlighted mod up (delta=-1) or down (delta=+1) in load order."""
        if not self.mods or delta == 0:
            return
        index = self.highlight
        target = index + delta
        if target < 0 or target >= len(self.mods):
            return
        ordered = list(self.mods)
        ordered[index], ordered[target] = ordered[target], ordered[index]
        for order, mod in enumerate(ordered, start=1):
            write_mod_state(mod.path, enabled=mod.enabled, order=order)
        self.highlight = target
        self.refresh()


def handle_mods_menu_event(
    state: ModsMenuState,
    event: tcod.event.Event,
) -> ModsMenuAction:
    if not isinstance(event, tcod.event.KeyDown):
        return ModsMenuAction.NONE

    sym = event.sym
    if sym == KeySym.ESCAPE:
        return ModsMenuAction.BACK
    if sym in _NAV_UP:
        state.move_up()
    elif sym in _NAV_DOWN:
        state.move_down()
    elif sym in _REORDER_UP:
        state.reorder_highlighted(-1)
    elif sym in _REORDER_DOWN:
        state.reorder_highlighted(1)
    elif sym in _TOGGLE or sym in MODAL_ADVANCE_KEYS:
        state.toggle_highlighted()
    return ModsMenuAction.NONE


def _centered_x(console: tcod.console.Console, text: str) -> int:
    return max(0, (console.width - len(text)) // 2)


def format_mod_row(mod: ModInfo, *, highlighted: bool) -> str:
    prefix = "> " if highlighted else "  "
    status = "Enabled" if mod.enabled else "Disabled"
    return f"{prefix}{mod.order}. {mod.name}  [{status}]"


def render_mods_menu(
    console: tcod.console.Console,
    state: ModsMenuState,
) -> None:
    """Draw the Mods list screen."""
    console.clear()
    title = "Mods"
    hint = (
        "(Up/Down select, Left/Right or Enter toggle, "
        "PgUp/PgDn reorder, Escape back)"
    )
    center_y = console.height // 2
    console.print(
        _centered_x(console, title),
        max(1, center_y - 10),
        cp437_safe(title),
        fg=(255, 220, 120),
    )

    if not state.mods:
        empty = "No mods found in the mods folder."
        console.print(
            _centered_x(console, empty),
            center_y,
            cp437_safe(empty),
            fg=(140, 140, 140),
        )
    else:
        # Window around highlight if many mods
        max_visible = max(5, console.height - 12)
        start = 0
        if len(state.mods) > max_visible:
            start = max(0, min(state.highlight - max_visible // 2, len(state.mods) - max_visible))
        visible = state.mods[start : start + max_visible]
        start_y = max(3, center_y - max_visible // 2)
        for offset, mod in enumerate(visible):
            index = start + offset
            line = format_mod_row(mod, highlighted=index == state.highlight)
            fg = (255, 255, 220) if index == state.highlight else (140, 140, 140)
            console.print(
                _centered_x(console, line),
                start_y + offset,
                cp437_safe(line),
                fg=fg,
            )

    console.print(
        _centered_x(console, hint),
        console.height - 3,
        cp437_safe(hint),
        fg=(100, 100, 100),
    )
