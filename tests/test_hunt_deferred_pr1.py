"""PR1 (hunt-deferred): Ctrl+numpad sidestep (Shift is not a sidestep modifier)."""

from __future__ import annotations

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.hunt_input import TankCommand, parse_tank_command


def _key(
    sym: KeySym,
    *,
    ctrl: bool = False,
    shift: bool = False,
    num: bool = False,
    scancode: Scancode = Scancode.UNKNOWN,
) -> tcod.event.KeyDown:
    mod = Modifier.NONE
    if ctrl:
        mod |= Modifier.LCTRL
    if shift:
        mod |= Modifier.SHIFT
    if num:
        mod |= Modifier.NUM
    return tcod.event.KeyDown(sym=sym, scancode=scancode, mod=mod)


def test_ctrl_numpad_sidesteps() -> None:
    assert parse_tank_command(_key(KeySym.KP_4, ctrl=True, scancode=Scancode.KP_4)) is TankCommand.SIDESTEP_LEFT
    assert parse_tank_command(_key(KeySym.KP_6, ctrl=True, scancode=Scancode.KP_6)) is TankCommand.SIDESTEP_RIGHT


def test_ctrl_numpad_sidesteps_with_numlock_on() -> None:
    assert (
        parse_tank_command(_key(KeySym.KP_4, ctrl=True, num=True, scancode=Scancode.KP_4))
        is TankCommand.SIDESTEP_LEFT
    )
    assert (
        parse_tank_command(_key(KeySym.N4, ctrl=True, num=True, scancode=Scancode.KP_4))
        is TankCommand.SIDESTEP_LEFT
    )
    assert (
        parse_tank_command(_key(KeySym.KP_6, ctrl=True, num=True, scancode=Scancode.KP_6))
        is TankCommand.SIDESTEP_RIGHT
    )


def test_shift_numpad_is_not_sidestep() -> None:
    assert parse_tank_command(_key(KeySym.KP_4, shift=True, scancode=Scancode.KP_4)) is TankCommand.ROTATE_90_LEFT
    assert parse_tank_command(_key(KeySym.KP_6, shift=True, scancode=Scancode.KP_6)) is TankCommand.ROTATE_90_RIGHT
    assert parse_tank_command(_key(KeySym.G, shift=True)) is TankCommand.ROTATE_90_LEFT
    assert parse_tank_command(_key(KeySym.LEFT, shift=True)) is TankCommand.ROTATE_90_LEFT


def test_unshifted_numpad_turns_numlock_on_or_off() -> None:
    assert parse_tank_command(_key(KeySym.KP_4, scancode=Scancode.KP_4)) is TankCommand.ROTATE_90_LEFT
    assert parse_tank_command(_key(KeySym.N4, num=True, scancode=Scancode.KP_4)) is TankCommand.ROTATE_90_LEFT
    assert parse_tank_command(_key(KeySym.KP_4, num=True, scancode=Scancode.KP_4)) is TankCommand.ROTATE_90_LEFT
    assert parse_tank_command(_key(KeySym.LEFT, num=True, scancode=Scancode.KP_4)) is TankCommand.ROTATE_90_LEFT


def test_fallback_cluster_ctrl_sidestep() -> None:
    assert parse_tank_command(_key(KeySym.G, ctrl=True)) is TankCommand.SIDESTEP_LEFT
    assert parse_tank_command(_key(KeySym.J, ctrl=True)) is TankCommand.SIDESTEP_RIGHT
    assert parse_tank_command(_key(KeySym.LEFT, ctrl=True)) is TankCommand.SIDESTEP_LEFT
    assert parse_tank_command(_key(KeySym.RIGHT, ctrl=True)) is TankCommand.SIDESTEP_RIGHT


def test_main_keyboard_digit_ctrl_is_not_strafe() -> None:
    assert parse_tank_command(_key(KeySym.N4, ctrl=True, scancode=Scancode.N4)) is TankCommand.NONE
    assert parse_tank_command(_key(KeySym.N6, ctrl=True, scancode=Scancode.N6)) is TankCommand.NONE
