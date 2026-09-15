"""PR3: session log milestone hooks."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.app import App
from src.components import DisplayName
from src.debug import paths as debug_paths
from src.debug.session_log import SessionLogCoordinator
from src.engine import GameEngine
from src.game_over_ending import GameOverEnding
from src.run_stats import RunStats
from src.save.coordinator import SaveCoordinator
from src.save.store import SaveStore
from src.save.snapshot import build_run_snapshot
from src.systems.digestion import GameOverState
from src.systems.inventory import (
    _add_instance_to_inventory,
    item_registry,
    make_potion_instance,
)
from src.message_log import MessageLog
from src.app import AppPhase

from tests.map_test_helpers import isolate_other_ais
from tests.ui_test_helpers import make_console


@pytest.fixture
def session_coordinator(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> SessionLogCoordinator:
    monkeypatch.setattr(debug_paths, "LOGS_DIR", tmp_path / "logs")
    coordinator = SessionLogCoordinator()
    coordinator.start_session()
    # Engine extract (PR4–PR6) moved session_log imports off src.engine onto
    # engine_floor / engine_input; patch each binding that logs milestones.
    # Also patch the module global for lazy importers (e.g. run_stats).
    import importlib

    session_log_mod = importlib.import_module("src.debug.session_log")
    monkeypatch.setattr(session_log_mod, "session_log", coordinator, raising=True)
    for module in (
        "src.app",
        "src.engine_floor",
        "src.engine_input",
        "src.systems.inventory",
        "src.systems.digestion",
    ):
        monkeypatch.setattr(f"{module}.session_log", coordinator)
    yield coordinator
    coordinator.close()


def _session_lines(coordinator: SessionLogCoordinator) -> list[str]:
    coordinator.flush()
    path = coordinator.session_path
    assert path is not None
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_new_game_canonical_order(session_coordinator: SessionLogCoordinator) -> None:
    app = App(save_coordinator=SaveCoordinator(store=SaveStore()))
    console = make_console()
    app._start_new_game("Hero", console=console)

    lines = _session_lines(session_coordinator)
    assert lines.index("Started new game") < lines.index(f"Seed: {app.engine.run_seed}")
    assert lines.index(f"Seed: {app.engine.run_seed}") < lines.index("Entered floor 1")


def test_loaded_game_milestone(
    tmp_path: Path,
    session_coordinator: SessionLogCoordinator,
) -> None:
    store = SaveStore(tmp_path)
    engine = GameEngine(player_name="SavedHero")
    isolate_other_ais(engine)
    store.save_run(build_run_snapshot(engine))

    app = App(save_coordinator=SaveCoordinator(store=store))
    app._load_saved_game(make_console())

    lines = _session_lines(session_coordinator)
    assert "Loaded game" in lines


def test_quit_to_menu_milestone(session_coordinator: SessionLogCoordinator) -> None:
    app = App()
    app.engine = GameEngine(skip_new_game=True)
    app.phase = AppPhase.PLAY
    app._return_to_menu()

    lines = _session_lines(session_coordinator)
    assert "Quit to menu" in lines


def test_debug_regen_logs_dungeon_regenerated_only(
    session_coordinator: SessionLogCoordinator,
) -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    session_coordinator.flush()
    before = _session_lines(session_coordinator)

    from src.debug.session_log import session_log

    engine.new_game(log_session_milestones=False)
    session_log.log("Dungeon regenerated")

    lines = _session_lines(session_coordinator)
    new_lines = lines[len(before) :]
    assert new_lines == ["Dungeon regenerated"]
    assert not any(line.startswith("Seed:") for line in new_lines)
    assert not any(line.startswith("Entered floor") for line in new_lines)


def test_game_over_milestone(session_coordinator: SessionLogCoordinator) -> None:
    state = GameOverState()
    state.open(
        player_name="Hero",
        ending=GameOverEnding(kind="defeated", detail="wolf"),
        monsters_defeated=1,
        runes_collected=0,
        depth=3,
    )
    assert "Game over" in _session_lines(session_coordinator)


def test_pickup_milestone(session_coordinator: SessionLogCoordinator) -> None:
    from src.components import Inventory

    inventory = Inventory()
    instance = make_potion_instance()
    reg = item_registry()
    slot = _add_instance_to_inventory(
        inventory,
        instance,
        reg,
        MessageLog(),
    )
    assert slot is not None
    lines = _session_lines(session_coordinator)
    assert any(line.startswith("Collected ") for line in lines)


def test_defeat_milestone(session_coordinator: SessionLogCoordinator) -> None:
    world = GameEngine(skip_new_game=True).world
    enemy = world[object()]
    enemy.components[DisplayName] = DisplayName(name="wolf")

    stats = RunStats()
    stats.record_monster_defeated(defeated_entity=enemy)

    lines = _session_lines(session_coordinator)
    assert any(line.startswith("Defeated ") for line in lines)