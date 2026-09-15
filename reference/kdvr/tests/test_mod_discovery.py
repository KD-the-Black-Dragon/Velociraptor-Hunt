"""PR1: mod folder discovery and mod.state repair (no content merge)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.mods.discovery import discover_mods, enabled_mods_in_load_order, list_mod_folders
from src.mods.state import (
    MOD_STATE_FILENAME,
    format_mod_state,
    parse_mod_state_text,
    read_mod_state,
    write_mod_state,
)
from src.user_data import MODS_DIR


def _mod_dir(root: Path, name: str) -> Path:
    path = root / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_mods_dir_is_under_user_data() -> None:
    from src.user_data import USER_DATA_DIR

    assert MODS_DIR == USER_DATA_DIR / "mods"


def test_parse_mod_state_valid() -> None:
    assert parse_mod_state_text("E 2\n") == (True, 2)
    assert parse_mod_state_text("d 10") == (False, 10)
    assert parse_mod_state_text("  e   3  \n") == (True, 3)


def test_parse_mod_state_rejects_malformed() -> None:
    assert parse_mod_state_text("") is None
    assert parse_mod_state_text("E\n") is None
    assert parse_mod_state_text("E 1\nextra\n") is None
    assert parse_mod_state_text("X 1\n") is None
    assert parse_mod_state_text("E 1.5\n") is None
    assert parse_mod_state_text("Enabled 1\n") is None
    assert parse_mod_state_text("E two\n") is None


def test_format_roundtrip() -> None:
    text = format_mod_state(enabled=False, order=7)
    assert parse_mod_state_text(text) == (False, 7)


def test_list_mod_folders_ignores_files(tmp_path: Path) -> None:
    _mod_dir(tmp_path, "Alpha")
    (tmp_path / "loose.txt").write_text("nope", encoding="utf-8")
    _mod_dir(tmp_path, "beta")
    names = [p.name for p in list_mod_folders(tmp_path)]
    assert names == ["Alpha", "beta"]


def test_discover_empty_root_creates_dir(tmp_path: Path) -> None:
    root = tmp_path / "mods"
    assert not root.exists()
    assert discover_mods(root) == []
    assert root.is_dir()


def test_first_discovery_assigns_alpha_enabled_orders(tmp_path: Path) -> None:
    _mod_dir(tmp_path, "Zebra")
    _mod_dir(tmp_path, "apple")
    _mod_dir(tmp_path, "Middle")

    mods = discover_mods(tmp_path)
    assert [m.name for m in mods] == ["apple", "Middle", "Zebra"]
    assert [m.order for m in mods] == [1, 2, 3]
    assert all(m.enabled for m in mods)
    for mod in mods:
        assert read_mod_state(mod.state_path) == (True, mod.order)


def test_missing_state_appends_after_existing(tmp_path: Path) -> None:
    a = _mod_dir(tmp_path, "alpha")
    write_mod_state(a, enabled=True, order=1)
    _mod_dir(tmp_path, "bravo")  # no state

    mods = discover_mods(tmp_path)
    by_name = {m.name: m for m in mods}
    assert by_name["alpha"].order == 1
    assert by_name["bravo"].enabled is True
    assert by_name["bravo"].order == 2
    assert read_mod_state(by_name["bravo"].state_path) == (True, 2)


def test_malformed_state_regenerated_enabled_append(tmp_path: Path) -> None:
    good = _mod_dir(tmp_path, "good")
    bad = _mod_dir(tmp_path, "bad")
    write_mod_state(good, enabled=False, order=5)
    (bad / MOD_STATE_FILENAME).write_text("garbage\n", encoding="utf-8")

    mods = discover_mods(tmp_path)
    by_name = {m.name: m for m in mods}
    assert by_name["good"].enabled is False
    assert by_name["good"].order == 5
    assert by_name["bad"].enabled is True
    assert by_name["bad"].order == 6
    assert read_mod_state(by_name["bad"].state_path) == (True, 6)


def test_duplicate_orders_renumber_stable(tmp_path: Path) -> None:
    a = _mod_dir(tmp_path, "alpha")
    b = _mod_dir(tmp_path, "bravo")
    c = _mod_dir(tmp_path, "charlie")
    write_mod_state(a, enabled=True, order=2)
    write_mod_state(b, enabled=False, order=2)
    write_mod_state(c, enabled=True, order=1)

    mods = discover_mods(tmp_path)
    # Sort key before renumber: (1, charlie), (2, alpha), (2, bravo) → 1,2,3
    assert [(m.name, m.order, m.enabled) for m in mods] == [
        ("charlie", 1, True),
        ("alpha", 2, True),
        ("bravo", 3, False),
    ]
    for mod in mods:
        assert read_mod_state(mod.state_path) == (mod.enabled, mod.order)


def test_valid_states_preserved_when_unique(tmp_path: Path) -> None:
    a = _mod_dir(tmp_path, "later")
    b = _mod_dir(tmp_path, "earlier")
    write_mod_state(a, enabled=True, order=10)
    write_mod_state(b, enabled=False, order=3)

    mods = discover_mods(tmp_path)
    assert [(m.name, m.order, m.enabled) for m in mods] == [
        ("earlier", 3, False),
        ("later", 10, True),
    ]


def test_enabled_mods_in_load_order(tmp_path: Path) -> None:
    a = _mod_dir(tmp_path, "a")
    b = _mod_dir(tmp_path, "b")
    c = _mod_dir(tmp_path, "c")
    write_mod_state(a, enabled=True, order=2)
    write_mod_state(b, enabled=False, order=1)
    write_mod_state(c, enabled=True, order=3)

    enabled = enabled_mods_in_load_order(root=tmp_path)
    assert [m.name for m in enabled] == ["a", "c"]


def test_discover_is_idempotent(tmp_path: Path) -> None:
    _mod_dir(tmp_path, "solo")
    first = discover_mods(tmp_path)
    second = discover_mods(tmp_path)
    assert [(m.name, m.enabled, m.order) for m in first] == [
        (m.name, m.enabled, m.order) for m in second
    ]
