"""Entity id entry for the secret 1v1 arena flow."""

from __future__ import annotations

import string
from enum import Enum, auto

import attrs
import tcod.console
import tcod.event
from tcod.event import KeySym, Modifier

from src.components import Alignment
from src.data.entity_loader import load_entity_registry
from src.data.entity_registry import EntityDefinition, EntityRegistry
from src.input_handlers import MODAL_ADVANCE_KEYS
from src.text import cp437_safe

ENTITY_ENTRY_MAX_LENGTH = 48
ENTITY_ENTRY_UNKNOWN = "Unknown entity id."
ENTITY_ENTRY_NOT_EVIL = "That entity is not Evil alignment."

_PRINTABLE_ASCII = frozenset(
    ch for ch in string.printable if ch not in "\t\n\r\x0b\x0c"
)
_ENTITY_ID_CHARS = frozenset(string.ascii_letters + string.digits + "_")

_EXCLUDED_KEYS: frozenset[KeySym] = frozenset({
    KeySym.RETURN,
    KeySym.KP_ENTER,
    KeySym.ESCAPE,
    KeySym.BACKSPACE,
    KeySym.TAB,
    KeySym.DELETE,
})


class EntityEntryAction(Enum):
    """Outcome of entity-entry input handling."""

    NONE = auto()
    CONFIRM = auto()
    CANCEL = auto()


@attrs.define
class EntityEntryState:
    """Single-line entity id buffer for arena starts."""

    buffer: str = ""
    error_message: str = ""

    def append(self, char: str) -> None:
        if len(self.buffer) >= ENTITY_ENTRY_MAX_LENGTH:
            return
        self.buffer += char

    def backspace(self) -> None:
        if self.buffer:
            self.buffer = self.buffer[:-1]
        self.error_message = ""


def evil_entity_ids(registry: EntityRegistry) -> tuple[str, ...]:
    """Sorted evil entity ids from the active registry."""
    return tuple(
        sorted(
            entity.id
            for entity in registry.entities
            if entity.alignment == Alignment.EVIL
        )
    )


def validate_entity_entry(
    raw: str,
    registry: EntityRegistry,
) -> tuple[EntityDefinition | None, str]:
    """Return ``(definition, error_message)``; definition set when valid."""
    entity_id = raw.strip()
    if not entity_id:
        return None, ENTITY_ENTRY_UNKNOWN
    by_id = registry.by_id()
    if entity_id not in by_id:
        return None, ENTITY_ENTRY_UNKNOWN
    definition = by_id[entity_id]
    if definition.alignment != Alignment.EVIL:
        return None, ENTITY_ENTRY_NOT_EVIL
    return definition, ""


def _char_from_keydown(event: tcod.event.KeyDown) -> str | None:
    sym = event.sym
    if sym in _EXCLUDED_KEYS:
        return None
    if KeySym.A <= sym <= KeySym.Z:
        ch = chr(sym)
        if event.mod & Modifier.SHIFT:
            return ch.upper()
        return ch.lower()
    if KeySym.N0 <= sym <= KeySym.N9:
        return chr(sym)
    if sym == KeySym.UNDERSCORE or (sym == KeySym.MINUS and event.mod & Modifier.SHIFT):
        return "_"
    if 32 <= sym <= 126:
        ch = chr(sym)
        if ch in _ENTITY_ID_CHARS:
            return ch
    return None


def handle_entity_entry_event(
    state: EntityEntryState,
    event: tcod.event.Event,
    *,
    registry: EntityRegistry | None = None,
) -> EntityEntryAction:
    """Process one event on the entity entry screen."""
    if not isinstance(event, tcod.event.KeyDown):
        return EntityEntryAction.NONE

    reg = registry if registry is not None else load_entity_registry()
    sym = event.sym
    if sym == KeySym.BACKSPACE:
        state.backspace()
    elif sym in MODAL_ADVANCE_KEYS:
        _, error = validate_entity_entry(state.buffer, reg)
        if error:
            state.error_message = error
            return EntityEntryAction.NONE
        state.error_message = ""
        return EntityEntryAction.CONFIRM
    elif sym == KeySym.ESCAPE:
        state.error_message = ""
        return EntityEntryAction.CANCEL
    else:
        ch = _char_from_keydown(event)
        if ch is not None:
            state.append(ch)
            state.error_message = ""
    return EntityEntryAction.NONE


def _render_three_column_list(
    console: tcod.console.Console,
    ids: tuple[str, ...],
    *,
    start_y: int,
    end_y: int,
) -> None:
    if not ids or end_y <= start_y:
        return
    columns = 3
    col_width = max(8, console.width // columns)
    rows_per_col = max(1, end_y - start_y)
    for index, entity_id in enumerate(ids):
        col = index // rows_per_col
        if col >= columns:
            break
        row = index % rows_per_col
        y = start_y + row
        x = col * col_width
        console.print(x + 1, y, cp437_safe(entity_id), fg=(120, 120, 120))


def render_entity_entry(
    console: tcod.console.Console,
    state: EntityEntryState,
    *,
    registry: EntityRegistry | None = None,
) -> None:
    """Draw entity id entry with a three-column evil-id reference list."""
    console.clear()
    reg = registry if registry is not None else load_entity_registry()
    ids = evil_entity_ids(reg)

    prompt = "Enter entity id:"
    hint = "(Enter to confirm, Escape to cancel)"
    entry = f"> {state.buffer}_"

    entry_y = console.height - 1
    hint_y = max(0, entry_y - 1)
    error_y = max(0, entry_y - 3)
    prompt_y = max(0, entry_y - 5)
    list_start_y = 1
    list_end_y = max(list_start_y, prompt_y - 1)

    _render_three_column_list(
        console,
        ids,
        start_y=list_start_y,
        end_y=list_end_y,
    )

    console.print(1, prompt_y, cp437_safe(prompt), fg=(255, 220, 120))
    console.print(1, entry_y, cp437_safe(entry), fg=(255, 255, 220))
    console.print(1, hint_y, cp437_safe(hint), fg=(140, 140, 140))
    if state.error_message:
        console.print(1, error_y, cp437_safe(state.error_message), fg=(255, 120, 120))