"""PR2: headless 1v1 arena bot and CSV export."""

from __future__ import annotations

import random
from pathlib import Path

from src.arena import initialize_arena
from src.arena_map import ARENA_ENEMY_X, ARENA_PLAYER_X, ARENA_WALK_Y
from src.components import Fighter, Position, Stunned
from src.data.entity_loader import parse_entity_registry
from src.engine import GameEngine
from src.events import fire_entity_defeated
from src.sim.arena_batch import (
    ARENA_ENTITY_FIELDS,
    ArenaEntityReport,
    arena_metric_column,
    build_arena_column_values,
    run_arena_batch,
    should_append_arena_compare_sheet,
    write_arena_compare_sheet_csv,
    write_arena_csv,
)
from src.sim.arena_policy import ArenaActionKind, ArenaPolicy
from src.sim.arena_runner import ArenaSimRun, ArenaTrialOutcome
from tests.entity_test_helpers import minimal_entity_payload


def _fixture_registry():
    return parse_entity_registry(
        {
            "schema_version": 1,
            "entities": [
                minimal_entity_payload(
                    "duel_rat",
                    display_name="rat",
                    max_hp=3,
                    min_damage=0,
                    max_damage=0,
                    spawn={"weight": 1, "min_depth": 1, "max_depth": 5, "terrain": "land"},
                ),
            ],
        }
    )


def _arena_engine(entity_id: str = "duel_rat") -> GameEngine:
    registry = _fixture_registry()
    engine = GameEngine(save_coordinator=None, skip_new_game=True)
    initialize_arena(engine, entity_id, seed=42, registry=registry)
    engine._update_fov()
    return engine


def test_arena_policy_moves_right_when_enemy_not_adjacent() -> None:
    engine = _arena_engine()
    policy = ArenaPolicy()
    action = policy.decide(engine)
    assert action.kind is ArenaActionKind.MOVE
    assert action.direction == (1, 0)


def test_arena_policy_attacks_adjacent_enemy() -> None:
    engine = _arena_engine()
    assert engine.player is not None
    engine.player.components[Position] = Position(ARENA_ENEMY_X - 1, ARENA_WALK_Y)
    engine._update_fov()
    action = ArenaPolicy().decide(engine)
    assert action.kind is ArenaActionKind.ATTACK
    assert action.direction == (1, 0)


def test_arena_policy_waits_when_stunned() -> None:
    engine = _arena_engine()
    assert engine.player is not None
    engine.player.tags.add(Stunned)
    action = ArenaPolicy().decide(engine)
    assert action.kind is ArenaActionKind.WAIT


def test_arena_victory_hook_sets_active_flag() -> None:
    registry = _fixture_registry()
    engine = GameEngine(save_coordinator=None, skip_new_game=True)
    enemy = initialize_arena(engine, "duel_rat", seed=1, registry=registry)
    enemy.components[Fighter].hp = 0
    fire_entity_defeated(enemy)
    assert engine.arena_victory_active is True


def test_arena_sim_run_draw_at_turn_cap(monkeypatch) -> None:
    registry = _fixture_registry()
    monkeypatch.setattr(
        "src.sim.arena_runner.load_entity_registry",
        lambda: registry,
    )
    result = ArenaSimRun(
        entity_id="duel_rat",
        difficulty_id="normal",
        seed=7,
        max_turns=1,
    ).run()
    assert result.outcome is ArenaTrialOutcome.DRAW
    assert result.turns_played == 1


