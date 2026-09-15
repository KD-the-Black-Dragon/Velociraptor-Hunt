from __future__ import annotations

from collections.abc import Callable
from enum import Enum, auto

import attrs
import numpy as np
import tcod.console
import tcod.event
import tcod.sdl.render
from PIL import Image, ImageDraw, ImageFont
from tcod.event import KeySym

from src.constants import VoreContentPreferences
from src.data.depth_scaling_config import cycle_difficulty_id, list_difficulty_ids
from src.data.depth_scaling_loader import default_depth_scaling_config
from src.input_handlers import MODAL_ADVANCE_KEYS
from src.settings_store import SettingsStore
from src.systems.render import MESSAGE_LOG_BACKGROUND
from src.text import cp437_safe
from src.ui.layout import UILayout, cycle_ui_preset, list_ui_preset_ids, ui_preset_display_label
from src.ui.proportional_log import (
    line_height_px,
    measure_text,
    overlay_panel_pixel_size,
)

OPTIONS_TITLE_FG = (255, 220, 120)
OPTIONS_ROW_FG = (140, 140, 140)
OPTIONS_ROW_SELECTED_FG = (255, 255, 220)
OPTIONS_ROW_SELECTED_BG = (72, 64, 24)
OPTIONS_HINT_FG = (100, 100, 100)
OPTIONS_HINT = "(Up/Down, Left/Right or Enter to change, Escape to back)"

VORE_OPTION_ROWS: tuple[tuple[str, str], ...] = (
    ("Oral Vore", "OV"),
    ("Cock Vore", "CV"),
    ("Anal Vore", "AV"),
)

UI_LAYOUT_ROW_INDEX = len(VORE_OPTION_ROWS)
DIFFICULTY_ROW_INDEX = UI_LAYOUT_ROW_INDEX + 1
FULLSCREEN_ROW_INDEX = DIFFICULTY_ROW_INDEX + 1
FOUR_K_SCALING_ROW_INDEX = FULLSCREEN_ROW_INDEX + 1
ALTERNATE_CV_ROW_INDEX = FOUR_K_SCALING_ROW_INDEX + 1
TUTORIAL_ROW_INDEX = ALTERNATE_CV_ROW_INDEX + 1
MODS_ROW_INDEX = TUTORIAL_ROW_INDEX + 1

_OPTIONS_NAV_UP: frozenset[KeySym] = frozenset({
    KeySym.UP,
    KeySym.KP_8,
})

_OPTIONS_NAV_DOWN: frozenset[KeySym] = frozenset({
    KeySym.DOWN,
    KeySym.KP_2,
})

_OPTIONS_TOGGLE: frozenset[KeySym] = frozenset({
    KeySym.LEFT,
    KeySym.RIGHT,
    KeySym.KP_4,
    KeySym.KP_6,
})

_OPTIONS_PREV: frozenset[KeySym] = frozenset({
    KeySym.LEFT,
    KeySym.KP_4,
})

_OPTIONS_NEXT: frozenset[KeySym] = frozenset({
    KeySym.RIGHT,
    KeySym.KP_6,
})


class OptionsAction(Enum):
    """Outcome of options-menu input handling."""

    NONE = auto()
    BACK = auto()
    OPEN_TUTORIAL = auto()
    OPEN_MODS = auto()


def option_row_count() -> int:
    return len(VORE_OPTION_ROWS) + 7


@attrs.define
class OptionsMenuState:
    """Highlight index for options rows (vore, UI, difficulty, display, Mods)."""

    highlight: int = 0

    def move_up(self) -> None:
        self.highlight = (self.highlight - 1) % option_row_count()

    def move_down(self) -> None:
        self.highlight = (self.highlight + 1) % option_row_count()

    @property
    def on_ui_layout_row(self) -> bool:
        return self.highlight == UI_LAYOUT_ROW_INDEX

    @property
    def on_difficulty_row(self) -> bool:
        return self.highlight == DIFFICULTY_ROW_INDEX

    @property
    def on_fullscreen_row(self) -> bool:
        return self.highlight == FULLSCREEN_ROW_INDEX

    @property
    def on_four_k_scaling_row(self) -> bool:
        return self.highlight == FOUR_K_SCALING_ROW_INDEX

    @property
    def on_alternate_cv_row(self) -> bool:
        return self.highlight == ALTERNATE_CV_ROW_INDEX

    @property
    def on_tutorial_row(self) -> bool:
        return self.highlight == TUTORIAL_ROW_INDEX

    @property
    def on_mods_row(self) -> bool:
        return self.highlight == MODS_ROW_INDEX

    @property
    def highlighted_code(self) -> str:
        return VORE_OPTION_ROWS[self.highlight][1]


