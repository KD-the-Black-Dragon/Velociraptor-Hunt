"""First-run welcome screen asking whether the player wants the tutorial."""

from __future__ import annotations

from enum import Enum, auto

import attrs
import numpy as np
import tcod.console
import tcod.event
import tcod.sdl.render
from PIL import Image, ImageDraw, ImageFont
from tcod.event import KeySym

from src.input_handlers import MODAL_ADVANCE_KEYS
from src.systems.render import MESSAGE_LOG_BACKGROUND
from src.text import cp437_safe
from src.ui.layout import UILayout
from src.ui.proportional_log import (
    line_height_px,
    measure_text,
    overlay_panel_pixel_size,
)

WELCOME_LINE_1 = "Welcome to Velociraptor Hunt."
WELCOME_LINE_2 = "Would you like a tutorial?"
TUTORIAL_OPTION_YES = "Yes, please!"
TUTORIAL_OPTION_NO = "No, I'm good."
TUTORIAL_OPTIONS: tuple[str, ...] = (TUTORIAL_OPTION_YES, TUTORIAL_OPTION_NO)
TUTORIAL_PROMPT_NAV_HINT = "Up/Down to choose, Enter to confirm"
TUTORIAL_DECLINED_NOTICE = (
    "If you change your mind, select 'Tutorial' in the Options menu."
)

_PROMPT_NAV_UP: frozenset[KeySym] = frozenset({
    KeySym.UP,
    KeySym.KP_8,
})
_PROMPT_NAV_DOWN: frozenset[KeySym] = frozenset({
    KeySym.DOWN,
    KeySym.KP_2,
})

PROMPT_TITLE_FG = (255, 255, 255)
PROMPT_BODY_FG = (210, 210, 210)
PROMPT_OPTION_FG = (140, 140, 140)
PROMPT_OPTION_SELECTED_FG = (255, 255, 200)
PROMPT_OPTION_SELECTED_BG = (72, 64, 24)
PROMPT_HINT_FG = (120, 120, 120)


class TutorialPromptAction(Enum):
    """Outcome of first-run tutorial prompt input."""

    NONE = auto()
    YES = auto()
    NO = auto()


@attrs.define
class TutorialPromptState:
    """Selection for the first-run tutorial prompt; nothing selected at start."""

    highlight: int | None = None

    def move_up(self) -> None:
        if self.highlight is None:
            self.highlight = len(TUTORIAL_OPTIONS) - 1
        else:
            self.highlight = (self.highlight - 1) % len(TUTORIAL_OPTIONS)

    def move_down(self) -> None:
        if self.highlight is None:
            self.highlight = 0
        else:
            self.highlight = (self.highlight + 1) % len(TUTORIAL_OPTIONS)

    @property
    def highlighted_option(self) -> str | None:
        if self.highlight is None:
            return None
        return TUTORIAL_OPTIONS[self.highlight]


def handle_tutorial_prompt_event(
    state: TutorialPromptState,
    event: tcod.event.Event,
) -> TutorialPromptAction:
    """Process one event on the first-run tutorial prompt."""
    if not isinstance(event, tcod.event.KeyDown):
        return TutorialPromptAction.NONE

    sym = event.sym
    if sym in _PROMPT_NAV_UP:
        state.move_up()
        return TutorialPromptAction.NONE
    if sym in _PROMPT_NAV_DOWN:
        state.move_down()
        return TutorialPromptAction.NONE
    if sym in MODAL_ADVANCE_KEYS and state.highlight is not None:
        if state.highlighted_option == TUTORIAL_OPTION_YES:
            return TutorialPromptAction.YES
        return TutorialPromptAction.NO
    return TutorialPromptAction.NONE


