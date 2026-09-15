"""PR2: startup JSON error dialog, log, and stderr."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.debug import paths as debug_paths
from src.debug.startup_error import (
    STARTUP_JSON_ERROR_HEADING,
    append_startup_error_log,
    format_startup_error_display,
    format_startup_error_log_entry,
    format_startup_error_timestamp,
    report_startup_json_error,
)


@pytest.fixture
def logs_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    log_root = tmp_path / "logs"
    monkeypatch.setattr(debug_paths, "LOGS_DIR", log_root)
    return log_root


def test_format_startup_error_timestamp() -> None:
    fixed = datetime(2026, 7, 6, 9, 56, tzinfo=timezone.utc)
    assert format_startup_error_timestamp(at=fixed) == "7/6/2026 9:56 AM"


def test_format_startup_error_display_includes_heading() -> None:
    detail = "entities.json\n\nProblem:\nbad field"
    text = format_startup_error_display(detail)
    assert text.startswith(STARTUP_JSON_ERROR_HEADING)
    assert "entities.json" in text


def test_append_startup_error_log_creates_and_appends(logs_dir: Path) -> None:
    fixed = datetime(2026, 7, 6, 9, 56, tzinfo=timezone.utc)
    append_startup_error_log("entities.json\n\nProblem:\nfirst", at=fixed)
    append_startup_error_log("entities.json\n\nProblem:\nsecond", at=fixed)

    path = logs_dir / "startup_error.log"
    text = path.read_text(encoding="utf-8")
    assert text.count("7/6/2026 9:56 AM") == 2
    assert "Problem:\nfirst" in text
    assert "Problem:\nsecond" in text
    assert text.index("first") < text.index("second")


def test_format_startup_error_log_entry() -> None:
    fixed = datetime(2026, 7, 6, 9, 56, tzinfo=timezone.utc)
    entry = format_startup_error_log_entry("entities.json\n\nProblem:\nx", at=fixed)
    assert entry.startswith("7/6/2026 9:56 AM\n")
    assert STARTUP_JSON_ERROR_HEADING in entry
    assert entry.endswith("\n\n")


def test_report_startup_json_error_stderr_log_and_dialog(
    logs_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dialog_calls: list[str] = []

    def fake_dialog(text: str) -> None:
        dialog_calls.append(text)

    monkeypatch.setattr(
        "src.debug.startup_error.show_startup_error_dialog",
        fake_dialog,
    )

    detail = "entities.json\n\nEntity: wolf\n\nProblem:\nbad"
    report_startup_json_error(detail)

    captured = capsys.readouterr()
    assert STARTUP_JSON_ERROR_HEADING in captured.err
    assert "Entity: wolf" in captured.err
    assert (logs_dir / "startup_error.log").is_file()
    assert dialog_calls and STARTUP_JSON_ERROR_HEADING in dialog_calls[0]