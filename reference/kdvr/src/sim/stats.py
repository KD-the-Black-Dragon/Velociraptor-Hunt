"""Aggregate floor snapshots and write balance CSV reports."""

from __future__ import annotations

import csv
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from src.sim.aggregator import (
    LoadoutBank,
    STARTER_LOADOUT_PROFILE,
    aggregate_trajectory_metrics,
    merge_isolation_into_rows,
)
from src.sim.floor_entry import isolation_seed
from src.sim.runner import SimIsolationRun, SimTrajectoryRun, SimTrajectoryRunResult
from src.sim.snapshots import FloorOutcomeSnapshot

FLOORS_MAX_DEFAULT = 20
COMPARE_LABEL_COLUMN = "label"
COMPARE_METRIC_COLUMN = "metric"

# Wide (one-run curve) layout: row = floor, column = metric.
CSV_FLOOR_COLUMNS: tuple[str, ...] = (
    "floor",
    "traj_runs_reached",
    "traj_digest_rate",
    "traj_descend_rate",
    "traj_difficulty_mean",
    "traj_difficulty_median",
    "traj_difficulty_p10",
    "traj_difficulty_p90",
    "traj_difficulty_stdev",
    "traj_runes_0",
    "traj_runes_1",
    "traj_runes_2",
    "traj_runes_3",
    "traj_early_bail_rate",
    "traj_consumable_heal_mean",
    "traj_consumable_might_mean",
    "traj_consumable_haste_mean",
    "traj_consumable_teleport_mean",
    "traj_wand_evoke_mean",
    "traj_weapon_improve_rate",
    "traj_armor_improve_rate",
    "traj_weapon_spawn_rate",
    "traj_weapon_take_rate",
    "traj_armor_spawn_rate",
    "traj_armor_take_rate",
    "traj_digest_when_weapon_spawned",
    "traj_digest_when_weapon_not_spawned",
    "traj_stunned_events_mean",
    "iso_runs",
    "iso_digest_rate",
    "iso_descend_rate",
    "iso_difficulty_mean",
    "iso_difficulty_median",
    "iso_difficulty_p10",
    "iso_difficulty_p90",
    "iso_difficulty_stdev",
    "iso_runes_0",
    "iso_runes_1",
    "iso_runes_2",
    "iso_runes_3",
    "iso_early_bail_rate",
    "iso_consumable_heal_mean",
    "iso_consumable_might_mean",
    "iso_consumable_haste_mean",
    "iso_consumable_teleport_mean",
    "iso_wand_evoke_mean",
    "iso_weapon_improve_rate",
    "iso_armor_improve_rate",
    "iso_weapon_spawn_rate",
    "iso_weapon_take_rate",
    "iso_armor_spawn_rate",
    "iso_armor_take_rate",
    "iso_digest_when_weapon_spawned",
    "iso_digest_when_weapon_not_spawned",
    "iso_stunned_events_mean",
)

_TRAJ_FLOOR_FIELDS: tuple[tuple[str, str], ...] = (
    ("runs_reached", "runs reached"),
    ("digest_rate", "digest rate"),
    ("descend_rate", "descend rate"),
    ("difficulty_mean", "difficulty mean"),
    ("difficulty_median", "difficulty median"),
    ("difficulty_p10", "difficulty p10"),
    ("difficulty_p90", "difficulty p90"),
    ("difficulty_stdev", "difficulty stdev"),
    ("runes_0", "runes 0"),
    ("runes_1", "runes 1"),
    ("runes_2", "runes 2"),
    ("runes_3", "runes 3"),
    ("early_bail_rate", "early bail rate"),
    ("consumable_heal_mean", "consumable heal mean"),
    ("consumable_might_mean", "consumable might mean"),
    ("consumable_haste_mean", "consumable haste mean"),
    ("consumable_teleport_mean", "consumable teleport mean"),
    ("wand_evoke_mean", "wand evoke mean"),
    ("weapon_improve_rate", "weapon improve rate"),
    ("armor_improve_rate", "armor improve rate"),
    ("weapon_spawn_rate", "weapon spawn rate"),
    ("weapon_take_rate", "weapon take rate"),
    ("armor_spawn_rate", "armor spawn rate"),
    ("armor_take_rate", "armor take rate"),
    ("digest_when_weapon_spawned", "digest when weapon spawned"),
    ("digest_when_weapon_not_spawned", "digest when weapon not spawned"),
    ("stunned_events_mean", "stunned events mean"),
)

