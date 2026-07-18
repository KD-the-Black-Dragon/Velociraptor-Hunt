"""Shared pytest hooks for Gladiavore product tests."""

from __future__ import annotations

import pytest

from src.data.entity_loader import reset_entity_registry_cache


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
