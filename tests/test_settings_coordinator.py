"""Background settings.json writer."""

from __future__ import annotations

import json

from src.settings_coordinator import SettingsCoordinator
from src.settings_store import SettingsStore


def test_coordinator_writes_enqueued_settings(tmp_path) -> None:
    path = tmp_path / "settings.json"
    coordinator = SettingsCoordinator()
    settings = SettingsStore(path=path)
    settings.window = settings.window.__class__(
        client_width=1500,
        client_height=860,
        x=12,
        y=34,
    )
    coordinator.enqueue(settings)
    coordinator.flush()

    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["window"]["client_width"] == 1500
    assert raw["window"]["y"] == 34
    coordinator.close()


def test_coordinator_keeps_latest_snapshot(tmp_path) -> None:
    path = tmp_path / "settings.json"
    coordinator = SettingsCoordinator()
    settings = SettingsStore(path=path)
    for width in (1400, 1500, 1600):
        settings.window = settings.window.__class__(client_width=width, client_height=800)
        coordinator.enqueue(settings)
    coordinator.flush()
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["window"]["client_width"] == 1600
    coordinator.close()