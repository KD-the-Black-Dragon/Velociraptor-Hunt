"""Weapon select after name entry (hunt start)."""

from __future__ import annotations

import json
from enum import Enum, auto
from pathlib import Path

import attrs
import tcod.event
from tcod.event import KeySym

from src.constants import DATA_DIR
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

HUNT_WEAPONS_PATH = DATA_DIR / "hunt_weapons.json"


@attrs.define(frozen=True)
class HuntWeaponDef:
    weapon_id: str
    name: str
    blurb: str


def load_hunt_weapons(path: Path | None = None) -> tuple[HuntWeaponDef, ...]:
    raw_path = path if path is not None else HUNT_WEAPONS_PATH
    data = json.loads(raw_path.read_text(encoding="utf-8"))
    weapons = data.get("weapons", []) if isinstance(data, dict) else data
    out: list[HuntWeaponDef] = []
    for item in weapons:
        if not isinstance(item, dict):
            continue
        wid = str(item.get("id", "")).strip()
        name = str(item.get("name", "")).strip()
        if not wid or not name:
            continue
        out.append(
            HuntWeaponDef(
                weapon_id=wid,
                name=name,
                blurb=str(item.get("blurb", "")).strip(),
            )
        )
    return tuple(out)


class WeaponSelectAction(Enum):
    NONE = auto()
    CONFIRM = auto()
    BACK = auto()


@attrs.define
class WeaponSelectState:
    highlight: int = 0
    options: tuple[HuntWeaponDef, ...] = ()

    def __attrs_post_init__(self) -> None:
        if not self.options:
            self.options = load_hunt_weapons()

    @property
    def selected(self) -> HuntWeaponDef | None:
        if not self.options:
            return None
        i = max(0, min(self.highlight, len(self.options) - 1))
        return self.options[i]


def handle_weapon_select_event(
    state: WeaponSelectState,
    event: tcod.event.Event,
) -> WeaponSelectAction:
    if not isinstance(event, tcod.event.KeyDown):
        return WeaponSelectAction.NONE
    sym = event.sym
    n = len(state.options)
    if n <= 0:
        return WeaponSelectAction.BACK
    if sym in _NAV_UP:
        state.highlight = (state.highlight - 1) % n
    elif sym in _NAV_DOWN:
        state.highlight = (state.highlight + 1) % n
    elif sym in _BACK:
        return WeaponSelectAction.BACK
    elif sym in _CONFIRM:
        return WeaponSelectAction.CONFIRM
    return WeaponSelectAction.NONE


def weapon_select_lines(state: WeaponSelectState) -> tuple[HelpTextLine, ...]:
    lines: list[HelpTextLine] = [
        HelpTextLine("CHOOSE WEAPON", HELP_TITLE_FG),
        HelpTextLine("Tranquilizers only. The raptor is under no such constraint.", HELP_BODY_FG),
        HelpTextLine("", HELP_BODY_FG),
    ]
    for i, w in enumerate(state.options):
        marker = ">" if i == state.highlight else " "
        fg = HELP_SECTION_FG if i == state.highlight else HELP_BODY_FG
        lines.append(HelpTextLine(f"{marker} {w.name}", fg))
        if i == state.highlight and w.blurb:
            lines.append(HelpTextLine(f"    {w.blurb}", HELP_FOOTER_FG))
    return tuple(lines)


def weapon_select_footer() -> str:
    return "Up/Down: move  |  Enter: choose  |  Esc: back"