def try_toggle_vore_type(prefs: VoreContentPreferences, code: str) -> VoreContentPreferences:
    """Toggle one narrative type; no-op when disabling the last enabled type."""
    enabled = set(prefs.enabled)
    if code in enabled:
        if len(enabled) <= 1:
            return prefs
        enabled.remove(code)
    else:
        enabled.add(code)
    return VoreContentPreferences(enabled=frozenset(enabled))


def _ui_layout_toggle_step(sym: KeySym) -> int:
    if sym in _OPTIONS_PREV:
        return -1
    return 1


def format_fullscreen_line(fullscreen: bool) -> str:
    """Format the fullscreen row as ``Fullscreen:  Off ► On`` with active bracketed."""
    if fullscreen:
        return "Fullscreen:  Off ► [On]"
    return "Fullscreen:  [Off] ► On"


def format_four_k_scaling_line(enabled: bool) -> str:
    """Format the 4K UI scaling row with active Off/On bracketed."""
    if enabled:
        return "4K UI scaling:  Off ► [On]  (F10 also toggles)"
    return "4K UI scaling:  [Off] ► On  (F10 also toggles)"


def format_alternate_cv_mechanics_line(enabled: bool) -> str:
    """Format Alternate CV Mechanics row with active No/Yes bracketed."""
    if enabled:
        return "Alternate CV Mechanics:  No ► [Yes]"
    return "Alternate CV Mechanics:  [No] ► Yes"


def format_ui_layout_line(preset_id: str) -> str:
    """Format the UI layout row; active preset is bracketed."""
    preset_ids = list_ui_preset_ids()
    if len(preset_ids) <= 1:
        return f"UI Layout:  {ui_preset_display_label(preset_id)}"
    parts: list[str] = []
    for pid in preset_ids:
        label = ui_preset_display_label(pid)
        parts.append(f"[{label}]" if pid == preset_id else label)
    return f"UI Layout:  {' ► '.join(parts)}"


def format_difficulty_line(difficulty_id: str) -> str:
    """Format difficulty row; active difficulty is bracketed."""
    config = default_depth_scaling_config()
    ids = list(list_difficulty_ids(config))
    if not ids:
        return "Difficulty:  Normal"
    if len(ids) == 1:
        profile = config.profile_for(ids[0])
        return f"Difficulty:  {profile.display_name}"
    parts: list[str] = []
    for did in ids:
        label = config.profile_for(did).display_name
        parts.append(f"[{label}]" if did == difficulty_id else label)
    return f"Difficulty:  {' ► '.join(parts)}"


def handle_options_event(
    state: OptionsMenuState,
    event: tcod.event.Event,
    *,
    settings: SettingsStore,
    toggle_fullscreen: Callable[[], None] | None = None,
) -> OptionsAction:
    """Process one event on the options screen."""
    if not isinstance(event, tcod.event.KeyDown):
        return OptionsAction.NONE

    sym = event.sym
    if sym in _OPTIONS_NAV_UP:
        state.move_up()
    elif sym in _OPTIONS_NAV_DOWN:
        state.move_down()
    elif sym == KeySym.ESCAPE:
        return OptionsAction.BACK
    elif sym in _OPTIONS_TOGGLE or sym in MODAL_ADVANCE_KEYS:
        if state.on_tutorial_row:
            return OptionsAction.OPEN_TUTORIAL
        if state.on_mods_row:
            return OptionsAction.OPEN_MODS
        if state.on_ui_layout_row:
            step = _ui_layout_toggle_step(sym)
            new_preset = cycle_ui_preset(settings.ui_preset, step=step)
            settings.set_ui_preset(new_preset)
        elif state.on_difficulty_row:
            step = _ui_layout_toggle_step(sym)
            new_id = cycle_difficulty_id(settings.difficulty_id, step=step)
            settings.set_difficulty_id(new_id)
        elif state.on_fullscreen_row:
            if toggle_fullscreen is not None:
                toggle_fullscreen()
            else:
                settings.window = attrs.evolve(
                    settings.window,
                    fullscreen=not settings.window.fullscreen,
                )
        elif state.on_four_k_scaling_row:
            settings.set_four_k_scaling(not settings.four_k_scaling)
        elif state.on_alternate_cv_row:
            settings.set_alternate_cv_mechanics(not settings.alternate_cv_mechanics)
        elif state.highlight < len(VORE_OPTION_ROWS):
            new_prefs = try_toggle_vore_type(settings.vore_content, state.highlighted_code)
            if new_prefs is not settings.vore_content:
                settings.set_vore_content(new_prefs)
    return OptionsAction.NONE


