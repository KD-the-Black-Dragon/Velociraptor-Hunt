"""Mod root path helpers."""

from __future__ import annotations

from pathlib import Path


def mods_root(root: Path | None = None) -> Path:
    """Return the mods directory (default: ``{user_data}/mods``)."""
    if root is not None:
        return root
    from src.user_data import MODS_DIR

    return MODS_DIR


def ensure_mods_root(root: Path | None = None) -> Path:
    """Create the mods directory if needed and return it."""
    path = mods_root(root)
    path.mkdir(parents=True, exist_ok=True)
    return path
