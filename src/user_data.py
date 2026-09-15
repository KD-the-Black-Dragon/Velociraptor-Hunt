"""Per-user writable data directory (saves, settings, logs, past runs, mods)."""

from __future__ import annotations

import os
from pathlib import Path

import platformdirs

APP_NAME = "Velociraptor Hunt"
# Prefer hunt env; accept Gladiavore/KDVR overrides so existing test harnesses keep working.
_USER_DATA_OVERRIDE_ENV = "VELOCIRAPTOR_HUNT_USER_DATA_DIR"
_USER_DATA_OVERRIDE_ENV_GLADIAVORE = "GLADIAVORE_USER_DATA_DIR"
_USER_DATA_OVERRIDE_ENV_LEGACY = "KDS_USER_DATA_DIR"


def _resolve_user_data_dir() -> Path:
    override = (
        os.environ.get(_USER_DATA_OVERRIDE_ENV)
        or os.environ.get(_USER_DATA_OVERRIDE_ENV_GLADIAVORE)
        or os.environ.get(_USER_DATA_OVERRIDE_ENV_LEGACY)
    )
    if override:
        return Path(override)
    return Path(platformdirs.user_data_dir(APP_NAME, appauthor=False))


USER_DATA_DIR = _resolve_user_data_dir()
SAVES_DIR = USER_DATA_DIR / "saves"
PAST_RUNS_PATH = USER_DATA_DIR / "past_runs.json"
HUNT_STATS_PATH = USER_DATA_DIR / "hunt_stats.json"
SETTINGS_PATH = USER_DATA_DIR / "settings.json"
LOGS_DIR = USER_DATA_DIR / "logs"
MODS_DIR = USER_DATA_DIR / "mods"