"""PR4: background floor map prefetch."""

from __future__ import annotations

from unittest.mock import patch

from src.floor_prefetch import (
    FloorPrefetch,
    PrefetchParams,
    _ProcessBackend,
    _ThreadBackend,
    menu_prefetch_params,
)
from src.map_gen import GameMap


def _params(**overrides) -> PrefetchParams:
    base = {
        "map_width": 20,
        "map_height": 12,
        "water_testing": False,
        "layout_archetype_force": None,
        "seed": None,
        "depth": 1,
    }
    base.update(overrides)
    return PrefetchParams(**base)


def _test_prefetch() -> FloorPrefetch:
    return FloorPrefetch(use_process=False)


def test_take_returns_none_when_empty() -> None:
    prefetch = _test_prefetch()
    try:
        assert prefetch.take(_params()) is None
    finally:
        prefetch.shutdown()


def test_schedule_and_take_returns_ready_map() -> None:
    expected = GameMap(20, 12)
    prefetch = _test_prefetch()
    params = _params()
    try:
        with patch("src.floor_prefetch.generate_dungeon", return_value=expected):
            prefetch.schedule(params)
            result = prefetch.take(params)
        assert result is expected
        assert prefetch.take(params) is None
    finally:
        prefetch.shutdown()


def test_params_mismatch_discards_cached_map() -> None:
    expected = GameMap(20, 12)
    prefetch = _test_prefetch()
    scheduled = _params(water_testing=False)
    consume = _params(water_testing=True)
    try:
        with patch("src.floor_prefetch.generate_dungeon", return_value=expected):
            prefetch.schedule(scheduled)
            assert prefetch.take(consume) is None
            assert prefetch.take(scheduled) is expected
    finally:
        prefetch.shutdown()


def test_cancel_prevents_take() -> None:
    expected = GameMap(20, 12)
    prefetch = _test_prefetch()
    params = _params()
    try:
        with patch("src.floor_prefetch.generate_dungeon", return_value=expected):
            prefetch.schedule(params)
            prefetch.cancel()
            assert prefetch.take(params) is None
    finally:
        prefetch.shutdown()


def test_menu_prefetch_params_use_stock_defaults() -> None:
    params = menu_prefetch_params(seed=None)
    assert params.depth == 1
    assert params.seed is None


def test_frozen_app_uses_process_backend(monkeypatch) -> None:
    import sys

    monkeypatch.setattr(sys, "frozen", True, raising=False)

    prefetch = FloorPrefetch(use_process=True)
    try:
        assert isinstance(prefetch._backend, _ProcessBackend)
    finally:
        prefetch.shutdown()


def test_engine_take_or_generate_uses_prefetch(monkeypatch) -> None:
    from src.engine import GameEngine
    from src.floor_prefetch import FloorPrefetch

    calls = {"sync": 0}
    cached = GameMap(20, 12)

    def fake_generate(*args, **kwargs):
        calls["sync"] += 1
        return GameMap(20, 12)

    monkeypatch.setattr("src.engine_floor.generate_dungeon", fake_generate)

    engine = GameEngine.__new__(GameEngine)
    engine.water_testing_mode = False
    engine.layout_archetype_force = None
    engine.floor_depth = 1
    engine.difficulty_id = "normal"
    engine.floor_prefetch = FloorPrefetch(use_process=False)
    params = menu_prefetch_params(seed=None)
    try:
        with patch("src.floor_prefetch.generate_dungeon", return_value=cached):
            engine.floor_prefetch.schedule(params)
            result = engine._take_or_generate_dungeon(seed=None)
        assert result is cached
        assert calls["sync"] == 0
    finally:
        engine.floor_prefetch.shutdown()