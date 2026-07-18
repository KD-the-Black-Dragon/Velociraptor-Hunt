"""PR2: pre-window entities.json validation via main()."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from src.constants import PROJECT_ROOT
from src.debug import paths as debug_paths
from src.debug.session_log import (
    reset_quit_milestone_state,
    should_log_quit_milestone,
    skip_quit_milestone,
)


@pytest.fixture(autouse=True)
def _reset_quit_skip() -> None:
    reset_quit_milestone_state()
    yield
    reset_quit_milestone_state()


def test_skip_quit_milestone_suppresses_flag() -> None:
    skip_quit_milestone(reason="startup_validation")
    assert not should_log_quit_milestone()
    reset_quit_milestone_state()
    assert should_log_quit_milestone()


def test_startup_validation_failure_subprocess(tmp_path: Path) -> None:
    shutil.copytree(PROJECT_ROOT / "src", tmp_path / "src")
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    shutil.copytree(PROJECT_ROOT / "data", data_dir, dirs_exist_ok=True)
    (data_dir / "entities.json").write_text("{ invalid json", encoding="utf-8")

    env = {
        **os.environ,
        "KDS_SKIP_STARTUP_DIALOG": "1",
        "KDS_USER_DATA_DIR": str(tmp_path),
    }
    result = subprocess.run(
        [sys.executable, "-m", "src.main"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 1
    assert "Unable to start the game due to JSON error." in result.stderr
    assert "entities.json" in result.stderr
    assert "Problem:" in result.stderr
    assert "Traceback" not in result.stderr

    startup_log = tmp_path / "logs" / "startup_error.log"
    assert startup_log.is_file()
    assert "Unable to start the game due to JSON error." in startup_log.read_text(
        encoding="utf-8"
    )

    log_dir = tmp_path / "logs"
    session_files = list(log_dir.glob("session_*.log")) if log_dir.is_dir() else []
    assert session_files, "expected session log from start_session"
    for session_file in session_files:
        assert "Quit" not in session_file.read_text(encoding="utf-8")


def test_startup_validation_failure_in_process(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.data import entity_validation

    broken = tmp_path / "entities.json"
    broken.write_text("{", encoding="utf-8")
    monkeypatch.setattr(entity_validation, "ENTITIES_PATH", broken)
    monkeypatch.setattr(debug_paths, "LOGS_DIR", tmp_path / "logs")
    monkeypatch.setenv("KDS_SKIP_STARTUP_DIALOG", "1")
    reset_quit_milestone_state()

    from src.main import main

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1
    assert not should_log_quit_milestone()