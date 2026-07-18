"""PR3: Options → Mods UI, toggle/reorder, capital-Y save wipe gate."""

from __future__ import annotations

from pathlib import Path

import tcod.console
import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.app import AppPhase
from src.mods.confirm import (
    MODS_ENTER_PROMPT_LINES,
    ModsEnterConfirmAction,
    ModsEnterConfirmState,
    handle_mods_enter_confirm_event,
)
from src.mods.menu import (
    ModsMenuAction,
    ModsMenuState,
    format_mod_row,
    handle_mods_menu_event,
    render_mods_menu,
)
from src.mods.state import read_mod_state, write_mod_state
from src.options_menu import (
    MODS_ROW_INDEX,
    OptionsAction,
    OptionsMenuState,
    handle_options_event,
    render_options_menu,
)
from src.save.store import SaveStore
from src.settings_store import SettingsStore
from tests.save_test_helpers import app_with_isolated_save


def _key(sym: KeySym, *, shift: bool = False) -> tcod.event.KeyDown:
    mod = Modifier.SHIFT if shift else 0
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=mod)


def _mod_folder(root: Path, name: str, *, order: int, enabled: bool = True) -> Path:
    path = root / name
    path.mkdir(parents=True, exist_ok=True)
    write_mod_state(path, enabled=enabled, order=order)
    return path


def test_options_open_mods_action() -> None:
    state = OptionsMenuState(highlight=MODS_ROW_INDEX)
    settings = SettingsStore()
    assert handle_options_event(state, _key(KeySym.RETURN), settings=settings) is (
        OptionsAction.OPEN_MODS
    )


def test_render_options_shows_mods_row() -> None:
    console = tcod.console.Console(80, 42, order="F")
    render_options_menu(console, OptionsMenuState(), settings=SettingsStore())
    text = "".join(
        chr(int(console.rgba[x, y]["ch"])) if int(console.rgba[x, y]["ch"]) else " "
        for y in range(console.height)
        for x in range(console.width)
    )
    assert "Mods" in text


def test_toggle_enable_persists(tmp_path: Path) -> None:
    root = tmp_path / "mods"
    _mod_folder(root, "Alpha", order=1, enabled=True)
    state = ModsMenuState(mods_root=root)
    state.refresh()
    assert state.mods[0].enabled is True
    handle_mods_menu_event(state, _key(KeySym.RETURN))
    assert state.mods[0].enabled is False
    assert read_mod_state(root / "Alpha" / "mod.state") == (False, 1)


def test_reorder_page_down_swaps_order(tmp_path: Path) -> None:
    root = tmp_path / "mods"
    _mod_folder(root, "Alpha", order=1)
    _mod_folder(root, "Bravo", order=2)
    state = ModsMenuState(mods_root=root)
    state.refresh()
    assert [m.name for m in state.mods] == ["Alpha", "Bravo"]
    state.highlight = 0
    handle_mods_menu_event(state, _key(KeySym.PAGEDOWN))
    assert [m.name for m in state.mods] == ["Bravo", "Alpha"]
    assert [m.order for m in state.mods] == [1, 2]
    assert read_mod_state(root / "Alpha" / "mod.state") == (True, 2)
    assert read_mod_state(root / "Bravo" / "mod.state") == (True, 1)


def test_mods_escape_is_back(tmp_path: Path) -> None:
    root = tmp_path / "mods"
    root.mkdir()
    state = ModsMenuState(mods_root=root)
    state.refresh()
    assert handle_mods_menu_event(state, _key(KeySym.ESCAPE)) is ModsMenuAction.BACK


def test_confirm_requires_capital_y() -> None:
    state = ModsEnterConfirmState()
    assert (
        handle_mods_enter_confirm_event(state, _key(KeySym.Y, shift=False))
        is ModsEnterConfirmAction.NONE
    )
    assert state.error_message
    assert (
        handle_mods_enter_confirm_event(state, _key(KeySym.Y, shift=True))
        is ModsEnterConfirmAction.CONFIRM
    )


def test_confirm_n_and_escape_cancel() -> None:
    state = ModsEnterConfirmState()
    assert (
        handle_mods_enter_confirm_event(state, _key(KeySym.N))
        is ModsEnterConfirmAction.CANCEL
    )
    state = ModsEnterConfirmState()
    assert (
        handle_mods_enter_confirm_event(state, _key(KeySym.ESCAPE))
        is ModsEnterConfirmAction.CANCEL
    )


