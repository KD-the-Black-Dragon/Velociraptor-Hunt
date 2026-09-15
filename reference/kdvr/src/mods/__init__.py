"""Official JSON mod discovery, load-order state, and layered data load.

Import submodules directly when possible (e.g. ``src.mods.fingerprint``) to avoid
heavy package import cycles at startup.
"""

from __future__ import annotations

from src.mods.discovery import discover_mods, enabled_mods_in_load_order
from src.mods.fingerprint import (
    LOAD_MODS_MISMATCH_MESSAGE,
    current_enabled_in_order,
    encode_mods_fingerprint,
    format_loaded_mods_for_crash,
    save_mods_compatible,
)
from src.mods.state import MOD_STATE_FILENAME, ModInfo, format_mod_state, parse_mod_state_text

__all__ = [
    "LOAD_MODS_MISMATCH_MESSAGE",
    "MOD_STATE_FILENAME",
    "ModInfo",
    "current_enabled_in_order",
    "discover_mods",
    "enabled_mods_in_load_order",
    "encode_mods_fingerprint",
    "format_loaded_mods_for_crash",
    "format_mod_state",
    "parse_mod_state_text",
    "save_mods_compatible",
]
