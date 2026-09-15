from __future__ import annotations

from collections.abc import Callable
from enum import Enum, auto

import attrs
import tcod.console
import tcod.event
from tcod.event import KeySym

from src.constants import VoreContentPreferences
from src.difficulties import load_difficulties
from src.hunt_loss import (
    POST_SWALLOW_DIGEST,
    POST_SWALLOW_ENDOSOMA,
    normalize_post_swallow,
)
from src.input_handlers import MODAL_ADVANCE_KEYS
from src.settings_store import SettingsStore
from src.text import cp437_safe
from src.ui.layout import cycle_ui_preset, list_ui_preset_ids, ui_preset_display_label

VORE_OPTION_ROWS: tuple[tuple[str, str], ...] = (
    ("Oral Vore", "OV"),
    ("Cock Vore", "CV"),
    ("Anal Vore", "AV"),
)

UI_LAYOUT_ROW_INDEX = 0
DIFFICULTY_ROW_INDEX = UI_LAYOUT_ROW_INDEX + 1
POST_SWALLOW_ROW_INDEX = DIFFICULTY_ROW_INDEX + 1
FULLSCREEN_ROW_INDEX = POST_SWALLOW_ROW_INDEX + 1
TUTORIAL_ROW_INDEX = FULLSCREEN_ROW_INDEX + 1
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
    return 6


@attrs.define
class OptionsMenuState:
    """Highlight index for options rows (UI, difficulty, post-swallow, fullscreen, Mods)."""

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
    def on_post_swallow_row(self) -> bool:
        return self.highlight == POST_SWALLOW_ROW_INDEX

    @property
    def on_fullscreen_row(self) -> bool:
        return self.highlight == FULLSCREEN_ROW_INDEX

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


def _difficulty_ids() -> list[str]:
    cfg = load_difficulties()
    order = ("easier", "normal", "hard", "nightmare")
    ids = [i for i in order if i in cfg.by_id]
    for i in cfg.by_id:
        if i not in ids:
            ids.append(i)
    return ids or ["normal"]


def cycle_difficulty_id(current: str, *, step: int = 1) -> str:
    ids = _difficulty_ids()
    if current not in ids:
        return ids[0]
    idx = (ids.index(current) + step) % len(ids)
    return ids[idx]


def cycle_post_swallow(current: str, *, step: int = 1) -> str:
    ids = (POST_SWALLOW_DIGEST, POST_SWALLOW_ENDOSOMA)
    cur = normalize_post_swallow(current)
    idx = ids.index(cur)
    return ids[(idx + step) % len(ids)]


def format_post_swallow_line(value: str) -> str:
    """Format Post-swallow row; active stance is bracketed."""
    current = normalize_post_swallow(value)
    parts: list[str] = []
    for stance, label in (
        (POST_SWALLOW_DIGEST, "Digest"),
        (POST_SWALLOW_ENDOSOMA, "Endosoma"),
    ):
        parts.append(f"[{label}]" if stance == current else label)
    return f"Post-swallow:  {' ► '.join(parts)}"


def format_difficulty_line(difficulty_id: str) -> str:
    """Format difficulty row; active difficulty is bracketed."""
    cfg = load_difficulties()
    ids = _difficulty_ids()
    if len(ids) == 1:
        return f"Difficulty:  {cfg.get(ids[0]).label}"
    parts: list[str] = []
    for did in ids:
        label = cfg.get(did).label
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
        elif state.on_post_swallow_row:
            step = _ui_layout_toggle_step(sym)
            new_stance = cycle_post_swallow(settings.post_swallow, step=step)
            settings.set_post_swallow(new_stance)
        elif state.on_fullscreen_row:
            if toggle_fullscreen is not None:
                toggle_fullscreen()
            else:
                settings.window = attrs.evolve(
                    settings.window,
                    fullscreen=not settings.window.fullscreen,
                )
    return OptionsAction.NONE


