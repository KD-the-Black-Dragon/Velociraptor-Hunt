"""Aggregate floor snapshots into trajectory CSV rows and loadout bank."""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field

from src.sim.runner import SimTrajectoryRunResult
from src.sim.scoring import event_score
from src.sim.snapshots import (
    FloorOutcomeSnapshot,
    LoadoutAtEntry,
    LoadoutProfile,
)

LOADOUT_BANK_MIN_RUNS = 5

STARTER_LOADOUT_PROFILE = LoadoutProfile(
    weapon_damage_sum=8,
    armor_ac=1,
    heal_potions=0,
    might_potions=0,
    haste_potions=0,
    teleport_potions=0,
    wand_charges=0,
)


@dataclass
class LoadoutBank:
    """Median loadout at floor entry per depth (feeds PR6 isolation)."""

    profiles: dict[int, LoadoutProfile] = field(default_factory=dict)

    def profile_for_floor(self, floor: int) -> LoadoutProfile:
        return self.profiles.get(floor, STARTER_LOADOUT_PROFILE)


def _percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    rank = (len(ordered) - 1) * fraction
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    weight = rank - low
    return ordered[low] * (1.0 - weight) + ordered[high] * weight


def _mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def _stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return statistics.stdev(values)


def _median_int(values: list[int]) -> int:
    if not values:
        return 0
    return int(round(statistics.median(values)))


def _profile_from_entries(entries: list[LoadoutAtEntry]) -> LoadoutProfile:
    if not entries:
        return LoadoutProfile()
    return LoadoutProfile(
        weapon_damage_sum=_median_int([e.weapon_damage_sum for e in entries]),
        armor_ac=_median_int([e.armor_ac for e in entries]),
        heal_potions=_median_int([e.heal_potions for e in entries]),
        might_potions=_median_int([e.might_potions for e in entries]),
        haste_potions=_median_int([e.haste_potions for e in entries]),
        teleport_potions=_median_int([e.teleport_potions for e in entries]),
        wand_charges=_median_int([e.wand_charges for e in entries]),
    )


def build_loadout_bank(
    visits_by_floor: dict[int, list[FloorOutcomeSnapshot]],
    *,
    floors_max: int,
    min_runs: int = LOADOUT_BANK_MIN_RUNS,
) -> LoadoutBank:
    """Median entry loadout per floor with shallow-floor fallback."""
    raw: dict[int, LoadoutProfile] = {}
    for floor in range(1, floors_max + 1):
        visits = visits_by_floor.get(floor, [])
        entries = [visit.entry_loadout for visit in visits]
        if len(visits) >= min_runs:
            raw[floor] = _profile_from_entries(entries)

    profiles: dict[int, LoadoutProfile] = {}
    previous = STARTER_LOADOUT_PROFILE
    for floor in range(1, floors_max + 1):
        if floor in raw:
            previous = raw[floor]
        profiles[floor] = previous
    return LoadoutBank(profiles=profiles)


def _runes_bucket(snapshot: FloorOutcomeSnapshot) -> int:
    """Map runes_this_floor to CSV bucket 0–3 (3 = three or more)."""
    return min(3, max(0, snapshot.runes_this_floor))


def _runs_column(prefix: str) -> str:
    return "traj_runs_reached" if prefix == "traj" else "iso_runs"


