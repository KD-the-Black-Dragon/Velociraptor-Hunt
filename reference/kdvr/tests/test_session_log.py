"""PR1: session log coordinator and paths."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.debug import paths as debug_paths
from src.debug.session_log import SessionLogCoordinator
from src.debug.version_info import get_game_version


@pytest.fixture
def logs_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    log_root = tmp_path / "logs"
    monkeypatch.setattr(debug_paths, "LOGS_DIR", log_root)
    return log_root


def test_log_no_op_before_start_session() -> None:
    coordinator = SessionLogCoordinator()
    coordinator.log("Started new game")
    assert coordinator.session_path is None


def test_start_session_creates_logs_dir_and_file(logs_dir: Path) -> None:
    coordinator = SessionLogCoordinator()
    coordinator.start_session()
    try:
        assert coordinator.session_path is not None
        assert coordinator.session_path.parent == logs_dir
        assert coordinator.session_path.name.startswith("session_")
        assert logs_dir.is_dir()
        assert coordinator.session_path.is_file()
        assert coordinator.session_path.read_text(encoding="utf-8") == ""
    finally:
        coordinator.close()


def test_start_session_is_idempotent(logs_dir: Path) -> None:
    coordinator = SessionLogCoordinator()
    coordinator.start_session()
    first = coordinator.session_path
    coordinator.start_session()
    try:
        assert coordinator.session_path == first
    finally:
        coordinator.close()


def test_worker_writes_enqueued_lines(logs_dir: Path) -> None:
    coordinator = SessionLogCoordinator()
    coordinator.start_session()
    try:
        coordinator.log("Started new game")
        coordinator.log("Seed: 42")
        coordinator.flush()
        path = coordinator.session_path
        assert path is not None
        text = path.read_text(encoding="utf-8")
        assert "Started new game\n" in text
        assert "Seed: 42\n" in text
    finally:
        coordinator.close()


def test_log_strips_newlines_and_skips_empty(logs_dir: Path) -> None:
    coordinator = SessionLogCoordinator()
    coordinator.start_session()
    try:
        coordinator.log("  line one  \n")
        coordinator.log("")
        coordinator.log("   ")
        coordinator.flush()
        path = coordinator.session_path
        assert path is not None
        assert path.read_text(encoding="utf-8") == "line one\n"
    finally:
        coordinator.close()


def test_session_log_path_uses_local_timestamp(monkeypatch: pytest.MonkeyPatch) -> None:
    fixed = datetime(2026, 7, 7, 19, 14, 3, tzinfo=timezone.utc)
    monkeypatch.setattr(debug_paths, "LOGS_DIR", Path("/tmp/logs"))
    assert debug_paths.session_log_path(at=fixed) == Path(
        "/tmp/logs/session_2026-07-07_19-14-03.log"
    )


def test_crash_log_path_under_logs_dir(logs_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(debug_paths, "LOGS_DIR", logs_dir)
    assert debug_paths.crash_log_path() == logs_dir / "crash.log"


def test_get_game_version_reads_pyproject() -> None:
    assert get_game_version() == "0.1.0"