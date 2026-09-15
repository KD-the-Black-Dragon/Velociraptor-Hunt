"""UnReal World tank commands for the hunt."""

from __future__ import annotations

from enum import Enum, auto

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.input_handlers import WAIT_KEYS


class TankCommand(Enum):
    NONE = auto()
    FORWARD = auto()
    BACK = auto()
    ROTATE_45_LEFT = auto()
    ROTATE_45_RIGHT = auto()
    ROTATE_90_LEFT = auto()
    ROTATE_90_RIGHT = auto()
    SIDESTEP_LEFT = auto()
    SIDESTEP_RIGHT = auto()
    WAIT = auto()
    SET_QUICK = auto()
    SET_WALK = auto()
    SET_RUN = auto()
    SET_SNEAK = auto()
    AIM = auto()
    YAW_AIM_LEFT = auto()
    YAW_AIM_RIGHT = auto()
    STAND_DOWN = auto()
    OPEN_TARGETING = auto()
    LEAVE = auto()


_FORWARD = frozenset({KeySym.KP_8, KeySym.Y, KeySym.UP})
_BACK = frozenset({KeySym.KP_2, KeySym.N, KeySym.DOWN})
_ROT45_L = frozenset({KeySym.KP_7, KeySym.T, KeySym.HOME})
_ROT45_R = frozenset({KeySym.KP_9, KeySym.U, KeySym.PAGEUP})
_TURN_OR_SIDE_L = frozenset({KeySym.KP_4, KeySym.G, KeySym.LEFT})
_TURN_OR_SIDE_R = frozenset({KeySym.KP_6, KeySym.J, KeySym.RIGHT})
_CTRL = Modifier.LCTRL | Modifier.RCTRL


def _ctrl_held(event: tcod.event.KeyDown) -> bool:
    return bool(event.mod & _CTRL)


def _turn_or_side_left(event: tcod.event.KeyDown) -> bool:
    """Numpad 4 even when NumLock reports a digit (scancode KP_4, sym N4)."""
    return event.scancode == Scancode.KP_4 or event.sym in _TURN_OR_SIDE_L


def _turn_or_side_right(event: tcod.event.KeyDown) -> bool:
    """Numpad 6 even when NumLock reports a digit (scancode KP_6, sym N6)."""
    return event.scancode == Scancode.KP_6 or event.sym in _TURN_OR_SIDE_R


def parse_tank_command(event: tcod.event.Event) -> TankCommand:
    if not isinstance(event, tcod.event.KeyDown):
        return TankCommand.NONE
    if event.sym == KeySym.ESCAPE:
        return TankCommand.LEAVE
    if event.sym == KeySym.Q:
        return TankCommand.SET_QUICK
    if event.sym == KeySym.W:
        return TankCommand.SET_WALK
    if event.sym == KeySym.R:
        return TankCommand.SET_RUN
    if event.sym == KeySym.S:
        return TankCommand.SET_SNEAK
    if event.sym == KeySym.A:
        return TankCommand.AIM
    if event.sym == KeySym.D:
        return TankCommand.STAND_DOWN
    if event.sym == KeySym.F:
        return TankCommand.OPEN_TARGETING
    if event.sym in WAIT_KEYS:
        return TankCommand.WAIT
    ctrl = _ctrl_held(event)
    sym = event.sym
    if ctrl and (sym in _ROT45_L or event.scancode == Scancode.KP_7):
        return TankCommand.YAW_AIM_LEFT
    if ctrl and (sym in _ROT45_R or event.scancode == Scancode.KP_9):
        return TankCommand.YAW_AIM_RIGHT
    if sym in _FORWARD:
        return TankCommand.FORWARD
    if sym in _BACK:
        return TankCommand.BACK
    if sym in _ROT45_L:
        return TankCommand.ROTATE_45_LEFT
    if sym in _ROT45_R:
        return TankCommand.ROTATE_45_RIGHT
    if _turn_or_side_left(event):
        return TankCommand.SIDESTEP_LEFT if _ctrl_held(event) else TankCommand.ROTATE_90_LEFT
    if _turn_or_side_right(event):
        return TankCommand.SIDESTEP_RIGHT if _ctrl_held(event) else TankCommand.ROTATE_90_RIGHT
    return TankCommand.NONE