_ISO_FLOOR_FIELDS: tuple[tuple[str, str], ...] = (
    ("runs", "runs"),
    ("digest_rate", "digest rate"),
    ("descend_rate", "descend rate"),
    ("difficulty_mean", "difficulty mean"),
    ("difficulty_median", "difficulty median"),
    ("difficulty_p10", "difficulty p10"),
    ("difficulty_p90", "difficulty p90"),
    ("difficulty_stdev", "difficulty stdev"),
    ("runes_0", "runes 0"),
    ("runes_1", "runes 1"),
    ("runes_2", "runes 2"),
    ("runes_3", "runes 3"),
    ("early_bail_rate", "early bail rate"),
    ("consumable_heal_mean", "consumable heal mean"),
    ("consumable_might_mean", "consumable might mean"),
    ("consumable_haste_mean", "consumable haste mean"),
    ("consumable_teleport_mean", "consumable teleport mean"),
    ("wand_evoke_mean", "wand evoke mean"),
    ("weapon_improve_rate", "weapon improve rate"),
    ("armor_improve_rate", "armor improve rate"),
    ("weapon_spawn_rate", "weapon spawn rate"),
    ("weapon_take_rate", "weapon take rate"),
    ("armor_spawn_rate", "armor spawn rate"),
    ("armor_take_rate", "armor take rate"),
    ("digest_when_weapon_spawned", "digest when weapon spawned"),
    ("digest_when_weapon_not_spawned", "digest when weapon not spawned"),
    ("stunned_events_mean", "stunned events mean"),
)

_META_SPECS: tuple[tuple[str, str], ...] = (
    ("meta.timestamp", "Timestamp (UTC)"),
    ("meta.difficulty_id", "Difficulty"),
    ("meta.seconds_budget", "Seconds budget"),
    ("meta.trajectory_seconds", "Trajectory seconds"),
    ("meta.isolation_seconds", "Isolation seconds"),
    ("meta.trajectory_runs", "Trajectory runs"),
    ("meta.isolation_runs_total", "Isolation runs total"),
    ("meta.data_fingerprint", "Data fingerprint"),
)


@dataclass(frozen=True)
class CompareRowSpec:
    key: str
    label: str
    section: bool = False


@dataclass
class SimRunMetadata:
    difficulty_id: str
    seconds_budget: float
    trajectory_seconds: float
    isolation_seconds: float
    trajectory_runs: int
    isolation_runs_total: int
    data_fingerprint: str
    seed: int | None = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class TrajectoryPassResult:
    runs: list[SimTrajectoryRunResult] = field(default_factory=list)
    wall_seconds: float = 0.0
    loadout_bank: LoadoutBank | None = None


@dataclass
class IsolationPassResult:
    visits_by_floor: dict[int, list[FloorOutcomeSnapshot]] = field(default_factory=dict)
    wall_seconds: float = 0.0
    runs_total: int = 0


def compare_row_specs(*, floors_max: int = FLOORS_MAX_DEFAULT) -> tuple[CompareRowSpec, ...]:
    """Stable row order for compare-sheet CSV (column A keys, column B labels)."""
    rows: list[CompareRowSpec] = [
        CompareRowSpec(key=key, label=label) for key, label in _META_SPECS
    ]
    rows.append(CompareRowSpec(key="_section.traj", label="--- trajectory ---", section=True))
    for floor in range(1, floors_max + 1):
        for field_key, field_label in _TRAJ_FLOOR_FIELDS:
            rows.append(
                CompareRowSpec(
                    key=f"traj.f{floor:02d}.{field_key}",
                    label=f"F{floor:02d} traj {field_label}",
                )
            )
    rows.append(CompareRowSpec(key="_section.iso", label="--- isolation ---", section=True))
    for floor in range(1, floors_max + 1):
        for field_key, field_label in _ISO_FLOOR_FIELDS:
            rows.append(
                CompareRowSpec(
                    key=f"iso.f{floor:02d}.{field_key}",
                    label=f"F{floor:02d} iso {field_label}",
                )
            )
    return tuple(rows)


def default_column_label(metadata: SimRunMetadata) -> str:
    """Auto column header when --label is omitted."""
    stamp = metadata.timestamp.replace(":", "").replace("-", "")[:15]
    budget = int(metadata.seconds_budget)
    return f"{metadata.difficulty_id}_{budget}s_{stamp}"


def _wide_column_for_compare_field(pass_prefix: str, floor: int, field_key: str) -> str:
    if pass_prefix == "traj":
        if field_key == "runs_reached":
            return "traj_runs_reached"
        return f"traj_{field_key}"
    if field_key == "runs":
        return "iso_runs"
    return f"iso_{field_key}"