def _centered_x(console: tcod.console.Console, text: str) -> int:
    return max(0, (console.width - len(text)) // 2)


def _on_off_label(prefs: VoreContentPreferences, code: str) -> str:
    return "ON" if prefs.is_enabled(code) else "OFF"


def options_menu_row_labels(settings: SettingsStore) -> list[str]:
    """Plain row labels (no highlight prefix) in Options highlight order."""
    rows: list[str] = []
    for label, code in VORE_OPTION_ROWS:
        rows.append(f"{label}:  {_on_off_label(settings.vore_content, code)}")
    rows.append(format_ui_layout_line(settings.ui_preset))
    rows.append(format_difficulty_line(settings.difficulty_id))
    rows.append(format_fullscreen_line(settings.window.fullscreen))
    rows.append(format_four_k_scaling_line(settings.four_k_scaling))
    rows.append(format_alternate_cv_mechanics_line(settings.alternate_cv_mechanics))
    rows.append("Tutorial")
    rows.append("Mods...")
    return rows


def render_options_menu(
    console: tcod.console.Console,
    state: OptionsMenuState,
    *,
    settings: SettingsStore,
) -> None:
    """Draw the options screen (vore, UI, difficulty, display, Mods)."""
    console.clear()

    title = "Options"
    center_y = console.height // 2
    console.print(
        _centered_x(console, title),
        center_y - 9,
        cp437_safe(title),
        fg=OPTIONS_TITLE_FG,
    )

    start_y = center_y - 6
    for index, label in enumerate(options_menu_row_labels(settings)):
        prefix = "> " if index == state.highlight else "  "
        line = f"{prefix}{label}"
        fg = OPTIONS_ROW_SELECTED_FG if index == state.highlight else OPTIONS_ROW_FG
        console.print(_centered_x(console, line), start_y + index, cp437_safe(line), fg=fg)

    console.print(
        _centered_x(console, OPTIONS_HINT),
        start_y + option_row_count() + 2,
        cp437_safe(OPTIONS_HINT),
        fg=OPTIONS_HINT_FG,
    )


def render_proportional_options_image(
    state: OptionsMenuState,
    *,
    settings: SettingsStore,
    font: ImageFont.FreeTypeFont,
    layout: UILayout,
) -> Image.Image:
    """Rasterize Options with the readable proportional log font."""
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

    _draw_centered("Options", center_y - row_h * 9, OPTIONS_TITLE_FG)
    start_y = center_y - row_h * 6
    for index, label in enumerate(options_menu_row_labels(settings)):
        selected = index == state.highlight
        prefix = "> " if selected else "  "
        line = f"{prefix}{label}"
        text_w = measure_text(font, line)
        x = max(0.0, (panel_w - text_w) / 2)
        y = start_y + index * row_h
        if selected:
            box_w = text_w + pad_x * 2
            box_x = max(0.0, (panel_w - box_w) / 2)
            draw.rectangle(
                (box_x, y - 2, box_x + box_w, y + row_h + 1),
                fill=(*OPTIONS_ROW_SELECTED_BG, 255),
            )
            draw.text((x, y), line, font=font, fill=(*OPTIONS_ROW_SELECTED_FG, 255))
        else:
            draw.text((x, y), line, font=font, fill=(*OPTIONS_ROW_FG, 255))

    hint_y = start_y + option_row_count() * row_h + row_h * 2
    _draw_centered(OPTIONS_HINT, hint_y, OPTIONS_HINT_FG)
    return image


def render_proportional_options_texture(
    renderer: tcod.sdl.render.Renderer,
    state: OptionsMenuState,
    *,
    settings: SettingsStore,
    font: ImageFont.FreeTypeFont,
    layout: UILayout,
) -> tcod.sdl.render.Texture:
    image = render_proportional_options_image(
        state,
        settings=settings,
        font=font,
        layout=layout,
    )
    pixels = np.asarray(image, dtype=np.uint8)
    return renderer.upload_texture(pixels)