def _centered_x(console: tcod.console.Console, text: str) -> int:
    return max(0, (console.width - len(cp437_safe(text))) // 2)


def _option_line(index: int, *, selected: bool) -> str:
    prefix = "> " if selected else "  "
    return f"{prefix}{TUTORIAL_OPTIONS[index]}"


def render_tutorial_prompt(console: tcod.console.Console, state: TutorialPromptState) -> None:
    """Draw the first-run tutorial prompt (CP437 fallback)."""
    console.clear(bg=MESSAGE_LOG_BACKGROUND)
    center_y = console.height // 2
    console.print(
        _centered_x(console, WELCOME_LINE_1),
        center_y - 5,
        cp437_safe(WELCOME_LINE_1),
        fg=PROMPT_TITLE_FG,
    )
    console.print(
        _centered_x(console, WELCOME_LINE_2),
        center_y - 3,
        cp437_safe(WELCOME_LINE_2),
        fg=PROMPT_BODY_FG,
    )

    options_start_y = center_y + 1
    for index, _option in enumerate(TUTORIAL_OPTIONS):
        selected = state.highlight == index
        line = _option_line(index, selected=selected)
        x = _centered_x(console, line)
        y = options_start_y + index
        if selected:
            bg = PROMPT_OPTION_SELECTED_BG
            fg = PROMPT_OPTION_SELECTED_FG
            for col_offset, ch in enumerate(cp437_safe(line)):
                if x + col_offset >= console.width:
                    break
                console.print(x + col_offset, y, ch, fg=fg, bg=bg)
        else:
            console.print(x, y, cp437_safe(line), fg=PROMPT_OPTION_FG)

    hint_y = options_start_y + len(TUTORIAL_OPTIONS) + 2
    console.print(
        _centered_x(console, TUTORIAL_PROMPT_NAV_HINT),
        hint_y,
        cp437_safe(TUTORIAL_PROMPT_NAV_HINT),
        fg=PROMPT_HINT_FG,
    )


def render_proportional_tutorial_prompt_image(
    state: TutorialPromptState,
    *,
    font: ImageFont.FreeTypeFont,
    layout: UILayout,
) -> Image.Image:
    """Rasterize the first-run tutorial prompt with the log proportional font."""
    panel_w, panel_h = overlay_panel_pixel_size(layout)
    image = Image.new("RGBA", (panel_w, panel_h), (*MESSAGE_LOG_BACKGROUND, 255))
    draw = ImageDraw.Draw(image)
    row_h = line_height_px(font)
    center_y = panel_h // 2

    def _draw_centered(text: str, y: float, fg: tuple[int, int, int]) -> None:
        text_w = measure_text(font, text)
        x = max(0.0, (panel_w - text_w) / 2)
        draw.text((x, y), text, font=font, fill=(*fg, 255))

    _draw_centered(WELCOME_LINE_1, center_y - row_h * 5, PROMPT_TITLE_FG)
    _draw_centered(WELCOME_LINE_2, center_y - row_h * 3, PROMPT_BODY_FG)

    options_start_y = center_y + row_h
    pad_x = 12
    for index, option in enumerate(TUTORIAL_OPTIONS):
        selected = state.highlight == index
        prefix = "> " if selected else "  "
        line = f"{prefix}{option}"
        text_w = measure_text(font, line)
        x = max(0.0, (panel_w - text_w) / 2)
        y = options_start_y + index * row_h
        if selected:
            box_w = text_w + pad_x * 2
            box_x = max(0.0, (panel_w - box_w) / 2)
            draw.rectangle(
                (box_x, y - 2, box_x + box_w, y + row_h + 1),
                fill=(*PROMPT_OPTION_SELECTED_BG, 255),
            )
            draw.text((x, y), line, font=font, fill=(*PROMPT_OPTION_SELECTED_FG, 255))
        else:
            draw.text((x, y), line, font=font, fill=(*PROMPT_OPTION_FG, 255))

    hint_y = options_start_y + len(TUTORIAL_OPTIONS) * row_h + row_h * 2
    _draw_centered(TUTORIAL_PROMPT_NAV_HINT, hint_y, PROMPT_HINT_FG)
    return image


def render_proportional_tutorial_prompt_texture(
    renderer: tcod.sdl.render.Renderer,
    state: TutorialPromptState,
    *,
    font: ImageFont.FreeTypeFont,
    layout: UILayout,
) -> tcod.sdl.render.Texture:
    """Upload the proportional tutorial prompt as an SDL texture."""
    image = render_proportional_tutorial_prompt_image(
        state,
        font=font,
        layout=layout,
    )
    pixels = np.asarray(image, dtype=np.uint8)
    return renderer.upload_texture(pixels)