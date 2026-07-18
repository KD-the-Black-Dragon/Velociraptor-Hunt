"""Append-only local history of completed runs."""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import Any

from src.past_runs.schema import (
    MAX_PAST_RUNS,
    PAST_RUNS_FORMAT_VERSION,
    PastRunRecord,
    parse_display_date,
    parse_record,
    record_to_dict,
)

from src.user_data import PAST_RUNS_PATH

PAST_RUNS_FILENAME = "past_runs.json"
TMP_FILENAME = "past_runs.tmp"


class PastRunsStoreError(Exception):
    """Base error for past-runs file operations."""


def today_display_date() -> str:
    """Local calendar date as MM/DD/YYYY."""
    today = date.today()
    return f"{today.month:02d}/{today.day:02d}/{today.year:04d}"


def sorted_for_display(runs: list[PastRunRecord]) -> list[PastRunRecord]:
    """Depth desc, runes desc, monsters desc, date asc (older first)."""
    return sorted(
        runs,
        key=lambda record: (
            -record.depth,
            -record.runes_collected,
            -record.monsters_defeated,
            parse_display_date(record.date),
        ),
    )


class PastRunsStore:
    """JSON file store for completed run history."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path if path is not None else PAST_RUNS_PATH

    def probe(self) -> bool:
        """True when the file exists and contains at least one valid run."""
        return len(self.load_runs()) > 0

    def load_runs(self) -> list[PastRunRecord]:
        """Parse all valid entries; corrupt or missing file yields empty list."""
        if not self.path.is_file():
            return []
        try:
            document = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return []
        if not isinstance(document, dict):
            return []
        if document.get("past_runs_format_version") != PAST_RUNS_FORMAT_VERSION:
            return []
        raw_runs = document.get("runs")
        if not isinstance(raw_runs, list):
            return []
        runs: list[PastRunRecord] = []
        for entry in raw_runs:
            record = parse_record(entry)
            if record is not None:
                runs.append(record)
        return runs

    def append(self, record: PastRunRecord) -> None:
        """Append one run, evicting the oldest when at capacity."""
        runs = self.load_runs()
        runs.append(record)
        if len(runs) > MAX_PAST_RUNS:
            runs = runs[-MAX_PAST_RUNS:]
        self._write_runs(runs)

    def _write_runs(self, runs: list[PastRunRecord]) -> None:
        document: dict[str, Any] = {
            "past_runs_format_version": PAST_RUNS_FORMAT_VERSION,
            "runs": [record_to_dict(record) for record in runs],
        }
        data = json.dumps(
            document,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.parent / TMP_FILENAME
        try:
            with tmp_path.open("wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_path, self.path)
        except OSError as exc:
            raise PastRunsStoreError("could not write past runs file") from exc