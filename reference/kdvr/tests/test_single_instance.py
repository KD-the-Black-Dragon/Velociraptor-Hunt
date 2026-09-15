"""Single-instance startup guard."""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

from src.single_instance import (
    block_second_instance,
    release_single_instance,
    try_acquire_single_instance,
)


@pytest.fixture(autouse=True)
def _release_lock_after_test() -> None:
    yield
    release_single_instance()


def test_try_acquire_succeeds_when_unheld(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("KDS_USER_DATA_DIR", str(tmp_path))
    assert try_acquire_single_instance() is True


def test_release_allows_reacquire(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("KDS_USER_DATA_DIR", str(tmp_path))
    assert try_acquire_single_instance() is True
    release_single_instance()
    assert try_acquire_single_instance() is True


def test_skip_env_disables_enforcement(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KDS_SKIP_SINGLE_INSTANCE", "1")
    assert try_acquire_single_instance() is True
    assert try_acquire_single_instance() is True


def test_block_second_instance_returns_false_when_held(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("KDS_USER_DATA_DIR", str(tmp_path))
    assert try_acquire_single_instance() is True

    script = textwrap.dedent(
        f"""
        import os
        os.environ["KDS_USER_DATA_DIR"] = {str(tmp_path)!r}
        os.environ["KDS_SKIP_STARTUP_DIALOG"] = "1"
        from src.single_instance import try_acquire_single_instance
        raise SystemExit(0 if try_acquire_single_instance() else 17)
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode == 17, result.stdout + result.stderr


def test_second_process_can_acquire_after_release(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("KDS_USER_DATA_DIR", str(tmp_path))
    assert try_acquire_single_instance() is True
    release_single_instance()

    script = textwrap.dedent(
        f"""
        import os
        os.environ["KDS_USER_DATA_DIR"] = {str(tmp_path)!r}
        from src.single_instance import try_acquire_single_instance
        raise SystemExit(0 if try_acquire_single_instance() else 19)
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr