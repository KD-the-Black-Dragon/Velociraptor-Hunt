"""Helpers for tests that need an App without a real autosave on disk."""

from __future__ import annotations

from pathlib import Path

from src.app import App
from src.career_store import CareerStore
from src.hunt_stats import HuntStatsStore
from src.past_runs.store import PastRunsStore
from src.save.coordinator import SaveCoordinator
from src.save.store import SaveStore
from src.settings_store import SettingsStore


def app_with_isolated_save(tmp_path: Path, **kwargs) -> App:
    """App whose autosave, career, past-runs, and settings use a pytest temp directory.

    Fresh product user-data dirs (e.g. first Gladiavore launch) start with onboarding
    flags false; tests that expect the main menu skip that by default here.
    """
    saves_dir = tmp_path / "saves"
    store = SaveStore(saves_dir)
    past_runs = PastRunsStore(tmp_path / "past_runs.json")
    hunt_stats = HuntStatsStore(tmp_path / "hunt_stats.json")
    coordinator = SaveCoordinator(store=store)
    if "settings" not in kwargs:
        kwargs["settings"] = SettingsStore(
            path=tmp_path / "settings.json",
            tutorial_prompt_answered=True,
            vore_prefs_onboarding_complete=True,
        )
    if "career_store" not in kwargs:
        kwargs["career_store"] = CareerStore(saves_dir)
    return App(
        save_coordinator=coordinator,
        past_runs_store=past_runs,
        hunt_stats_store=hunt_stats,
        **kwargs,
    )