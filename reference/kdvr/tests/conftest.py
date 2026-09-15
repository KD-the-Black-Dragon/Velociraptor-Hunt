"""Shared pytest hooks.

Mechanics tests should pin JSON via tests/*_test_helpers fixtures, not assert
fixed damage/health/spawn counts from live data/ files you tune during playtest.

Policy (fix-tests-decouple-live-data):
- Do not pin live balance (stats, depths, spawn weights, narrative phrases).
- Live-file tests may only smoke-load (parses, schema_version, non-empty).
- Behavior tests use inline fixtures / spawn_test_npc / tmp_path JSON.
"""

from __future__ import annotations

import pytest

from src.data.entity_loader import reset_entity_registry_cache
from tests.item_test_helpers import clear_item_registry


@pytest.fixture(autouse=True)
def _isolate_mods_and_entity_cache(
    tmp_path_factory: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty mods root so default layered entity load is core-only under pytest."""
    empty_mods = tmp_path_factory.mktemp("pytest_mods")
    monkeypatch.setattr("src.user_data.MODS_DIR", empty_mods)
    reset_entity_registry_cache()
    yield
    reset_entity_registry_cache()


@pytest.fixture(autouse=True)
def _reset_item_registry_after_each_test() -> None:
    yield
    clear_item_registry()