"""Per-mod ``mod.state`` read, write, and format helpers."""

from __future__ import annotations

from pathlib import Path

import attrs

MOD_STATE_FILENAME = "mod.state"


@attrs.define(frozen=True)
class ModInfo:
    """One discovered mod folder and its load-order state."""

    name: str
    path: Path
    enabled: bool
    order: int

    @property
    def state_path(self) -> Path:
        return self.path / MOD_STATE_FILENAME


def format_mod_state(*, enabled: bool, order: int) -> str:
    """Serialize enable flag and order to ``mod.state`` text."""
    flag = "E" if enabled else "D"
    return f"{flag} {order}\n"


def _is_plain_int_token(token: str) -> bool:
    if not token:
        return False
    if token[0] in "+-":
        return len(token) > 1 and token[1:].isdigit()
    return token.isdigit()


def parse_mod_state_text(text: str) -> tuple[bool, int] | None:
    """Parse ``mod.state`` body.

    Expected: exactly one non-empty line with two tokens — ``E``/``D``
    (case-insensitive) and an integer order. Otherwise ``None`` (caller repairs).
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if len(lines) != 1:
        return None
    parts = lines[0].split()
    if len(parts) != 2:
        return None
    flag_raw, order_raw = parts
    flag = flag_raw.upper()
    if flag not in {"E", "D"}:
        return None
    if not _is_plain_int_token(order_raw):
        return None
    return (flag == "E", int(order_raw))


def read_mod_state(path: Path) -> tuple[bool, int] | None:
    """Read and parse a ``mod.state`` file; ``None`` if missing or unreadable/malformed."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    return parse_mod_state_text(text)


def write_mod_state(path: Path, *, enabled: bool, order: int) -> None:
    """Write ``mod.state``; *path* may be the state file or the mod folder."""
    state_file = path if path.name == MOD_STATE_FILENAME else path / MOD_STATE_FILENAME
    state_file.write_text(format_mod_state(enabled=enabled, order=order), encoding="utf-8")
