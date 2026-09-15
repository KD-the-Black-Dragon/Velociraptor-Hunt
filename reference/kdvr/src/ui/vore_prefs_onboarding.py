"""First-run vore preference selection screen."""

from __future__ import annotations

from enum import Enum, auto

import attrs
import numpy as np
import tcod.console
import tcod.event
import tcod.sdl.render
from PIL import Image, ImageDraw, ImageFont
from tcod.event import KeySym

from src.constants import VoreContentPreferences
from src.input_handlers import MODAL_ADVANCE_KEYS
from src.options_menu import VORE_OPTION_ROWS, try_toggle_vore_type
from src.settings_store import SettingsStore
from src.systems.render import MESSAGE_LOG_BACKGROUND
from src.text import cp437_safe
from src.ui.layout import UILayout
from src.ui.proportional_log import (
    line_height_px,
    measure_text,
    overlay_panel_pixel_size,
)

VORE_PREFS_INTRO = "Choose which vore types can appear in your run."
VORE_PREFS_CONFIRM_LABEL = "These settings are correct!"
VORE_PREFS_NAV_HINT = "Up/Down to choose, Left/Right or Enter to toggle, Enter to confirm"

CONFIRM_ROW_INDEX = len(VORE_OPTION_ROWS)
CONFIRM_ROW_GAP = 1

_NAV_UP: frozenset[KeySym] = frozenset({KeySym.UP, KeySym.KP_8})
_NAV_DOWN: frozenset[KeySym] = frozenset({KeySym.DOWN, KeySym.KP_2})
_TOGGLE: frozenset[KeySym] = frozenset({
    KeySym.LEFT,
    KeySym.RIGHT,
    KeySym.KP_4,
    KeySym.KP_6,
})

TITLE_FG = (255, 220, 120)
ROW_FG = (140, 140, 140)
ROW_SELECTED_FG = (255, 255, 220)
ROW_SELECTED_BG = (72, 64, 24)
HINT_FG = (100, 100, 100)


class VorePrefsOnboardingAction(Enum):
    """Outcome of vore prefs onboarding input."""

    NONE = auto()
    CONFIRMED = auto()


@attrs.define
class VorePrefsOnboardingState:
    """Highlight for vore onboarding; nothing selected at start."""

    highlight: int | None = None

    def move_up(self) -> None:
        row_count = CONFIRM_ROW_INDEX + 1
        if self.highlight is None:
            self.highlight = row_count - 1
        else:
            self.highlight = (self.highlight - 1) % row_count

    def move_down(self) -> None:
        row_count = CONFIRM_ROW_INDEX + 1
        if self.highlight is None:
            self.highlight = 0
        else:
            self.highlight = (self.highlight + 1) % row_count

    @property
    def on_confirm_row(self) -> bool:
        return self.highlight == CONFIRM_ROW_INDEX


def handle_vore_prefs_onboarding_event(
    state: VorePrefsOnboardingState,
    event: tcod.event.Event,
    *,
    settings: SettingsStore,
) -> VorePrefsOnboardingAction:
    """Process one event on the vore prefs onboarding screen."""
    if not isinstance(event, tcod.event.KeyDown):
        return VorePrefsOnboardingAction.NONE

    sym = event.sym
    if sym in _NAV_UP:
        state.move_up()
        return VorePrefsOnboardingAction.NONE
    if sym in _NAV_DOWN:
        state.move_down()
        return VorePrefsOnboardingAction.NONE
    if state.highlight is None:
        return VorePrefsOnboardingAction.NONE
    if sym in _TOGGLE or sym in MODAL_ADVANCE_KEYS:
        if state.on_confirm_row and sym in MODAL_ADVANCE_KEYS:
            return VorePrefsOnboardingAction.CONFIRMED
        if state.on_confirm_row:
            return VorePrefsOnboardingAction.NONE
        if state.highlight < len(VORE_OPTION_ROWS):
            code = VORE_OPTION_ROWS[state.highlight][1]
            new_prefs = try_toggle_vore_type(settings.vore_content, code)
            if new_prefs is not settings.vore_content:
                settings.set_vore_content(new_prefs)
    return VorePrefsOnboardingAction.NONE


def _on_off_label(prefs: VoreContentPreferences, code: str) -> str:
    return "ON" if prefs.is_enabled(code) else "OFF"


