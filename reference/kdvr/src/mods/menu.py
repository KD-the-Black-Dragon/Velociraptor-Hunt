"""Options → Mods submenu: list, toggle enable, reorder load order."""

from __future__ import annotations

from enum import Enum, auto
from pathlib import Path

import attrs
import numpy as np
import tcod.console
import tcod.event
import tcod.sdl.render
from PIL import Image, ImageDraw, ImageFont
from tcod.event import KeySym

from src.input_handlers import MODAL_ADVANCE_KEYS
from src.mods.discovery import discover_mods
from src.mods.state import ModInfo, write_mod_state
from src.systems.render import MESSAGE_LOG_BACKGROUND
from src.text import cp437_safe
from src.ui.layout import UILayout
from src.ui.proportional_log import (
    line_height_px,
    measure_text,
    overlay_panel_pixel_size,
)

MODS_TITLE_FG = (255, 220, 120)
MODS_ROW_FG = (140, 140, 140)
MODS_ROW_SELECTED_FG = (255, 255, 220)
MODS_ROW_SELECTED_BG = (72, 64, 24)
MODS_HINT_FG = (100, 100, 100)
MODS_HINT = (
    "(Up/Down select, Left/Right or Enter toggle, "
    "PgUp/PgDn reorder, Escape back)"
)
MODS_EMPTY = "No mods found in the mods folder."

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
    center_y = console.height // 2
    console.print(
        _centered_x(console, title),
        max(1, center_y - 10),
        cp437_safe(title),
        fg=MODS_TITLE_FG,
    )

    if not state.mods:
        console.print(
            _centered_x(console, MODS_EMPTY),
            center_y,
            cp437_safe(MODS_EMPTY),
            fg=MODS_ROW_FG,
        )
    else:
        # Window around highlight if many mods
        max_visible = max(5, console.height - 12)
        start = 0
        if len(state.mods) > max_visible:
            start = max(
                0,
                min(state.highlight - max_visible // 2, len(state.mods) - max_visible),
            )
        visible = state.mods[start : start + max_visible]
        start_y = max(3, center_y - max_visible // 2)
        for offset, mod in enumerate(visible):
            index = start + offset
            line = format_mod_row(mod, highlighted=index == state.highlight)
            fg = MODS_ROW_SELECTED_FG if index == state.highlight else MODS_ROW_FG
            console.print(
                _centered_x(console, line),
                start_y + offset,
                cp437_safe(line),
                fg=fg,
            )

    console.print(
        _centered_x(console, MODS_HINT),
        console.height - 3,
        cp437_safe(MODS_HINT),
        fg=MODS_HINT_FG,
    )


def render_proportional_mods_image(
    state: ModsMenuState,
    *,
    font: ImageFont.FreeTypeFont,
    layout: UILayout,
) -> Image.Image:
    """Rasterize Mods list with the readable proportional log font."""
    panel_w, panel_h = overlay_panel_pixel_size(layout)
    image = Image.new("RGBA", (panel_w, panel_h), (*MESSAGE_LOG_BACKGROUND, 255))
    draw = ImageDraw.Draw(image)
    row_h = line_height_px(font)
    center_y = panel_h // 2
    pad_x = 12

    def _draw_centered(text: str, y: float, fg: tuple[int, int, int]) -> None:
        text_w = measure_text(font, text)
        x = max(0.0, (panel_w - text_w) / 2)
        draw.text((x, y), text, font=font, fill=(*fg, 255))

    _draw_centered("Mods", max(row_h, center_y - row_h * 10), MODS_TITLE_FG)

    if not state.mods:
        _draw_centered(MODS_EMPTY, center_y, MODS_ROW_FG)
    else:
        max_visible = max(5, int(panel_h / row_h) - 8)
        start = 0
        if len(state.mods) > max_visible:
            start = max(
                0,
                min(state.highlight - max_visible // 2, len(state.mods) - max_visible),
            )
        visible = state.mods[start : start + max_visible]
        start_y = max(row_h * 3, center_y - (len(visible) * row_h) / 2)
        for offset, mod in enumerate(visible):
            index = start + offset
            selected = index == state.highlight
            line = format_mod_row(mod, highlighted=selected)
            text_w = measure_text(font, line)
            x = max(0.0, (panel_w - text_w) / 2)
            y = start_y + offset * row_h
            if selected:
                box_w = text_w + pad_x * 2
                box_x = max(0.0, (panel_w - box_w) / 2)
                draw.rectangle(
                    (box_x, y - 2, box_x + box_w, y + row_h + 1),
                    fill=(*MODS_ROW_SELECTED_BG, 255),
                )
                draw.text((x, y), line, font=font, fill=(*MODS_ROW_SELECTED_FG, 255))
            else:
                draw.text((x, y), line, font=font, fill=(*MODS_ROW_FG, 255))

    _draw_centered(MODS_HINT, panel_h - row_h * 3, MODS_HINT_FG)
    return image


def render_proportional_mods_texture(
    renderer: tcod.sdl.render.Renderer,
    state: ModsMenuState,
    *,
    font: ImageFont.FreeTypeFont,
    layout: UILayout,
) -> tcod.sdl.render.Texture:
    image = render_proportional_mods_image(state, font=font, layout=layout)
    pixels = np.asarray(image, dtype=np.uint8)
    return renderer.upload_texture(pixels)