def aggregate_floor_visits(
    visits: list[FloorOutcomeSnapshot],
    *,
    prefix: str = "traj",
) -> dict[str, int | float]:
    """Compute ``traj_*`` or ``iso_*`` metrics for one floor from visit snapshots."""
    reached = len(visits)
    runs_key = _runs_column(prefix)
    row: dict[str, int | float] = {
        runs_key: reached,
        f"{prefix}_digest_rate": 0.0,
        f"{prefix}_descend_rate": 0.0,
        f"{prefix}_difficulty_mean": 0.0,
        f"{prefix}_difficulty_median": 0.0,
        f"{prefix}_difficulty_p10": 0.0,
        f"{prefix}_difficulty_p90": 0.0,
        f"{prefix}_difficulty_stdev": 0.0,
        f"{prefix}_runes_0": 0.0,
        f"{prefix}_runes_1": 0.0,
        f"{prefix}_runes_2": 0.0,
        f"{prefix}_runes_3": 0.0,
        f"{prefix}_early_bail_rate": 0.0,
        f"{prefix}_consumable_heal_mean": 0.0,
        f"{prefix}_consumable_might_mean": 0.0,
        f"{prefix}_consumable_haste_mean": 0.0,
        f"{prefix}_consumable_teleport_mean": 0.0,
        f"{prefix}_wand_evoke_mean": 0.0,
        f"{prefix}_weapon_improve_rate": 0.0,
        f"{prefix}_armor_improve_rate": 0.0,
        f"{prefix}_weapon_spawn_rate": 0.0,
        f"{prefix}_weapon_take_rate": 0.0,
        f"{prefix}_armor_spawn_rate": 0.0,
        f"{prefix}_armor_take_rate": 0.0,
        f"{prefix}_digest_when_weapon_spawned": 0.0,
        f"{prefix}_digest_when_weapon_not_spawned": 0.0,
        f"{prefix}_stunned_events_mean": 0.0,
    }
    if not visits:
        return row

    scores = [event_score(visit) for visit in visits]
    row[f"{prefix}_digest_rate"] = sum(1 for v in visits if v.digested) / reached
    row[f"{prefix}_descend_rate"] = sum(1 for v in visits if v.descended) / reached
    row[f"{prefix}_difficulty_mean"] = _mean(scores)
    row[f"{prefix}_difficulty_median"] = _percentile(scores, 0.5)
    row[f"{prefix}_difficulty_p10"] = _percentile(scores, 0.10)
    row[f"{prefix}_difficulty_p90"] = _percentile(scores, 0.90)
    row[f"{prefix}_difficulty_stdev"] = _stdev(scores)

    descended = [v for v in visits if v.descended]
    if descended:
        for bucket in range(4):
            count = sum(1 for v in descended if _runes_bucket(v) == bucket)
            row[f"{prefix}_runes_{bucket}"] = count / len(descended)
        row[f"{prefix}_early_bail_rate"] = (
            sum(
                1
                for v in descended
                if v.bail_for_survival and v.runes_this_floor < v.rune_quota
            )
            / len(descended)
        )

    row[f"{prefix}_consumable_heal_mean"] = _mean([float(v.consumable_heal) for v in visits])
    row[f"{prefix}_consumable_might_mean"] = _mean([float(v.consumable_might) for v in visits])
    row[f"{prefix}_consumable_haste_mean"] = _mean([float(v.consumable_haste) for v in visits])
    row[f"{prefix}_consumable_teleport_mean"] = _mean(
        [float(v.consumable_teleport) for v in visits]
    )
    row[f"{prefix}_wand_evoke_mean"] = _mean([float(v.wand_evokes) for v in visits])
    row[f"{prefix}_weapon_improve_rate"] = sum(1 for v in visits if v.weapon_improved) / reached
    row[f"{prefix}_armor_improve_rate"] = sum(1 for v in visits if v.armor_improved) / reached
    row[f"{prefix}_weapon_spawn_rate"] = (
        sum(1 for v in visits if v.upgrade_weapon_spawned) / reached
    )
    row[f"{prefix}_armor_spawn_rate"] = (
        sum(1 for v in visits if v.upgrade_armor_spawned) / reached
    )

    weapon_spawned = [v for v in visits if v.upgrade_weapon_spawned]
    if weapon_spawned:
        row[f"{prefix}_weapon_take_rate"] = (
            sum(1 for v in weapon_spawned if v.upgrade_weapon_taken) / len(weapon_spawned)
        )
        row[f"{prefix}_digest_when_weapon_spawned"] = (
            sum(1 for v in weapon_spawned if v.digested) / len(weapon_spawned)
        )

    weapon_not_spawned = [v for v in visits if not v.upgrade_weapon_spawned]
    if weapon_not_spawned:
        row[f"{prefix}_digest_when_weapon_not_spawned"] = (
            sum(1 for v in weapon_not_spawned if v.digested) / len(weapon_not_spawned)
        )

    armor_spawned = [v for v in visits if v.upgrade_armor_spawned]
    if armor_spawned:
        row[f"{prefix}_armor_take_rate"] = (
            sum(1 for v in armor_spawned if v.upgrade_armor_taken) / len(armor_spawned)
        )

    row[f"{prefix}_stunned_events_mean"] = _mean([float(v.stunned_events) for v in visits])
    return row


def collect_visits_by_floor(
    runs: list[SimTrajectoryRunResult],
    *,
    floors_max: int,
) -> dict[int, list[FloorOutcomeSnapshot]]:
    visits_by_floor: dict[int, list[FloorOutcomeSnapshot]] = {
        floor: [] for floor in range(1, floors_max + 1)
    }
    for run in runs:
        for snapshot in run.floor_snapshots:
            if 1 <= snapshot.floor <= floors_max:
                visits_by_floor[snapshot.floor].append(snapshot)
    return visits_by_floor


def aggregate_trajectory_metrics(
    runs: list[SimTrajectoryRunResult],
    *,
    floors_max: int,
) -> tuple[list[dict[str, int | float | str]], LoadoutBank]:
    """Build per-floor wide rows and loadout bank from trajectory runs."""
    visits_by_floor = collect_visits_by_floor(runs, floors_max=floors_max)
    loadout_bank = build_loadout_bank(visits_by_floor, floors_max=floors_max)

    rows: list[dict[str, int | float | str]] = []
    for floor in range(1, floors_max + 1):
        metrics = aggregate_floor_visits(visits_by_floor[floor], prefix="traj")
        row: dict[str, int | float | str] = {"floor": floor}
        row.update(metrics)
        row.update(aggregate_floor_visits([], prefix="iso"))
        rows.append(row)
    return rows, loadout_bank


def merge_isolation_into_rows(
    rows: list[dict[str, int | float | str]],
    visits_by_floor: dict[int, list[FloorOutcomeSnapshot]],
    *,
    floors_max: int,
) -> list[dict[str, int | float | str]]:
    """Attach ``iso_*`` columns to existing per-floor wide rows."""
    for row in rows:
        floor = int(row["floor"])
        if 1 <= floor <= floors_max:
            row.update(aggregate_floor_visits(visits_by_floor[floor], prefix="iso"))
    return rows