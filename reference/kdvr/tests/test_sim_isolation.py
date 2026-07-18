"""PR6 tests for isolation floor entry and iso aggregation."""

from __future__ import annotations

import pytest

from src.components import EquipState, Inventory, ItemCategory
from src.engine import GameEngine
from src.sim.aggregator import merge_isolation_into_rows
from src.sim.floor_entry import (
    apply_loadout_profile,
    isolation_seed,
    start_isolation_floor,
)
from src.sim.runner import SimIsolationRun
from src.sim.snapshots import FloorOutcomeSnapshot, LoadoutProfile
from src.sim.stats import run_balance_analysis


@pytest.fixture(scope="module", autouse=True)
def _stock_data() -> None:
    from src.sim.data_loader import install_stock_game_data

    install_stock_game_data()


def test_isolation_seed_is_deterministic() -> None:
    assert isolation_seed(42, 3, 1) == isolation_seed(42, 3, 1)
    assert isolation_seed(42, 3, 1) != isolation_seed(42, 3, 2)


def test_apply_loadout_profile_wields_closest_weapon() -> None:
    engine = GameEngine(save_coordinator=None, skip_new_game=True)
    engine.new_game(seed=1, log_session_milestones=False)
    player = engine.player
    assert player is not None
    apply_loadout_profile(
        player,
        LoadoutProfile(weapon_damage_sum=12, armor_ac=2, heal_potions=1),
    )
    equip = player.components[EquipState]
    inventory = player.components[Inventory]
    assert equip.wielded_slot is not None
    wielded = inventory.slots[equip.wielded_slot]
    assert wielded is not None
    assert wielded.category is ItemCategory.WEAPON


def test_start_isolation_floor_at_depth_three() -> None:
    engine = GameEngine(save_coordinator=None, skip_new_game=True)
    start_isolation_floor(
        engine,
        depth=3,
        seed=77,
        loadout=LoadoutProfile(),
    )
    assert engine.floor_depth == 3
    assert engine.player is not None


def test_sim_isolation_run_returns_snapshot() -> None:
    run = SimIsolationRun(
        difficulty_id="normal",
        floor=1,
        seed=99,
        loadout=LoadoutProfile(heal_potions=1),
        max_turns=200,
    )
    result = run.run()
    assert result.snapshot is not None
    assert result.snapshot.floor == 1


def test_merge_isolation_into_rows_populates_iso_runs() -> None:
    rows = [{"floor": 1, "traj_runs_reached": 2}]
    visits = {
        1: [
            FloorOutcomeSnapshot(
                floor=1,
                seed=1,
                digested=False,
                descended=True,
                rune_quota=3,
                runes_this_floor=1,
            )
        ],
    }
    merged = merge_isolation_into_rows(rows, visits, floors_max=1)
    assert merged[0]["iso_runs"] == 1
    assert merged[0]["iso_descend_rate"] == 1.0


def test_balance_analysis_includes_isolation_runs() -> None:
    rows, metadata = run_balance_analysis(
        difficulty_id="normal",
        seconds_budget=2.0,
        trajectory_fraction=0.5,
        seed=7,
        max_turns=500,
        floors_max=2,
        data_fingerprint="test",
        run_isolation=True,
    )
    assert metadata.isolation_runs_total >= 1
    assert rows[0]["iso_runs"] >= 1