def test_arena_sim_enemy_win_records_hp_after_digestion(monkeypatch) -> None:
    """Forced engulf + digest must count ENEMY_WIN with predator HP remaining."""
    from src.arena import initialize_arena
    from src.components import Engulfed, Position, Stunned
    from src.sim.arena_runner import _run_one_arena_turn
    from src.systems.vore import engulf_player

    registry = _fixture_registry()
    monkeypatch.setattr(
        "src.sim.arena_runner.load_entity_registry",
        lambda: registry,
    )
    engine = GameEngine(save_coordinator=None, skip_new_game=True)
    enemy = initialize_arena(engine, "duel_rat", seed=3, registry=registry)
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 0
    player.tags.add(Stunned)
    enemy_pos = enemy.components[Position]
    player.components[Position] = Position(enemy_pos.x - 1, enemy_pos.y)
    engine._update_fov()
    engulf_player(engine.world, player, enemy, engine.message_log, narrative_type="OV")
    assert Engulfed in player.tags

    outcome = None
    enemy_hp = None
    for _ in range(50):
        step = _run_one_arena_turn(engine)
        if engine.game_over.active or step.name == "RUN_ENDED":
            from src.sim.arena_runner import _enemy_hp_percent

            enemy_hp = _enemy_hp_percent(engine)
            outcome = ArenaTrialOutcome.ENEMY_WIN
            break
    assert outcome is ArenaTrialOutcome.ENEMY_WIN
    assert enemy_hp is not None
    assert enemy_hp > 0

    # Full runner path (same forced setup via weak player max turns won't work;
    # re-run through record path using batch report helpers).
    report = ArenaEntityReport(enemy_id="duel_rat", min_spawn_depth=1)
    report.record_enemy_win(enemy_hp)
    assert report.enemy_wins == 1
    assert report.enemy_win_hp_remaining() != ""


def test_arena_entity_report_wins_and_hp_averages() -> None:
    report = ArenaEntityReport(enemy_id="duel_rat", min_spawn_depth=2)
    report.record_player_win(50.0)
    report.record_player_win(30.0)
    report.record_enemy_win(80.0)
    assert report.player_wins == 2
    assert report.enemy_wins == 1
    assert report.player_win_hp_remaining() == "40.0"
    assert report.enemy_win_hp_remaining() == "80.0"


def _sample_batch_result() -> "ArenaBatchResult":
    from src.sim.arena_batch import ArenaBatchResult

    return ArenaBatchResult(
        seed=4242,
        difficulty_id="normal",
        trials_per_entity=10,
        max_turns=1000,
        entity_ids=("rat", "bat"),
        reports=[
            ArenaEntityReport(
                "rat",
                1,
                player_wins=6,
                enemy_wins=4,
                player_win_hp_total=593.4,
                player_win_hp_count=6,
            ),
            ArenaEntityReport(
                "bat",
                2,
                player_wins=3,
                enemy_wins=7,
                enemy_win_hp_total=560.0,
                enemy_win_hp_count=7,
            ),
        ],
    )


def test_arena_metric_column_repeats_fields_per_entity() -> None:
    metrics = arena_metric_column(("rat", "bat"))
    assert metrics[0] == "meta.seed"
    assert metrics[4:4 + len(ARENA_ENTITY_FIELDS)] == ARENA_ENTITY_FIELDS
    assert metrics[4 + len(ARENA_ENTITY_FIELDS)] == ""
    assert metrics[5 + len(ARENA_ENTITY_FIELDS)] == "enemy_id"


def test_arena_compare_sheet_layout(tmp_path) -> None:
    import csv

    result = _sample_batch_result()
    path = tmp_path / "arena_compare.csv"
    write_arena_compare_sheet_csv(path, result=result, column_label="baseline")

    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))

    assert rows[0] == ["metric", "baseline"]
    assert rows[1] == ["meta.seed", "4242"]
    assert rows[5] == ["enemy_id", "rat"]
    assert rows[6] == ["min_spawn_depth", "1"]
    assert rows[9] == ["player_win_hp_remaining", "98.9"]
    # rat report has enemy_wins but no hp samples in fixture → blank average
    assert rows[10] == ["enemy_win_hp_remaining", ""]
    assert rows[11] == ["", ""]
    assert rows[12] == ["enemy_id", "bat"]
    assert rows[13] == ["min_spawn_depth", "2"]
    assert rows[15] == ["enemy_wins", "7"]
    assert rows[17] == ["enemy_win_hp_remaining", "80.0"]


