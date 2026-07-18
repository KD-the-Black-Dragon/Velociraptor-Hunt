"""Save fingerprint: enabled mod names in load order must match for Load Game."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.mods.discovery import enabled_mods_in_load_order

LOAD_MODS_MISMATCH_MESSAGE = (
    "Cannot load saved game: mods do not match this save. "
    "Re-enable the same mods, or start a New Game."
)


def current_enabled_in_order(*, root: Path | None = None) -> tuple[str, ...]:
    """Enabled mod folder names in ascending load order."""
    return tuple(mod.name for mod in enabled_mods_in_load_order(root=root))


def encode_mods_fingerprint(*, root: Path | None = None) -> dict[str, list[str]]:
    """Payload fragment stored on the run snapshot."""
    return {"enabled_in_order": list(current_enabled_in_order(root=root))}


def fingerprint_from_run(run: dict[str, Any]) -> tuple[str, ...]:
    """Read fingerprint from a save run dict. Missing field = pre-modding (empty)."""
    mods = run.get("mods")
    if mods is None:
        return ()
    if not isinstance(mods, dict):
        return ()
    order = mods.get("enabled_in_order")
    if order is None:
        return ()
    if not isinstance(order, list):
        return ()
    names: list[str] = []
    for item in order:
        if not isinstance(item, str) or not item:
            return ()
        names.append(item)
    return tuple(names)


def save_mods_compatible(run: dict[str, Any], *, root: Path | None = None) -> bool:
    """True when the save's enabled-in-order list matches the live mod setup."""
    return fingerprint_from_run(run) == current_enabled_in_order(root=root)


def format_loaded_mods_for_crash(*, root: Path | None = None) -> str:
    """Crash-report line value: comma-separated names or ``(none)``."""
    names = current_enabled_in_order(root=root)
    if not names:
        return "(none)"
    return ", ".join(names)