def build_compare_column_values(
    rows: list[dict[str, int | float | str]],
    metadata: SimRunMetadata,
    *,
    floors_max: int = FLOORS_MAX_DEFAULT,
) -> dict[str, str | int | float]:
    """Map compare-row keys to values for one analysis pass."""
    floor_by_number = {int(row["floor"]): row for row in rows}
    values: dict[str, str | int | float] = {
        "meta.timestamp": metadata.timestamp,
        "meta.difficulty_id": metadata.difficulty_id,
        "meta.seconds_budget": metadata.seconds_budget,
        "meta.trajectory_seconds": round(metadata.trajectory_seconds, 3),
        "meta.isolation_seconds": round(metadata.isolation_seconds, 3),
        "meta.trajectory_runs": metadata.trajectory_runs,
        "meta.isolation_runs_total": metadata.isolation_runs_total,
        "meta.data_fingerprint": metadata.data_fingerprint,
        "_section.traj": "",
        "_section.iso": "",
    }
    for floor in range(1, floors_max + 1):
        wide = floor_by_number.get(floor, {})
        for field_key, _ in _TRAJ_FLOOR_FIELDS:
            wide_key = _wide_column_for_compare_field("traj", floor, field_key)
            values[f"traj.f{floor:02d}.{field_key}"] = wide.get(wide_key, 0)
        for field_key, _ in _ISO_FLOOR_FIELDS:
            wide_key = _wide_column_for_compare_field("iso", floor, field_key)
            values[f"iso.f{floor:02d}.{field_key}"] = wide.get(wide_key, 0)
    return values


def run_trajectory_pass(
    *,
    difficulty_id: str,
    seconds_budget: float,
    seed_start: int,
    max_turns: int,
    floors_max: int,
) -> TrajectoryPassResult:
    """Run trajectory simulations until the time budget expires."""
    started = time.perf_counter()
    deadline = started + seconds_budget
    runs: list[SimTrajectoryRunResult] = []
    seed = seed_start

    while time.perf_counter() < deadline:
        run = SimTrajectoryRun(
            difficulty_id=difficulty_id,
            seed=seed,
            max_turns=max_turns,
            floors_max=floors_max,
        )
        runs.append(run.run(deadline=deadline))
        seed += 1

    elapsed = time.perf_counter() - started
    _rows, loadout_bank = aggregate_trajectory_metrics(runs, floors_max=floors_max)
    return TrajectoryPassResult(
        runs=runs,
        wall_seconds=elapsed,
        loadout_bank=loadout_bank,
    )


def aggregate_trajectory_rows(
    runs: list[SimTrajectoryRunResult],
    *,
    floors_max: int = FLOORS_MAX_DEFAULT,
) -> list[dict[str, int | float | str]]:
    """Build per-floor wide rows from trajectory snapshots."""
    rows, _bank = aggregate_trajectory_metrics(runs, floors_max=floors_max)
    return rows


def _read_compare_sheet(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError(f"compare sheet is empty: {path}") from None
        body = [list(row) for row in reader]
    return header, body


def _validate_compare_body(
    body: list[list[str]],
    *,
    floors_max: int,
) -> None:
    expected = [spec.key for spec in compare_row_specs(floors_max=floors_max)]
    if len(body) != len(expected):
        raise ValueError(
            f"compare sheet row count mismatch: expected {len(expected)}, got {len(body)}"
        )
    for index, (row, key) in enumerate(zip(body, expected, strict=True)):
        if not row:
            raise ValueError(f"compare sheet row {index + 2} is empty")
        if row[0] != key:
            raise ValueError(
                f"compare sheet row {index + 2}: expected metric {key!r}, got {row[0]!r}"
            )


def write_compare_sheet_csv(
    path: Path,
    *,
    column_label: str,
    column_values: dict[str, str | int | float],
    floors_max: int = FLOORS_MAX_DEFAULT,
    append: bool = False,
) -> None:
    """Write side-by-side compare CSV (metric + label columns, one column per run)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    specs = compare_row_specs(floors_max=floors_max)

    if append and path.is_file():
        header, body = _read_compare_sheet(path)
        if len(header) < 3 or header[0] != COMPARE_METRIC_COLUMN:
            raise ValueError(f"not a compare sheet: {path}")
        if column_label in header:
            raise ValueError(f"column label already exists: {column_label}")
        _validate_compare_body(body, floors_max=floors_max)
        header.append(column_label)
        for row in body:
            value = column_values.get(row[0], "")
            row.append(_format_cell(value))
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            writer.writerows(body)
        return

    header = [COMPARE_METRIC_COLUMN, COMPARE_LABEL_COLUMN, column_label]
    body: list[list[str]] = []
    for spec in specs:
        value = column_values.get(spec.key, "")
        body.append([spec.key, spec.label, _format_cell(value)])

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(body)


def write_wide_curve_csv(
    path: Path,
    *,
    rows: list[dict[str, int | float | str]],
) -> None:
    """Optional one-run curve table (row = floor) for charting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(CSV_FLOOR_COLUMNS))
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, 0) for col in CSV_FLOOR_COLUMNS})


