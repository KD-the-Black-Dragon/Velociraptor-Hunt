"""spawn.py must not eager-load entities.json at import."""

from __future__ import annotations

import importlib

from src.data.entity_loader import load_entity_registry


def test_import_spawn_does_not_load_registry(monkeypatch) -> None:
    calls: list[object] = []

    def track_load(path=None):
        calls.append(path)
        return load_entity_registry(path)

    import src.spawn as spawn_module

    importlib.reload(spawn_module)
    monkeypatch.setattr(spawn_module, "load_entity_registry", track_load)
    spawn_module._get_registry.cache_clear()

    assert calls == []

    # Direct registry access is the production load point (lazy attrs call this).
    _ = spawn_module._get_registry()
    assert len(calls) == 1

    # Lazy module attributes also resolve via the same path.
    spawn_module._get_registry.cache_clear()
    calls.clear()
    _ = spawn_module.renderable_for("wolf")
    assert len(calls) == 1

    spawn_module._get_registry.cache_clear()
