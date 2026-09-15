"""Scan ``{user_data}/mods`` and repair per-folder ``mod.state`` files."""

from __future__ import annotations

from pathlib import Path

from src.mods.paths import ensure_mods_root
from src.mods.state import MOD_STATE_FILENAME, ModInfo, read_mod_state, write_mod_state


def list_mod_folders(root: Path) -> list[Path]:
    """Immediate subdirectories of *root*, sorted by name. Ignores loose files."""
    if not root.is_dir():
        return []
    folders = [p for p in root.iterdir() if p.is_dir()]
    folders.sort(key=lambda p: p.name.casefold())
    return folders


def discover_mods(root: Path | None = None) -> list[ModInfo]:
    """Discover mod folders, repair ``mod.state`` as needed, return all mods.

    Order of operations:
    1. Ensure mods root exists.
    2. Scan subfolders (ignore non-directories).
    3. Parse valid ``mod.state`` files; mark missing/malformed for repair.
    4. Assign Enabled + unique append orders for new/broken states
       (alphabetical ``1..N`` when no folder had a valid state).
    5. If any duplicate orders remain, renumber ``1..N`` by ``(order, name)``.
    6. Rewrite any state that differs on disk; return list sorted by ``(order, name)``.
    """
    mods_dir = ensure_mods_root(root)
    folders = list_mod_folders(mods_dir)
    if not folders:
        return []

    parsed: dict[str, tuple[bool, int] | None] = {}
    for folder in folders:
        parsed[folder.name] = read_mod_state(folder / MOD_STATE_FILENAME)

    valid_pairs = [pair for pair in parsed.values() if pair is not None]
    max_order = max((order for _, order in valid_pairs), default=0)

    needs_assign = sorted(
        (name for name, pair in parsed.items() if pair is None),
        key=str.casefold,
    )

    if not valid_pairs and needs_assign:
        for index, name in enumerate(needs_assign, start=1):
            parsed[name] = (True, index)
    else:
        next_order = max_order
        for name in needs_assign:
            next_order += 1
            parsed[name] = (True, next_order)

    provisional: list[ModInfo] = []
    for folder in folders:
        pair = parsed[folder.name]
        assert pair is not None
        enabled, order = pair
        provisional.append(
            ModInfo(name=folder.name, path=folder, enabled=enabled, order=order)
        )

    orders = [m.order for m in provisional]
    if len(orders) != len(set(orders)):
        provisional.sort(key=lambda m: (m.order, m.name.casefold()))
        provisional = [
            ModInfo(name=m.name, path=m.path, enabled=m.enabled, order=index)
            for index, m in enumerate(provisional, start=1)
        ]

    result: list[ModInfo] = []
    for mod in provisional:
        disk = read_mod_state(mod.state_path)
        if disk != (mod.enabled, mod.order):
            try:
                write_mod_state(mod.state_path, enabled=mod.enabled, order=mod.order)
            except OSError:
                pass
        result.append(mod)

    result.sort(key=lambda m: (m.order, m.name.casefold()))
    return result


def enabled_mods_in_load_order(
    mods: list[ModInfo] | None = None,
    *,
    root: Path | None = None,
) -> list[ModInfo]:
    """Enabled mods only, ascending load order (core still loads before these)."""
    all_mods = mods if mods is not None else discover_mods(root)
    return [m for m in all_mods if m.enabled]