def write_balance_report(
    path: Path,
    *,
    rows: list[dict[str, int | float | str]],
    metadata: SimRunMetadata,
    column_label: str | None = None,
    floors_max: int = FLOORS_MAX_DEFAULT,
    append: bool = False,
    output_format: str = "compare",
    curve_output: Path | None = None,
) -> str:
    """Write balance output; returns the column label used."""
    label = column_label or default_column_label(metadata)
    if output_format == "wide":
        write_wide_curve_csv(path, rows=rows)
        return label

    values = build_compare_column_values(rows, metadata, floors_max=floors_max)
    write_compare_sheet_csv(
        path,
        column_label=label,
        column_values=values,
        floors_max=floors_max,
        append=append,
    )
    if curve_output is not None:
        write_wide_curve_csv(curve_output, rows=rows)
    return label


def _format_cell(value: str | int | float) -> str:
    if value == "":
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def run_isolation_pass(
    *,
    difficulty_id: str,
    seconds_budget: float,
    seed_start: int,
    max_turns: int,
    floors_max: int,
    loadout_bank: LoadoutBank | None,
) -> IsolationPassResult:
    """Run isolation sims per floor slice until the time budget expires."""
    started = time.perf_counter()
    deadline = started + seconds_budget
    slice_seconds = seconds_budget / floors_max if floors_max > 0 else seconds_budget
    visits_by_floor: dict[int, list[FloorOutcomeSnapshot]] = {
        floor: [] for floor in range(1, floors_max + 1)
    }
    bank = loadout_bank or LoadoutBank(profiles={floor: STARTER_LOADOUT_PROFILE for floor in range(1, floors_max + 1)})
    runs_total = 0
    run_index = 0

    for floor in range(1, floors_max + 1):
        floor_deadline = started + floor * slice_seconds
        profile = bank.profile_for_floor(floor)
        while time.perf_counter() < min(deadline, floor_deadline):
            iso_seed = isolation_seed(seed_start, floor, run_index)
            run = SimIsolationRun(
                difficulty_id=difficulty_id,
                floor=floor,
                seed=iso_seed,
                loadout=profile,
                max_turns=max_turns,
            )
            result = run.run(deadline=min(deadline, floor_deadline))
            if result.snapshot is not None:
                visits_by_floor[floor].append(result.snapshot)
                runs_total += 1
            run_index += 1

    elapsed = time.perf_counter() - started
    return IsolationPassResult(
        visits_by_floor=visits_by_floor,
        wall_seconds=elapsed,
        runs_total=runs_total,
    )


def run_balance_analysis(
    *,
    difficulty_id: str,
    seconds_budget: float,
    trajectory_fraction: float,
    seed: int,
    max_turns: int,
    floors_max: int,
    data_fingerprint: str,
    run_isolation: bool = True,
) -> tuple[list[dict[str, int | float | str]], SimRunMetadata]:
    """Trajectory + isolation passes with full ``traj_*`` and ``iso_*`` aggregation."""
    trajectory_seconds = seconds_budget * trajectory_fraction
    isolation_seconds = max(0.0, seconds_budget - trajectory_seconds)

    pass_result = run_trajectory_pass(
        difficulty_id=difficulty_id,
        seconds_budget=trajectory_seconds,
        seed_start=seed,
        max_turns=max_turns,
        floors_max=floors_max,
    )

    rows, _bank = aggregate_trajectory_metrics(pass_result.runs, floors_max=floors_max)
    loadout_bank = pass_result.loadout_bank or _bank

    iso_result = IsolationPassResult()
    if run_isolation and isolation_seconds > 0:
        iso_result = run_isolation_pass(
            difficulty_id=difficulty_id,
            seconds_budget=isolation_seconds,
            seed_start=seed,
            max_turns=max_turns,
            floors_max=floors_max,
            loadout_bank=loadout_bank,
        )
        rows = merge_isolation_into_rows(
            rows,
            iso_result.visits_by_floor,
            floors_max=floors_max,
        )

    metadata = SimRunMetadata(
        difficulty_id=difficulty_id,
        seconds_budget=seconds_budget,
        trajectory_seconds=pass_result.wall_seconds,
        isolation_seconds=iso_result.wall_seconds,
        trajectory_runs=len(pass_result.runs),
        isolation_runs_total=iso_result.runs_total,
        data_fingerprint=data_fingerprint,
        seed=seed,
    )
    return rows, metadata