def _centered_x(console: tcod.console.Console, text: str) -> int:
    return max(0, (console.width - len(text)) // 2)


def _on_off_label(prefs: VoreContentPreferences, code: str) -> str:
    return "ON" if prefs.is_enabled(code) else "OFF"


def render_options_menu(
    console: tcod.console.Console,
    state: OptionsMenuState,
    *,
    settings: SettingsStore,
) -> None:
    """Draw the options screen (UI, difficulty, post-swallow, fullscreen, Mods)."""
    console.clear()

    title = "Options"
    hint = "(Up/Down, Left/Right or Enter to change, Escape to back)"
    center_y = console.height // 2
    console.print(_centered_x(console, title), center_y - 8, cp437_safe(title), fg=(255, 220, 120))

    start_y = center_y - 5
    ui_index = UI_LAYOUT_ROW_INDEX
    ui_prefix = "> " if state.highlight == ui_index else "  "
    ui_line = f"{ui_prefix}{format_ui_layout_line(settings.ui_preset)}"
    ui_fg = (255, 255, 220) if state.highlight == ui_index else (140, 140, 140)
    console.print(
        _centered_x(console, ui_line),
        start_y + ui_index,
        cp437_safe(ui_line),
        fg=ui_fg,
    )

    diff_index = DIFFICULTY_ROW_INDEX
    diff_prefix = "> " if state.highlight == diff_index else "  "
    diff_line = f"{diff_prefix}{format_difficulty_line(settings.difficulty_id)}"
    diff_fg = (255, 255, 220) if state.highlight == diff_index else (140, 140, 140)
    console.print(
        _centered_x(console, diff_line),
        start_y + diff_index,
        cp437_safe(diff_line),
        fg=diff_fg,
    )

    post_index = POST_SWALLOW_ROW_INDEX
    post_prefix = "> " if state.highlight == post_index else "  "
    post_line = f"{post_prefix}{format_post_swallow_line(settings.post_swallow)}"
    post_fg = (255, 255, 220) if state.highlight == post_index else (140, 140, 140)
    console.print(
        _centered_x(console, post_line),
        start_y + post_index,
        cp437_safe(post_line),
        fg=post_fg,
    )

    fullscreen_index = FULLSCREEN_ROW_INDEX
    fullscreen_prefix = "> " if state.highlight == fullscreen_index else "  "
    fullscreen_line = f"{fullscreen_prefix}{format_fullscreen_line(settings.window.fullscreen)}"
    fullscreen_fg = (
        (255, 255, 220) if state.highlight == fullscreen_index else (140, 140, 140)
    )
    console.print(
        _centered_x(console, fullscreen_line),
        start_y + fullscreen_index,
        cp437_safe(fullscreen_line),
        fg=fullscreen_fg,
    )

    tutorial_index = TUTORIAL_ROW_INDEX
    tutorial_prefix = "> " if state.highlight == tutorial_index else "  "
    tutorial_line = f"{tutorial_prefix}Tutorial"
    tutorial_fg = (
        (255, 255, 220) if state.highlight == tutorial_index else (140, 140, 140)
    )
    console.print(
        _centered_x(console, tutorial_line),
        start_y + tutorial_index,
        cp437_safe(tutorial_line),
        fg=tutorial_fg,
    )

    mods_index = MODS_ROW_INDEX
    mods_prefix = "> " if state.highlight == mods_index else "  "
    mods_line = f"{mods_prefix}Mods..."
    mods_fg = (255, 255, 220) if state.highlight == mods_index else (140, 140, 140)
    console.print(
        _centered_x(console, mods_line),
        start_y + mods_index,
        cp437_safe(mods_line),
        fg=mods_fg,
    )

    console.print(
        _centered_x(console, hint),
        start_y + option_row_count() + 2,
        cp437_safe(hint),
        fg=(100, 100, 100),
    )
