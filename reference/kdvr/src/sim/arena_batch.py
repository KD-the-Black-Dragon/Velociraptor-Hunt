"""Batch 1v1 arena trials and compare-sheet CSV export."""

from __future__ import annotations

import csv
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from src.components import Alignment
from src.data.entity_loader import load_entity_registry
from src.sim.arena_runner import ArenaSimRun, ArenaTrialOutcome
from src.sim.stats import _format_cell

ARENA_COMPARE_METRIC_COLUMN = "metric"

ARENA_META_ROWS: tuple[str, ...] = (
    "meta.seed",
    "meta.difficulty_id",
    "meta.trials_per_entity",
    "meta.max_turns",
)

ARENA_ENTITY_FIELDS: tuple[str, ...] = (
    "enemy_id",
    "min_spawn_depth",
    "player_wins",
    "enemy_wins",
    "player_win_hp_remaining",
    "enemy_win_hp_remaining",
)


@dataclass
class ArenaEntityReport:
    enemy_id: str
    min_spawn_depth: int
    player_wins: int = 0
    enemy_wins: int = 0
    player_win_hp_total: float = 0.0
    player_win_hp_count: int = 0
    enemy_win_hp_total: float = 0.0
    enemy_win_hp_count: int = 0

    def record_player_win(self, hp_percent: float | None) -> None:
        self.player_wins += 1
        if hp_percent is not None:
            self.player_win_hp_total += hp_percent
            self.player_win_hp_count += 1

    def record_enemy_win(self, hp_percent: float | None) -> None:
        self.enemy_wins += 1
        if hp_percent is not None:
            self.enemy_win_hp_total += hp_percent
            self.enemy_win_hp_count += 1

    def player_win_hp_remaining(self) -> str:
        if self.player_win_hp_count == 0:
            return ""
        return str(round(self.player_win_hp_total / self.player_win_hp_count, 1))

    def enemy_win_hp_remaining(self) -> str:
        if self.enemy_win_hp_count == 0:
            return ""
        return str(round(self.enemy_win_hp_total / self.enemy_win_hp_count, 1))


@dataclass
class ArenaBatchResult:
    seed: int
    difficulty_id: str
    trials_per_entity: int
    max_turns: int
    entity_ids: tuple[str, ...]
    reports: list[ArenaEntityReport] = field(default_factory=list)


def evil_entity_ids_sorted() -> list[str]:
    """Evil ids ordered by ``spawn.min_depth`` ascending, then id for ties."""
    registry = load_entity_registry()
    evils = [
        entity
        for entity in registry.entities
        if entity.alignment == Alignment.EVIL
    ]
    evils.sort(key=lambda entity: (entity.spawn.min_depth, entity.id))
    return [entity.id for entity in evils]


def _trial_seed(root_seed: int, entity_index: int, trial: int) -> int:
    mixed = root_seed ^ (entity_index * 1_000_003) ^ (trial * 1_009)
    return mixed & 0x7FFF_FFFF


def run_arena_batch(
    *,
    difficulty_id: str,
    seed: int | None = None,
    trials_per_entity: int = 10,
    max_turns: int = 1000,
    entity_ids: list[str] | None = None,
) -> ArenaBatchResult:
    root_seed = seed if seed is not None else random.randint(0, 2_147_483_647)
    registry = load_entity_registry()
    if entity_ids is not None:
        # Always emit compare-sheet blocks by min_spawn_depth, then id.
        ids = tuple(
            sorted(
                entity_ids,
                key=lambda entity_id: (
                    registry.get(entity_id).spawn.min_depth,
                    entity_id,
                ),
            )
        )
    else:
        ids = tuple(evil_entity_ids_sorted())
    reports: list[ArenaEntityReport] = []

    for entity_index, entity_id in enumerate(ids):
        definition = registry.get(entity_id)
        report = ArenaEntityReport(
            enemy_id=entity_id,
            min_spawn_depth=definition.spawn.min_depth,
        )
        for trial in range(trials_per_entity):
            trial_seed = _trial_seed(root_seed, entity_index, trial)
            result = ArenaSimRun(
                entity_id=entity_id,
                difficulty_id=difficulty_id,
                seed=trial_seed,
                max_turns=max_turns,
            ).run()
            if result.outcome is ArenaTrialOutcome.PLAYER_WIN:
                report.record_player_win(result.player_hp_percent)
            elif result.outcome is ArenaTrialOutcome.ENEMY_WIN:
                report.record_enemy_win(result.enemy_hp_percent)
        reports.append(report)

    return ArenaBatchResult(
        seed=root_seed,
        difficulty_id=difficulty_id,
        trials_per_entity=trials_per_entity,
        max_turns=max_turns,
        entity_ids=ids,
        reports=reports,
    )