def _centered_x(console: tcod.console.Console, text: str) -> int:
    return max(0, (console.width - len(cp437_safe(text))) // 2)


def _onboarding_row_y(start_y: int, row_index: int) -> int:
    """Row Y with an extra blank line before the confirm row."""
    gap = CONFIRM_ROW_GAP if row_index == CONFIRM_ROW_INDEX else 0
    return start_y + row_index + gap


def render_vore_prefs_onboarding(
    console: tcod.console.Console,
    state: VorePrefsOnboardingState,
    *,
    settings: SettingsStore,
) -> None:
    """Draw the first-run vore preferences screen (CP437 fallback)."""
    console.clear(bg=MESSAGE_LOG_BACKGROUND)
    center_y = console.height // 2
    title = "Vore Preferences"
    console.print(
        _centered_x(console, title),
        center_y - 8,
        cp437_safe(title),
        fg=TITLE_FG,
    )
    console.print(
        _centered_x(console, VORE_PREFS_INTRO),
        center_y - 6,
        cp437_safe(VORE_PREFS_INTRO)[: console.width - 2],
        fg=ROW_FG,
    )

    start_y = center_y - 3
    for index, (label, code) in enumerate(VORE_OPTION_ROWS):
        selected = state.highlight == index
        prefix = "> " if selected else "  "
        status = _on_off_label(settings.vore_content, code)
        line = f"{prefix}{label}:  {status}"
        x = _centered_x(console, line)
        y = start_y + index
        if selected:
            for col_offset, ch in enumerate(cp437_safe(line)):
                if x + col_offset >= console.width:
                    break
                console.print(
                    x + col_offset,
                    y,
                    ch,
                    fg=ROW_SELECTED_FG,
                    bg=ROW_SELECTED_BG,
                )
        else:
            console.print(x, y, cp437_safe(line), fg=ROW_FG)

    confirm_index = CONFIRM_ROW_INDEX
    selected = state.highlight == confirm_index
    prefix = "> " if selected else "  "
    confirm_line = f"{prefix}{VORE_PREFS_CONFIRM_LABEL}"
    x = _centered_x(console, confirm_line)
    y = _onboarding_row_y(start_y, confirm_index)
    if selected:
        for col_offset, ch in enumerate(cp437_safe(confirm_line)):
            if x + col_offset >= console.width:
                break
            console.print(
                x + col_offset,
                y,
                ch,
                fg=ROW_SELECTED_FG,
                bg=ROW_SELECTED_BG,
            )
    else:
        console.print(x, y, cp437_safe(confirm_line), fg=ROW_FG)

    hint_y = _onboarding_row_y(start_y, confirm_index) + 2
    console.print(
        _centered_x(console, VORE_PREFS_NAV_HINT),
        hint_y,
        cp437_safe(VORE_PREFS_NAV_HINT),
        fg=HINT_FG,
    )


def render_proportional_vore_prefs_image(
    state: VorePrefsOnboardingState,
    *,
    settings: SettingsStore,
    font: ImageFont.FreeTypeFont,
    layout: UILayout,
) -> Image.Image:
    """Rasterize vore prefs onboarding with the log proportional font."""
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

    title = "Vore Preferences"
    _draw_centered(title, center_y - row_h * 8, TITLE_FG)
    _draw_centered(VORE_PREFS_INTRO, center_y - row_h * 6, ROW_FG)

    start_y = center_y - row_h * 3
    rows: list[tuple[str, bool]] = []
    for label, code in VORE_OPTION_ROWS:
        status = _on_off_label(settings.vore_content, code)
        rows.append((f"{label}:  {status}", False))
    rows.append((VORE_PREFS_CONFIRM_LABEL, True))

    for index, (text, _is_confirm) in enumerate(rows):
        selected = state.highlight == index
        prefix = "> " if selected else "  "
        line = f"{prefix}{text}"
        text_w = measure_text(font, line)
        x = max(0.0, (panel_w - text_w) / 2)
        gap_rows = CONFIRM_ROW_GAP if index == CONFIRM_ROW_INDEX else 0
        y = start_y + index * row_h + gap_rows * row_h
        if selected:
            box_w = text_w + pad_x * 2
            box_x = max(0.0, (panel_w - box_w) / 2)
            draw.rectangle(
                (box_x, y - 2, box_x + box_w, y + row_h + 1),
                fill=(*ROW_SELECTED_BG, 255),
            )
            draw.text((x, y), line, font=font, fill=(*ROW_SELECTED_FG, 255))
        else:
            draw.text((x, y), line, font=font, fill=(*ROW_FG, 255))

    hint_y = start_y + len(rows) * row_h + CONFIRM_ROW_GAP * row_h + row_h * 2
    _draw_centered(VORE_PREFS_NAV_HINT, hint_y, HINT_FG)
    return image


def render_proportional_vore_prefs_texture(
    renderer: tcod.sdl.render.Renderer,
    state: VorePrefsOnboardingState,
    *,
    settings: SettingsStore,
    font: ImageFont.FreeTypeFont,
    layout: UILayout,
) -> tcod.sdl.render.Texture:
    """Upload proportional vore prefs onboarding as an SDL texture."""
    image = render_proportional_vore_prefs_image(
        state,
        settings=settings,
        font=font,
        layout=layout,
    )
    pixels = np.asarray(image, dtype=np.uint8)
    return renderer.upload_texture(pixels)