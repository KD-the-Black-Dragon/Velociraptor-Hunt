"""PR3: background autosave coordinator."""

from __future__ import annotations

import threading
from typing import Any

import pytest

from src.components import Engulfed
from src.engine import GameEngine
from src.save.coordinator import SaveCoordinator
from src.systems.rest import RestSession
from src.systems.vore import VoreModalSegment

from tests.map_test_helpers import isolate_other_ais


class RecordingStore:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def save_run(self, run: dict[str, Any], **kwargs: Any) -> None:
        self.calls.append(run)


class BlockingStore:
    """Hold the first save until the test releases it."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.started = threading.Event()
        self.release = threading.Event()

    def save_run(self, run: dict[str, Any], **kwargs: Any) -> None:
        self.started.set()
        self.release.wait(timeout=5.0)
        self.calls.append(run)


@pytest.fixture
def engine() -> GameEngine:
    game = GameEngine()
    isolate_other_ais(game)
    return game


def test_coalesces_pending_snapshots_while_save_in_flight(engine: GameEngine) -> None:
    store = BlockingStore()
    # turn_interval must be ≤ the turn deltas below so mid-flight enqueues fire.
    coordinator = SaveCoordinator(
        store=store,
        turn_interval=5,
        time_interval_seconds=9999.0,
    )

    first = threading.Thread(target=coordinator.on_play_enter, args=(engine,))
    first.start()
    assert store.started.wait(timeout=5.0)

    for turn in range(10, 15):
        engine.player_turn_count = turn
        coordinator.on_player_turn_end(engine)
    store.release.set()

    coordinator.flush()
    first.join(timeout=5.0)
    coordinator.close()

    assert len(store.calls) == 2
    assert store.calls[1]["player_turn_count"] == 14


def test_autosave_skipped_when_vore_modal_blocks_idle_gate(engine: GameEngine) -> None:
    store = RecordingStore()
    coordinator = SaveCoordinator(
        store=store,
        turn_interval=1,
        time_interval_seconds=0.0,
        time_fn=lambda: 100.0,
    )
    engine.vore_modal.segment = VoreModalSegment.ATTEMPT

    engine.player_turn_count = 5
    coordinator.on_player_turn_end(engine)
    coordinator.flush()
    coordinator.close()

    assert store.calls == []


def test_autosave_skipped_during_rest(engine: GameEngine) -> None:
    store = RecordingStore()
    coordinator = SaveCoordinator(
        store=store,
        turn_interval=1,
        time_interval_seconds=0.0,
        time_fn=lambda: 100.0,
    )
    engine.rest_session = RestSession()

    engine.player_turn_count = 5
    coordinator.on_player_turn_end(engine)
    coordinator.flush()
    coordinator.close()

    assert store.calls == []


def test_turn_interval_triggers_autosave(engine: GameEngine) -> None:
    store = RecordingStore()
    now = {"value": 0.0}
    coordinator = SaveCoordinator(
        store=store,
        turn_interval=15,
        time_interval_seconds=9999.0,
        time_fn=lambda: now["value"],
    )

    coordinator.on_play_enter(engine)
    coordinator.flush()
    store.calls.clear()

    engine.player_turn_count = 14
    coordinator.on_player_turn_end(engine)
    coordinator.flush()
    assert store.calls == []

    engine.player_turn_count = 15
    coordinator.on_player_turn_end(engine)
    coordinator.flush()
    coordinator.close()

    assert len(store.calls) == 1
    assert store.calls[0]["player_turn_count"] == 15


def test_time_interval_triggers_autosave(engine: GameEngine) -> None:
    store = RecordingStore()
    now = {"value": 0.0}
    coordinator = SaveCoordinator(
        store=store,
        turn_interval=9999,
        time_interval_seconds=30.0,
        time_fn=lambda: now["value"],
    )

    coordinator.on_play_enter(engine)
    coordinator.flush()
    store.calls.clear()

    engine.player_turn_count = 3
    coordinator.on_player_turn_end(engine)
    coordinator.flush()
    assert store.calls == []

    now["value"] = 30.0
    coordinator.on_player_turn_end(engine)
    coordinator.flush()
    coordinator.close()

    assert len(store.calls) == 1


def test_engulfed_triggers_autosave_every_turn(engine: GameEngine) -> None:
    store = RecordingStore()
    coordinator = SaveCoordinator(
        store=store,
        turn_interval=9999,
        time_interval_seconds=9999.0,
    )
    assert engine.player is not None
    engine.player.tags.add(Engulfed)

    coordinator.on_play_enter(engine)
    coordinator.flush()
    store.calls.clear()

    engine.player_turn_count = 1
    coordinator.on_player_turn_end(engine)
    coordinator.flush()
    coordinator.close()

    assert len(store.calls) == 1


def test_descend_floor_triggers_autosave(engine: GameEngine) -> None:
    store = RecordingStore()
    coordinator = SaveCoordinator(
        store=store,
        turn_interval=9999,
        time_interval_seconds=9999.0,
    )

    coordinator.on_play_enter(engine)
    coordinator.flush()
    store.calls.clear()

    engine.floor_depth = 2
    coordinator.on_descend_floor(engine)
    coordinator.flush()
    coordinator.close()

    assert len(store.calls) == 1
    assert store.calls[0]["floor_depth"] == 2


def test_engine_post_turn_hook_invokes_coordinator(engine: GameEngine) -> None:
    store = RecordingStore()
    coordinator = SaveCoordinator(
        store=store,
        turn_interval=1,
        time_interval_seconds=9999.0,
    )
    engine.save_coordinator = coordinator

    coordinator.on_play_enter(engine)
    coordinator.flush()
    store.calls.clear()

    engine.player_turn_count = 0
    engine._consume_player_turn()
    coordinator.flush()
    coordinator.close()

    assert len(store.calls) == 1
    assert store.calls[0]["player_turn_count"] == 1


def test_can_issue_idle_command_matches_modal_and_rest(engine: GameEngine) -> None:
    assert engine.can_issue_idle_command()

    engine.vore_modal.segment = VoreModalSegment.ATTEMPT
    assert not engine.can_issue_idle_command()

    engine.vore_modal.reset()
    engine.rest_session = RestSession()
    assert not engine.can_issue_idle_command()