def arena_metric_column(entity_ids: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """Stable column-A metric keys (repeated field names per entity, blank row between)."""
    rows: list[str] = list(ARENA_META_ROWS)
    for index, _entity_id in enumerate(entity_ids):
        if index > 0:
            rows.append("")
        rows.extend(ARENA_ENTITY_FIELDS)
    return tuple(rows)


def build_arena_column_values(result: ArenaBatchResult) -> list[str]:
    """One run column aligned to :func:`arena_metric_column`."""
    report_by_id = {report.enemy_id: report for report in result.reports}
    values: list[str] = [
        str(result.seed),
        result.difficulty_id,
        str(result.trials_per_entity),
        str(result.max_turns),
    ]
    for index, entity_id in enumerate(result.entity_ids):
        if index > 0:
            values.append("")
        report = report_by_id[entity_id]
        values.extend(
            [
                report.enemy_id,
                str(report.min_spawn_depth),
                str(report.player_wins),
                str(report.enemy_wins),
                report.player_win_hp_remaining(),
                report.enemy_win_hp_remaining(),
            ]
        )
    return values


def default_arena_column_label(result: ArenaBatchResult) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"{result.difficulty_id}_{result.trials_per_entity}t_{stamp}"


def _read_arena_compare_sheet(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError(f"compare sheet is empty: {path}") from None
        body = [list(row) for row in reader]
    return header, body


def _validate_arena_metric_body(
    body: list[list[str]],
    *,
    entity_ids: tuple[str, ...] | list[str],
) -> None:
    expected = arena_metric_column(entity_ids)
    if len(body) != len(expected):
        raise ValueError(
            f"arena compare sheet row count mismatch: expected {len(expected)}, got {len(body)}"
        )
    for index, (row, metric) in enumerate(zip(body, expected, strict=True)):
        if not row:
            raise ValueError(f"arena compare sheet row {index + 2} is empty")
        if row[0] != metric:
            raise ValueError(
                f"arena compare sheet row {index + 2}: expected metric {metric!r}, got {row[0]!r}"
            )


def write_arena_compare_sheet_csv(
    path: Path,
    *,
    result: ArenaBatchResult,
    column_label: str,
    append: bool = False,
) -> str:
    """Write or append a compare-sheet column (metric + one column per run)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    metrics = arena_metric_column(result.entity_ids)
    values = build_arena_column_values(result)

    if append and path.is_file():
        header, body = _read_arena_compare_sheet(path)
        if len(header) < 2 or header[0] != ARENA_COMPARE_METRIC_COLUMN:
            raise ValueError(f"not an arena compare sheet: {path}")
        if column_label in header:
            raise ValueError(f"column label already exists: {column_label}")
        _validate_arena_metric_body(body, entity_ids=result.entity_ids)
        header.append(column_label)
        for row, value in zip(body, values, strict=True):
            row.append(_format_cell(value))
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            writer.writerows(body)
        return column_label

    header = [ARENA_COMPARE_METRIC_COLUMN, column_label]
    body = [
        [metric, _format_cell(value)]
        for metric, value in zip(metrics, values, strict=True)
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(body)
    return column_label


def should_append_arena_compare_sheet(
    path: Path,
    *,
    append: bool = False,
    overwrite: bool = False,
) -> bool:
    """True when an existing compare sheet should gain a new column."""
    if overwrite:
        return False
    if append:
        return path.is_file()
    return path.is_file()


def write_arena_csv(
    path: Path,
    result: ArenaBatchResult,
    *,
    column_label: str | None = None,
    append: bool = False,
    overwrite: bool = False,
) -> str:
    """Write arena batch output as a compare sheet."""
    label = column_label if column_label is not None else default_arena_column_label(result)
    return write_arena_compare_sheet_csv(
        path,
        result=result,
        column_label=label,
        append=should_append_arena_compare_sheet(
            path,
            append=append,
            overwrite=overwrite,
        ),
    )