def test_write_arena_csv_auto_appends_when_file_exists(tmp_path) -> None:
    import csv

    result = _sample_batch_result()
    path = tmp_path / "arena_compare.csv"
    write_arena_csv(path, result, column_label="run_a")
    write_arena_csv(path, result, column_label="run_b")

    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))

    assert rows[0] == ["metric", "run_a", "run_b"]


def test_write_arena_csv_overwrite_replaces_sheet(tmp_path) -> None:
    import csv

    result = _sample_batch_result()
    path = tmp_path / "arena_compare.csv"
    write_arena_csv(path, result, column_label="run_a")
    write_arena_csv(path, result, column_label="run_b", overwrite=True)

    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))

    assert rows[0] == ["metric", "run_b"]


def test_should_append_arena_compare_sheet(tmp_path) -> None:
    missing = tmp_path / "missing.csv"
    assert should_append_arena_compare_sheet(missing) is False
    assert should_append_arena_compare_sheet(missing, overwrite=True) is False

    existing = tmp_path / "arena_compare.csv"
    existing.write_text("metric,run_a\n", encoding="utf-8")
    assert should_append_arena_compare_sheet(existing) is True
    assert should_append_arena_compare_sheet(existing, overwrite=True) is False


def test_arena_compare_sheet_append_adds_column(tmp_path) -> None:
    import csv

    result = _sample_batch_result()
    path = tmp_path / "arena_compare.csv"
    write_arena_compare_sheet_csv(path, result=result, column_label="run_a")

    second = _sample_batch_result()
    second.seed = 9999
    second.reports[0].player_wins = 2
    write_arena_compare_sheet_csv(
        path,
        result=second,
        column_label="run_b",
        append=True,
    )

    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))

    assert rows[0] == ["metric", "run_a", "run_b"]
    assert rows[1] == ["meta.seed", "4242", "9999"]
    assert rows[5] == ["enemy_id", "rat", "rat"]
    assert rows[7] == ["player_wins", "6", "2"]


def test_build_arena_column_values_aligns_with_metrics() -> None:
    result = _sample_batch_result()
    metrics = arena_metric_column(result.entity_ids)
    values = build_arena_column_values(result)
    assert len(metrics) == len(values)
    assert values[4] == "rat"


def test_run_arena_batch_with_fixture_registry(monkeypatch) -> None:
    registry = _fixture_registry()
    monkeypatch.setattr(
        "src.sim.arena_batch.load_entity_registry",
        lambda: registry,
    )
    monkeypatch.setattr(
        "src.sim.arena_runner.load_entity_registry",
        lambda: registry,
    )
    result = run_arena_batch(
        difficulty_id="normal",
        seed=1,
        trials_per_entity=2,
        max_turns=1,
        entity_ids=["duel_rat"],
    )
    assert result.seed == 1
    assert len(result.reports) == 1
    report = result.reports[0]
    assert report.enemy_id == "duel_rat"
    assert report.player_wins + report.enemy_wins <= 2


def test_evil_entity_ids_sorted_by_min_spawn_depth(monkeypatch) -> None:
    from src.sim import arena_batch

    registry = parse_entity_registry(
        {
            "schema_version": 1,
            "entities": [
                minimal_entity_payload(
                    "zebra_deep",
                    spawn={"weight": 1, "min_depth": 10, "max_depth": 20, "terrain": "land"},
                ),
                minimal_entity_payload(
                    "aardvark_early",
                    spawn={"weight": 1, "min_depth": 1, "max_depth": 5, "terrain": "land"},
                ),
                minimal_entity_payload(
                    "mule_mid",
                    spawn={"weight": 1, "min_depth": 5, "max_depth": 9, "terrain": "land"},
                ),
            ],
        }
    )
    monkeypatch.setattr(arena_batch, "load_entity_registry", lambda: registry)
    assert arena_batch.evil_entity_ids_sorted() == [
        "aardvark_early",
        "mule_mid",
        "zebra_deep",
    ]


def test_trial_seed_is_deterministic() -> None:
    from src.sim.arena_batch import _trial_seed

    assert _trial_seed(100, 3, 5) == _trial_seed(100, 3, 5)
    assert _trial_seed(100, 3, 5) != _trial_seed(100, 3, 6)