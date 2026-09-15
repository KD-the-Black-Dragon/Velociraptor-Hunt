"""PR6: save mod fingerprint, load gate, crash Loaded mods line."""

from __future__ import annotations

from pathlib import Path

import tcod.event
from tcod.event import KeySym, Scancode

import pytest

from src.app import AppPhase
from src.debug.context import build_crash_context

try:
    from src.engine import GameEngine
except ImportError:
    pytest.skip("GameEngine is not on the hunt product path", allow_module_level=True)
from src.mods.fingerprint import (
    LOAD_MODS_MISMATCH_MESSAGE,
    current_enabled_in_order,
    encode_mods_fingerprint,
    fingerprint_from_run,
    format_loaded_mods_for_crash,
    save_mods_compatible,
)
from src.mods.state import write_mod_state
from src.save.snapshot import build_run_snapshot
from tests.map_test_helpers import isolate_other_ais
from tests.save_test_helpers import app_with_isolated_save
from tests.ui_test_helpers import make_console


def _key(sym: KeySym) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=0)


def _mod(root: Path, name: str, *, order: int, enabled: bool = True) -> Path:
    path = root / name
    path.mkdir(parents=True, exist_ok=True)
    write_mod_state(path, enabled=enabled, order=order)
    return path


def test_fingerprint_from_run_missing_is_empty() -> None:
    assert fingerprint_from_run({}) == ()
    assert fingerprint_from_run({"mods": None}) == ()
    assert fingerprint_from_run({"mods": {"enabled_in_order": ["A", "B"]}}) == ("A", "B")


def test_current_enabled_in_order(tmp_path: Path) -> None:
    mods = tmp_path / "mods"
    _mod(mods, "Alpha", order=2)
    _mod(mods, "Bravo", order=1, enabled=False)
    _mod(mods, "Charlie", order=3)
    assert current_enabled_in_order(root=mods) == ("Alpha", "Charlie")


def test_save_mods_compatible(tmp_path: Path) -> None:
    mods = tmp_path / "mods"
    _mod(mods, "Solo", order=1)
    run = {"mods": encode_mods_fingerprint(root=mods)}
    assert save_mods_compatible(run, root=mods) is True
    run_pre_mod: dict = {}
    assert save_mods_compatible(run_pre_mod, root=mods) is False
    empty = tmp_path / "empty_mods"
    empty.mkdir()
    assert save_mods_compatible(run_pre_mod, root=empty) is True


def test_build_run_snapshot_includes_mods(tmp_path: Path, monkeypatch) -> None:
    mods = tmp_path / "mods"
    _mod(mods, "Pack", order=1)
    monkeypatch.setattr("src.user_data.MODS_DIR", mods)
    engine = GameEngine(player_name="Hero")
    isolate_other_ais(engine)
    snap = build_run_snapshot(engine)
    assert snap["mods"]["enabled_in_order"] == ["Pack"]


def test_format_loaded_mods_for_crash(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    assert format_loaded_mods_for_crash(root=empty) == "(none)"
    mods = tmp_path / "mods"
    _mod(mods, "A", order=1)
    _mod(mods, "B", order=2)
    assert format_loaded_mods_for_crash(root=mods) == "A, B"


def test_build_crash_context_lists_mods(tmp_path: Path, monkeypatch) -> None:
    mods = tmp_path / "mods"
    _mod(mods, "CrashMod", order=1)
    monkeypatch.setattr("src.user_data.MODS_DIR", mods)
    ctx = build_crash_context(None, RuntimeError("boom"))
    assert ctx.loaded_mods == "CrashMod"


def test_load_game_refuses_mod_mismatch(tmp_path: Path, monkeypatch) -> None:
    from src.save.snapshot import build_run_snapshot
    from src.save.store import SaveStore

    mods = tmp_path / "mods"
    mods.mkdir()
    monkeypatch.setattr("src.user_data.MODS_DIR", mods)

    # Save written with no mods (empty enabled list)
    engine = GameEngine(player_name="Saved")
    isolate_other_ais(engine)
    store = SaveStore(tmp_path / "saves")
    store.save_run(build_run_snapshot(engine))
    assert store.probe() is True

    # Enable a mod after the save was written
    _mod(mods, "NewMod", order=1)

    app = app_with_isolated_save(tmp_path)
    # Reuse the save we wrote into tmp_path/saves — app_with_isolated_save uses tmp_path/saves
    assert app.save_coordinator.store.probe() is True
    console = make_console()
    app.phase = AppPhase.MENU
    app._on_menu_enter()
    app._load_career_or_dungeon(console)

    assert app.phase is AppPhase.MENU
    assert app.engine is None
    assert app.load_game_error == LOAD_MODS_MISMATCH_MESSAGE
    assert app.save_coordinator.store.probe() is True  # save kept


def test_load_game_succeeds_when_mods_match(tmp_path: Path, monkeypatch) -> None:
    mods = tmp_path / "mods"
    _mod(mods, "MatchMe", order=1)
    monkeypatch.setattr("src.user_data.MODS_DIR", mods)

    engine = GameEngine(player_name="Saved")
    isolate_other_ais(engine)
    app = app_with_isolated_save(tmp_path)
    app.save_coordinator.store.save_run(build_run_snapshot(engine))

    console = make_console()
    app.phase = AppPhase.MENU
    app._on_menu_enter()
    app._load_career_or_dungeon(console)

    assert app.phase is AppPhase.PLAY
    assert app.engine is not None
    assert app.load_game_error is None
