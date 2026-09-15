"""User-writable data directory layout."""

from __future__ import annotations

from src.user_data import (
    APP_NAME,
    HUNT_STATS_PATH,
    LOGS_DIR,
    PAST_RUNS_PATH,
    SAVES_DIR,
    SETTINGS_PATH,
    USER_DATA_DIR,
)


def test_user_data_dir_name() -> None:
    assert APP_NAME == "Velociraptor Hunt"
    assert USER_DATA_DIR.name == APP_NAME


def test_user_data_layout() -> None:
    assert SAVES_DIR == USER_DATA_DIR / "saves"
    assert PAST_RUNS_PATH == USER_DATA_DIR / "past_runs.json"
    assert HUNT_STATS_PATH == USER_DATA_DIR / "hunt_stats.json"
    assert SETTINGS_PATH == USER_DATA_DIR / "settings.json"
    assert LOGS_DIR == USER_DATA_DIR / "logs"