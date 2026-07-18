"""Background prefetch of validated dungeon map geometry.

Map generation is CPU-heavy. A thread still fights the main loop for the GIL,
so production uses a single-worker process pool to run generation on another core.
"""

from __future__ import annotations

import multiprocessing as mp
import os
import threading
from concurrent.futures import Future, ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Protocol

from src.debug_log import debug_print
from src.constants import (
    FLOOR_DEPTH_START,
    LAYOUT_ARCHETYPE_FORCE,
    MAP_HEIGHT,
    MAP_WIDTH,
    MAX_ROOMS,
    ROOM_MAX_SIZE,
    ROOM_MIN_SIZE,
    RUNES_PER_FLOOR,
    WATER_TESTING_MODE,
)
from src.map_gen import GameMap, generate_dungeon


@dataclass(frozen=True)
class PrefetchParams:
    """Snapshot of generation inputs; depth is advisory for logging only."""

    map_width: int
    map_height: int
    water_testing: bool
    layout_archetype_force: str | None
    seed: int | None
    depth: int
    runes_per_floor: int = RUNES_PER_FLOOR

    def matches(self, other: PrefetchParams) -> bool:
        """Return True when consume-time params match the cached job."""
        return (
            self.map_width == other.map_width
            and self.map_height == other.map_height
            and self.water_testing == other.water_testing
            and self.layout_archetype_force == other.layout_archetype_force
            and self.seed == other.seed
            and self.runes_per_floor == other.runes_per_floor
        )


def menu_prefetch_params(*, seed: int | None = None) -> PrefetchParams:
    """Params for depth-1 prefetch while the player is on the title flow."""
    try:
        from src.systems.floor_runes import configured_runes_per_floor

        rpf = configured_runes_per_floor()
    except Exception:
        rpf = RUNES_PER_FLOOR
    return PrefetchParams(
        map_width=MAP_WIDTH,
        map_height=MAP_HEIGHT,
        water_testing=WATER_TESTING_MODE,
        layout_archetype_force=LAYOUT_ARCHETYPE_FORCE,
        seed=seed,
        depth=FLOOR_DEPTH_START,
        runes_per_floor=rpf,
    )


def _generate_worker(params: PrefetchParams) -> GameMap:
    """Top-level worker entrypoint (must stay importable for process spawn)."""
    return generate_dungeon(
        params.map_width,
        params.map_height,
        max_rooms=MAX_ROOMS,
        room_min_size=ROOM_MIN_SIZE,
        room_max_size=ROOM_MAX_SIZE,
        seed=params.seed,
        water_testing=params.water_testing,
        layout_archetype_force=params.layout_archetype_force,
        runes_per_floor=params.runes_per_floor,
    )


class _ExecutorBackend(Protocol):
    def submit(self, params: PrefetchParams) -> Future[GameMap]: ...

    def shutdown(self) -> None: ...


class _ProcessBackend:
    """Single-worker process backend for production and frozen builds."""

    def __init__(self) -> None:
        self._executor = ProcessPoolExecutor(
            max_workers=1,
            mp_context=mp.get_context("spawn"),
        )

    def submit(self, params: PrefetchParams) -> Future[GameMap]:
        return self._executor.submit(_generate_worker, params)

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)


class _ThreadBackend:
    """Single-worker in-process backend for tests."""

    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="floor_prefetch",
        )

    def submit(self, params: PrefetchParams) -> Future[GameMap]:
        return self._executor.submit(_generate_worker, params)

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)


class FloorPrefetch:
    """Owns at most one in-flight `GameMap` prefetch job."""

    def __init__(self, *, use_process: bool = True) -> None:
        self._lock = threading.Lock()
        self._backend: _ExecutorBackend = (
            _ProcessBackend() if use_process and not os.environ.get("KDS_PREFETCH_DISABLE_PROCESS") else _ThreadBackend()
        )
        self._params: PrefetchParams | None = None
        self._result: GameMap | None = None
        self._error: BaseException | None = None
        self._ready = threading.Event()
        self._future: Future[GameMap] | None = None
        self._collector: threading.Thread | None = None
        self._generation = 0

    def schedule(self, params: PrefetchParams) -> None:
        """Cancel any stale job and start prefetching `params`."""
        with self._lock:
            self._clear_locked()
            self._generation += 1
            generation = self._generation
            self._params = params
            self._ready.clear()
            debug_print(
                f"[prefetch] schedule depth={params.depth} seed={params.seed} generation={generation}",
                flush=True,
            )
            future = self._backend.submit(params)
            self._future = future
            collector = threading.Thread(
                target=self._collect_result,
                args=(generation, future),
                name="floor_prefetch_collect",
                daemon=True,
            )
            self._collector = collector
            collector.start()

    def take(self, params: PrefetchParams) -> GameMap | None:
        """Return a ready cached map when params match; otherwise None."""
        with self._lock:
            if self._params is None or not self._params.matches(params):
                return None

        self._ready.wait()

        with self._lock:
            if self._params is None or not self._params.matches(params):
                return None
            if self._error is not None:
                debug_print(f"[prefetch] miss -> worker failed: {self._error}", flush=True)
                self._clear_locked()
                return None
            if self._result is None:
                return None
            result = self._result
            self._clear_locked()
            debug_print(f"[prefetch] hit depth={params.depth}", flush=True)
            return result

    def cancel(self) -> None:
        with self._lock:
            self._clear_locked()

    def shutdown(self) -> None:
        self.cancel()
        self._backend.shutdown()

    def _collect_result(self, generation: int, future: Future[GameMap]) -> None:
        """Wait for the worker process/thread without doing generation work here."""
        try:
            game_map = future.result()
        except BaseException as exc:
            with self._lock:
                if generation != self._generation:
                    return
                self._error = exc
                debug_print(f"[prefetch] worker failed: {exc}", flush=True)
            self._ready.set()
            return

        with self._lock:
            if generation != self._generation:
                return
            self._result = game_map
            depth = self._params.depth if self._params is not None else "?"
            debug_print(f"[prefetch] ready depth={depth}", flush=True)
        self._ready.set()

    def _clear_locked(self) -> None:
        self._generation += 1
        if self._future is not None:
            self._future.cancel()
        self._future = None
        self._collector = None
        self._params = None
        self._result = None
        self._error = None
        self._ready.clear()