from __future__ import annotations

import string
from typing import Final

from tcod.event import KeySym, Modifier

_ARROW_DIRECTION_KEYS: Final[dict[KeySym, tuple[int, int]]] = {
    KeySym.LEFT: (-1, 0),
    KeySym.RIGHT: (1, 0),
    KeySym.UP: (0, -1),
    KeySym.DOWN: (0, 1),
    KeySym.HOME: (-1, -1),
    KeySym.END: (-1, 1),
    KeySym.PAGEUP: (1, -1),
    KeySym.PAGEDOWN: (1, 1),
    KeySym.KP_4: (-1, 0),
    KeySym.KP_6: (1, 0),
    KeySym.KP_8: (0, -1),
    KeySym.KP_2: (0, 1),
    KeySym.KP_7: (-1, -1),
    KeySym.KP_1: (-1, 1),
    KeySym.KP_9: (1, -1),
    KeySym.KP_3: (1, 1),
}

# TYUGHJBNM keyboard layout (H is wait, not movement):
#   T U
#     Y
#   G H J
#     N
#   B M
# Uppercase letters avoid conflicting with inventory slots a-z.
_KEYBOARD_DIRECTION_KEYS: Final[dict[KeySym, tuple[int, int]]] = {
    KeySym.Y: (0, -1),
    KeySym.N: (0, 1),
    KeySym.G: (-1, 0),
    KeySym.J: (1, 0),
    KeySym.T: (-1, -1),
    KeySym.U: (1, -1),
    KeySym.B: (-1, 1),
    KeySym.M: (1, 1),
}

DIRECTION_KEYS: Final[dict[KeySym, tuple[int, int]]] = {
    **_ARROW_DIRECTION_KEYS,
    **_KEYBOARD_DIRECTION_KEYS,
}

WAIT_KEYS: Final[frozenset[KeySym]] = frozenset({
    KeySym.KP_5,
    KeySym.PERIOD,
    KeySym.H,
})

REST_UNTIL_KEY: Final[KeySym] = KeySym.N5

AUTOEXPLORE_KEY: Final[KeySym] = KeySym.GRAVE

# Main keyboard digit 1 only (not KP_1 / numpad southwest).
COME_HERE_KEY: Final[KeySym] = KeySym.N1

# DCSS-style descend: Shift+. produces `>` on US keyboards.
DESCEND_SHIFT_KEY: Final[KeySym] = KeySym.PERIOD
# Extra bindings for layouts where Shift+. / `>` is awkward or unavailable.
DESCEND_EXTRA_KEYS: Final[frozenset[KeySym]] = frozenset({
    KeySym.N0,
    KeySym.KP_0,
})
# Back-compat alias (Shift+. path still uses PERIOD).
DESCEND_KEY: Final[KeySym] = DESCEND_SHIFT_KEY

MODAL_ADVANCE_KEYS: Final[frozenset[KeySym]] = frozenset({
    KeySym.RETURN,
    KeySym.KP_ENTER,
})

CLOSE_DOOR_KEY: Final[KeySym] = getattr(KeySym, "c")
EXAMINE_KEY: Final[KeySym] = getattr(KeySym, "x")
INSPECT_INVENTORY_KEY: Final[KeySym] = getattr(KeySym, "i")
DROP_ITEM_KEY: Final[KeySym] = getattr(KeySym, "d")
DISMISS_ALLY_KEY: Final[KeySym] = getattr(KeySym, "d")
WIELD_WEAPON_KEY: Final[KeySym] = getattr(KeySym, "w")
WEAR_ARMOR_KEY: Final[KeySym] = getattr(KeySym, "w")
QUAFF_POTION_KEY: Final[KeySym] = getattr(KeySym, "q")
EVOKE_WAND_KEY: Final[KeySym] = getattr(KeySym, "v")
THROW_QUICK_KEY: Final[KeySym] = getattr(KeySym, "f")
THROW_PICK_KEY: Final[KeySym] = getattr(KeySym, "f")

INVENTORY_KEYS: Final[dict[KeySym, str]] = {
    getattr(KeySym, letter): letter for letter in string.ascii_lowercase
}

LOG_OVERLAY_LINE_UP_KEYS: Final[frozenset[KeySym]] = frozenset({
    KeySym.UP,
    KeySym.KP_8,
    KeySym.Y,
})

LOG_OVERLAY_LINE_DOWN_KEYS: Final[frozenset[KeySym]] = frozenset({
    KeySym.DOWN,
    KeySym.KP_2,
    KeySym.N,
})

LOG_OVERLAY_PAGE_UP_KEYS: Final[frozenset[KeySym]] = frozenset({
    KeySym.PAGEUP,
})

LOG_OVERLAY_PAGE_DOWN_KEYS: Final[frozenset[KeySym]] = frozenset({
    KeySym.PAGEDOWN,
})


def is_help_open_key(event: object) -> bool:
    """True when the event opens help (F1 or Shift+/ ``?``)."""
    from tcod.event import KeyDown

    return (
        isinstance(event, KeyDown)
        and (
            event.sym == KeySym.F1
            or event.sym == KeySym.QUESTION
            or (event.sym == KeySym.SLASH and bool(event.mod & Modifier.SHIFT))
        )
    )


def is_ctrl_p(event: object) -> bool:
    """True when the event is Ctrl+P (full message log overlay)."""
    from tcod.event import KeyDown

    return (
        isinstance(event, KeyDown)
        and event.sym == KeySym.P
        and bool(event.mod & Modifier.CTRL)
    )


def is_ctrl_direction(event: object) -> tuple[int, int] | None:
    """Return (dx, dy) when the event is Ctrl + a movement key, else None."""
    from tcod.event import KeyDown

    if not isinstance(event, KeyDown):
        return None
    if not (event.mod & Modifier.CTRL):
        return None
    return DIRECTION_KEYS.get(event.sym)