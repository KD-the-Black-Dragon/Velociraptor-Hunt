"""PR5 tests for trajectory aggregation and loadout bank."""

from __future__ import annotations

from src.sim.aggregator import (
    LOADOUT_BANK_MIN_RUNS,
    aggregate_floor_visits,
    build_loadout_bank,
    collect_visits_by_floor,
)
from src.sim.runner import SimTerminationReason, SimTrajectoryRunResult
from src.sim.snapshots import FloorOutcomeSnapshot, LoadoutAtEntry, LoadoutProfile


def _visit(
    floor: int,
    *,
    digested: bool = False,
    descended: bool = True,
    runes: int = 3,
    bail: bool = False,
    weapon_spawned: bool = False,
    weapon_taken: bool = False,
    entry_damage: int = 8,
) -> FloorOutcomeSnapshot:
    return FloorOutcomeSnapshot(
        floor=floor,
        seed=floor,
        digested=digested,
        descended=descended,
        rune_quota=3,
        runes_this_floor=runes,
        bail_for_survival=bail,
        upgrade_weapon_spawned=weapon_spawned,
        upgrade_weapon_taken=weapon_taken,
        entry_loadout=LoadoutAtEntry(weapon_damage_sum=entry_damage, armor_ac=1),
        event_score=100.0 if digested else 10.0,
    )


def test_aggregate_floor_visits_digest_and_descend_rates() -> None:
    visits = [
        _visit(1, digested=True, descended=False),
        _visit(1, descended=True),
    ]
    row = aggregate_floor_visits(visits)
    assert row["traj_runs_reached"] == 2
    assert row["traj_digest_rate"] == 0.5
    assert row["traj_descend_rate"] == 0.5


def test_aggregate_floor_weapon_take_rate_conditional() -> None:
    visits = [
        _visit(1, weapon_spawned=True, weapon_taken=True),
        _visit(1, weapon_spawned=True, weapon_taken=False),
        _visit(1, weapon_spawned=False),
    ]
    row = aggregate_floor_visits(visits)
    assert row["traj_weapon_spawn_rate"] == 2 / 3
    assert row["traj_weapon_take_rate"] == 0.5


def test_aggregate_floor_digest_when_weapon_spawned() -> None:
    visits = [
        _visit(1, digested=True, descended=False, weapon_spawned=True),
        _visit(1, descended=True, weapon_spawned=True),
    ]
    row = aggregate_floor_visits(visits)
    assert row["traj_digest_when_weapon_spawned"] == 0.5
    assert row["traj_digest_when_weapon_not_spawned"] == 0.0


def test_build_loadout_bank_median_and_fallback() -> None:
    visits_by_floor = {
        1: [
            _visit(1, entry_damage=8),
            _visit(1, entry_damage=10),
            _visit(1, entry_damage=12),
            _visit(1, entry_damage=14),
            _visit(1, entry_damage=16),
        ],
        2: [_visit(2, entry_damage=20)],
    }
    bank = build_loadout_bank(visits_by_floor, floors_max=3, min_runs=LOADOUT_BANK_MIN_RUNS)
    assert bank.profile_for_floor(1).weapon_damage_sum == 12
    assert bank.profile_for_floor(2).weapon_damage_sum == 12  # fallback from floor 1
    assert bank.profile_for_floor(3).weapon_damage_sum == 12


def test_collect_visits_by_floor_from_run_results() -> None:
    run = SimTrajectoryRunResult(
        seed=1,
        difficulty_id="normal",
        termination=SimTerminationReason.TURN_CAP,
        depth_reached=2,
        runes_collected=0,
        monsters_defeated=0,
        turns_played=10,
        hp_at_end=1,
        floor_snapshots=[_visit(1), _visit(2)],
    )
    by_floor = collect_visits_by_floor([run], floors_max=3)
    assert len(by_floor[1]) == 1
    assert len(by_floor[2]) == 1
    assert len(by_floor[3]) == 0