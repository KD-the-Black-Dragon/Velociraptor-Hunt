"""Per-user writable data directory (saves, settings, logs, past runs, mods)."""

from __future__ import annotations

import os
from pathlib import Path

import platformdirs

APP_NAME = "KD's Vore Roguelike"
_USER_DATA_OVERRIDE_ENV = "KDS_USER_DATA_DIR"


def _resolve_user_data_dir() -> Path:
    override = os.environ.get(_USER_DATA_OVERRIDE_ENV)
    if override:
        return Path(override)
    return Path(platformdirs.user_data_dir(APP_NAME, appauthor=False))


USER_DATA_DIR = _resolve_user_data_dir()
SAVES_DIR = USER_DATA_DIR / "saves"
PAST_RUNS_PATH = USER_DATA_DIR / "past_runs.json"
SETTINGS_PATH = USER_DATA_DIR / "settings.json"
LOGS_DIR = USER_DATA_DIR / "logs"
MODS_DIR = USER_DATA_DIR / "mods"