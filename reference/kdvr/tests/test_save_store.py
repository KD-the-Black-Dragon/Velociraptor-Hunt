"""PR2: rotating autosave file store."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.engine import GameEngine
from src.save.store import (
    BAK1_NAME,
    BAK2_NAME,
    BAK3_NAME,
    PRIMARY_NAME,
    TMP_NAME,
    SaveNotFoundError,
    SaveStore,
    compute_payload_sha256,
)
from src.save.snapshot import build_run_snapshot

from tests.map_test_helpers import isolate_other_ais


def _minimal_run(*, player_name: str = "Tester") -> dict:
    engine = GameEngine(player_name=player_name)
    isolate_other_ais(engine)
    run = build_run_snapshot(engine)
    run["player_name"] = player_name
    return run


def test_probe_false_when_directory_empty(tmp_path: Path) -> None:
    store = SaveStore(tmp_path)
    assert not store.probe()


def test_probe_true_after_valid_save(tmp_path: Path) -> None:
    store = SaveStore(tmp_path)
    store.save_run(_minimal_run())
    assert store.probe()
    assert store.primary_path().is_file()


def test_write_and_rotate_produces_backup_chain(tmp_path: Path) -> None:
    store = SaveStore(tmp_path)
    names = ["first", "second", "third", "fourth", "fifth"]

    for name in names:
        store.save_run(_minimal_run(player_name=name), saved_at_unix=100)

    assert store.path_for(PRIMARY_NAME).is_file()
    assert store.path_for(BAK1_NAME).is_file()
    assert store.path_for(BAK2_NAME).is_file()
    assert store.path_for(BAK3_NAME).is_file()
    assert not store.path_for(TMP_NAME).exists()

    loaded = store.load_best()
    assert loaded["player_name"] == "fifth"

    bak3_run = json.loads(store.path_for(BAK3_NAME).read_text(encoding="utf-8"))["run"]
    assert bak3_run["player_name"] == "second"


def test_corrupt_primary_falls_back_to_bak1(tmp_path: Path) -> None:
    store = SaveStore(tmp_path)
    store.save_run(_minimal_run(player_name="older"), saved_at_unix=10)
    store.save_run(_minimal_run(player_name="newer"), saved_at_unix=20)

    primary_path = store.path_for(PRIMARY_NAME)
    document = json.loads(primary_path.read_text(encoding="utf-8"))
    document["payload_sha256"] = "0" * 64
    primary_path.write_text(json.dumps(document), encoding="utf-8")

    loaded = store.load_best()
    assert loaded["player_name"] == "older"


def test_delete_all_removes_slot_files(tmp_path: Path) -> None:
    store = SaveStore(tmp_path)
    for index in range(4):
        store.save_run(_minimal_run(player_name=f"run-{index}"), saved_at_unix=index)

    store.delete_all()

    for name in (PRIMARY_NAME, BAK1_NAME, BAK2_NAME, BAK3_NAME, TMP_NAME):
        assert not store.path_for(name).exists()
    assert not store.probe()


def test_load_best_raises_when_no_valid_files(tmp_path: Path) -> None:
    store = SaveStore(tmp_path)
    with pytest.raises(SaveNotFoundError):
        store.load_best()


def test_round_trip_engine_snapshot_through_store(tmp_path: Path) -> None:
    engine = GameEngine(player_name="Persisted")
    isolate_other_ais(engine)
    engine.player_turn_count = 42

    store = SaveStore(tmp_path)
    store.save_run(build_run_snapshot(engine))

    restored = GameEngine.from_run_snapshot(store.load_best())
    assert restored.player_name == "Persisted"
    assert restored.player_turn_count == 42


def test_compute_payload_sha256_is_stable() -> None:
    run = _minimal_run(player_name="hash-check")
    assert compute_payload_sha256(run) == compute_payload_sha256(run.copy())