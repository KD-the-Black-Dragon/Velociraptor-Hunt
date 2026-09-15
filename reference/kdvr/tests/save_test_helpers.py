"""Helpers for tests that need an App without a real autosave on disk."""

from __future__ import annotations

from pathlib import Path

from src.app import App
from src.past_runs.store import PastRunsStore
from src.save.coordinator import SaveCoordinator
from src.save.store import SaveStore


def app_with_isolated_save(tmp_path: Path, **kwargs) -> App:
    """App whose autosave and past-runs files are confined to a pytest temp directory."""
    store = SaveStore(tmp_path / "saves")
    past_runs = PastRunsStore(tmp_path / "past_runs.json")
    coordinator = SaveCoordinator(store=store)
    return App(
        save_coordinator=coordinator,
        past_runs_store=past_runs,
        **kwargs,
    )