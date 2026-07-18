"""PR1 tests for balance simulator runner shell."""

from __future__ import annotations

import csv
import time
from pathlib import Path

import pytest

from src.sim.data_loader import data_fingerprint, install_stock_game_data
from src.sim.runner import (
    SimTerminationReason,
    SimTrajectoryRun,
    execute_wait_turn,
)
from src.sim.stats import (
    COMPARE_LABEL_COLUMN,
    COMPARE_METRIC_COLUMN,
    aggregate_trajectory_rows,
    build_compare_column_values,
    compare_row_specs,
    run_balance_analysis,
    run_trajectory_pass,
    write_balance_report,
    SimRunMetadata,
)
from src.engine import GameEngine


@pytest.fixture(scope="module", autouse=True)
def _stock_data() -> None:
    install_stock_game_data()


def test_install_stock_game_data_fingerprint_stable() -> None:
    fp1 = data_fingerprint()
    fp2 = data_fingerprint()
    assert fp1 == fp2
    assert len(fp1) == 64


def test_trajectory_run_completes_ten_turns() -> None:
    run = SimTrajectoryRun(
        difficulty_id="normal",
        seed=42,
        max_turns=10,
    )
    result = run.run()
    assert result.turns_played == 10
    assert result.termination is SimTerminationReason.TURN_CAP
    assert result.depth_reached >= 1


def test_trajectory_run_records_floor_one_visit() -> None:
    run = SimTrajectoryRun(
        difficulty_id="normal",
        seed=99,
        max_turns=5,
    )
    result = run.run()
    assert len(result.floor_snapshots) >= 1
    assert result.floor_snapshots[0].floor == 1


def test_wait_turn_advances_counter() -> None:
    engine = GameEngine(save_coordinator=None, skip_new_game=True)
    engine.new_game(seed=1, log_session_milestones=False)
    before = engine.player_turn_count
    execute_wait_turn(engine)
    assert engine.player_turn_count == before + 1


def test_compare_sheet_layout(tmp_path: Path) -> None:
    rows = aggregate_trajectory_rows([], floors_max=20)
    metadata = SimRunMetadata(
        difficulty_id="normal",
        seconds_budget=1.0,
        trajectory_seconds=0.5,
        isolation_seconds=0.5,
        trajectory_runs=0,
        isolation_runs_total=0,
        data_fingerprint="abc",
    )
    out = tmp_path / "compare.csv"
    label = write_balance_report(
        out,
        rows=rows,
        metadata=metadata,
        column_label="baseline",
        floors_max=20,
    )
    assert label == "baseline"

    with out.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        body = list(reader)

    assert header == [COMPARE_METRIC_COLUMN, COMPARE_LABEL_COLUMN, "baseline"]
    assert len(body) == len(compare_row_specs(floors_max=20))
    assert body[0][0] == "meta.timestamp"
    assert body[0][2] == metadata.timestamp
    assert body[8][0] == "_section.traj"
    assert body[9][0] == "traj.f01.runs_reached"


def test_compare_sheet_append_column(tmp_path: Path) -> None:
    rows = aggregate_trajectory_rows([], floors_max=2)
    meta_a = SimRunMetadata(
        difficulty_id="normal",
        seconds_budget=1.0,
        trajectory_seconds=0.5,
        isolation_seconds=0.5,
        trajectory_runs=1,
        isolation_runs_total=0,
        data_fingerprint="abc",
    )
    meta_b = SimRunMetadata(
        difficulty_id="hard",
        seconds_budget=2.0,
        trajectory_seconds=1.0,
        isolation_seconds=1.0,
        trajectory_runs=2,
        isolation_runs_total=0,
        data_fingerprint="def",
    )
    out = tmp_path / "compare.csv"
    write_balance_report(
        out,
        rows=rows,
        metadata=meta_a,
        column_label="run_a",
        floors_max=2,
    )
    write_balance_report(
        out,
        rows=rows,
        metadata=meta_b,
        column_label="run_b",
        floors_max=2,
        append=True,
    )

    with out.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        body = list(reader)

    assert header == [COMPARE_METRIC_COLUMN, COMPARE_LABEL_COLUMN, "run_a", "run_b"]
    assert body[1][3] == "hard"
    assert body[0][2] == meta_a.timestamp
    assert body[0][3] == meta_b.timestamp


def test_wide_curve_format(tmp_path: Path) -> None:
    rows = aggregate_trajectory_rows([], floors_max=3)
    metadata = SimRunMetadata(
        difficulty_id="normal",
        seconds_budget=1.0,
        trajectory_seconds=0.5,
        isolation_seconds=0.5,
        trajectory_runs=0,
        isolation_runs_total=0,
        data_fingerprint="abc",
    )
    out = tmp_path / "curve.csv"
    write_balance_report(
        out,
        rows=rows,
        metadata=metadata,
        floors_max=3,
        output_format="wide",
    )
    with out.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        parsed = list(reader)
    assert len(parsed) == 3
    assert parsed[0]["floor"] == "1"


def test_build_compare_values_includes_floor_metric() -> None:
    rows = aggregate_trajectory_rows([], floors_max=1)
    rows[0]["traj_runs_reached"] = 7
    metadata = SimRunMetadata(
        difficulty_id="normal",
        seconds_budget=1.0,
        trajectory_seconds=0.5,
        isolation_seconds=0.5,
        trajectory_runs=3,
        isolation_runs_total=0,
        data_fingerprint="abc",
    )
    values = build_compare_column_values(rows, metadata, floors_max=1)
    assert values["traj.f01.runs_reached"] == 7
    assert values["meta.trajectory_runs"] == 3


def test_trajectory_pass_respects_time_budget() -> None:
    started = time.perf_counter()
    result = run_trajectory_pass(
        difficulty_id="normal",
        seconds_budget=0.25,
        seed_start=1,
        max_turns=50_000,
        floors_max=20,
    )
    elapsed = time.perf_counter() - started
    assert elapsed < 2.0
    assert result.wall_seconds <= 0.6
    assert len(result.runs) >= 1
    assert any(
        run.termination is SimTerminationReason.TIME_BUDGET
        for run in result.runs
    )


def test_balance_analysis_short_budget() -> None:
    rows, metadata = run_balance_analysis(
        difficulty_id="normal",
        seconds_budget=0.01,
        trajectory_fraction=1.0,
        seed=7,
        max_turns=20,
        floors_max=20,
        data_fingerprint="test",
        run_isolation=False,
    )
    assert metadata.trajectory_runs >= 1
    assert len(rows) == 20
    assert rows[0]["traj_runs_reached"] >= 1