def test_app_open_mods_without_save(tmp_path: Path, monkeypatch) -> None:
    mods_root = tmp_path / "mods"
    _mod_folder(mods_root, "Solo", order=1)
    monkeypatch.setattr("src.user_data.MODS_DIR", mods_root)

    app = app_with_isolated_save(tmp_path)
    app.phase = AppPhase.OPTIONS
    app.options = OptionsMenuState(highlight=MODS_ROW_INDEX)
    app.handle_event(_key(KeySym.RETURN))
    assert app.phase is AppPhase.MODS
    assert app.mods_menu is not None
    assert app.mods_enter_confirm is None
    assert any(m.name == "Solo" for m in app.mods_menu.mods)


def _write_minimal_save(store: SaveStore) -> None:
    """Write a valid autosave so ``probe()`` is True."""
    from src.engine import GameEngine
    from src.save.snapshot import build_run_snapshot
    from tests.map_test_helpers import isolate_other_ais

    engine = GameEngine(player_name="Tester")
    isolate_other_ais(engine)
    store.save_run(build_run_snapshot(engine))


def test_app_open_mods_with_save_shows_confirm(tmp_path: Path, monkeypatch) -> None:
    mods_root = tmp_path / "mods"
    mods_root.mkdir()
    monkeypatch.setattr("src.user_data.MODS_DIR", mods_root)

    app = app_with_isolated_save(tmp_path)
    _write_minimal_save(app.save_coordinator.store)
    assert app.save_coordinator.store.probe() is True

    app.phase = AppPhase.OPTIONS
    app.options = OptionsMenuState(highlight=MODS_ROW_INDEX)
    app.handle_event(_key(KeySym.RETURN))
    assert app.phase is AppPhase.OPTIONS
    assert app.mods_enter_confirm is not None
    assert app.mods_menu is None


def test_app_confirm_y_deletes_save_and_enters_mods(tmp_path: Path, monkeypatch) -> None:
    mods_root = tmp_path / "mods"
    _mod_folder(mods_root, "Solo", order=1)
    monkeypatch.setattr("src.user_data.MODS_DIR", mods_root)

    app = app_with_isolated_save(tmp_path)
    _write_minimal_save(app.save_coordinator.store)
    assert app.save_coordinator.store.probe() is True

    app.phase = AppPhase.OPTIONS
    app.options = OptionsMenuState(highlight=MODS_ROW_INDEX)
    app.handle_event(_key(KeySym.RETURN))
    app.handle_event(_key(KeySym.Y, shift=True))
    assert app.phase is AppPhase.MODS
    assert app.save_coordinator.store.probe() is False
    assert app.mods_enter_confirm is None


def test_app_confirm_n_stays_on_options_keeps_save(tmp_path: Path, monkeypatch) -> None:
    mods_root = tmp_path / "mods"
    mods_root.mkdir()
    monkeypatch.setattr("src.user_data.MODS_DIR", mods_root)

    app = app_with_isolated_save(tmp_path)
    _write_minimal_save(app.save_coordinator.store)

    app.phase = AppPhase.OPTIONS
    app.options = OptionsMenuState(highlight=MODS_ROW_INDEX)
    app.handle_event(_key(KeySym.RETURN))
    app.handle_event(_key(KeySym.N))
    assert app.phase is AppPhase.OPTIONS
    assert app.mods_enter_confirm is None
    assert app.save_coordinator.store.probe() is True


def test_leave_mods_returns_to_options(tmp_path: Path, monkeypatch) -> None:
    mods_root = tmp_path / "mods"
    mods_root.mkdir()
    monkeypatch.setattr("src.user_data.MODS_DIR", mods_root)

    app = app_with_isolated_save(tmp_path)
    app.phase = AppPhase.OPTIONS
    app.options = OptionsMenuState(highlight=MODS_ROW_INDEX)
    app.handle_event(_key(KeySym.RETURN))
    assert app.phase is AppPhase.MODS
    app.handle_event(_key(KeySym.ESCAPE))
    assert app.phase is AppPhase.OPTIONS
    assert app.mods_menu is None


def test_format_mod_row() -> None:
    from src.mods.state import ModInfo

    mod = ModInfo(name="Cool", path=Path("Cool"), enabled=True, order=2)
    assert format_mod_row(mod, highlighted=True) == "> 2. Cool  [Enabled]"
    mod_off = ModInfo(name="Cool", path=Path("Cool"), enabled=False, order=2)
    assert format_mod_row(mod_off, highlighted=False) == "  2. Cool  [Disabled]"


def test_render_mods_menu_empty(tmp_path: Path) -> None:
    root = tmp_path / "mods"
    root.mkdir()
    state = ModsMenuState(mods_root=root)
    state.refresh()
    console = tcod.console.Console(80, 42, order="F")
    render_mods_menu(console, state)
    text = "".join(
        chr(int(console.rgba[x, y]["ch"])) if int(console.rgba[x, y]["ch"]) else " "
        for y in range(console.height)
        for x in range(console.width)
    )
    assert "No mods found" in text
    assert MODS_ENTER_PROMPT_LINES[0]  # imported constant exists
