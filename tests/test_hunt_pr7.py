"""PR7: hunt clock, ring-control score, three-state HUD, time-over."""

from __future__ import annotations

from tcod.event import KeySym

from src.hunt_aut import load_hunt_aut_costs
from src.hunt_clock import RingState, center_weight, load_hunt_clock, ring_state
from src.hunt_session import HuntAction, HuntMode, handle_hunt_event
from tests.test_hunt_pr2 import _key, _open_square, _session


def test_center_scores_more_than_rim() -> None:
    mmap = _open_square()
    mid = center_weight(mmap, mmap.center_x, mmap.center_y)
    rim = center_weight(mmap, 1, mmap.center_y)
    assert mid > rim
    assert mid == 1.0 or mid > 0.5
    assert rim < mid


def test_ring_state_three_buckets() -> None:
    assert ring_state(0.0, 0.0, 12.0) is RingState.CLOSE
    assert ring_state(12.0, 0.0, 12.0) is RingState.HUNTER_WINNING
    assert ring_state(11.9, 0.0, 12.0) is RingState.CLOSE
    assert ring_state(0.0, 12.0, 12.0) is RingState.RAPTOR_WINNING


def test_wait_accrues_ring_and_burns_clock() -> None:
    session = _session()
    start = session.clock_remaining()
    handle_hunt_event(session, _key(KeySym.PERIOD))
    assert session.clock_remaining() == start - load_hunt_aut_costs().wait
    assert session.hunter_ring > 0.0
    assert session.raptor_ring >= 0.0


def test_time_over_hunter_win_needs_definite_lead() -> None:
    session = _session()
    cfg = load_hunt_clock()
    session.hunter_ring = cfg.definitely_margin
    session.raptor_ring = 0.0
    session.scheduler.world_aut = cfg.duration_aut
    session._check_clock()
    assert session.mode is HuntMode.TIME_OVER
    assert session.time_over_win is True
    assert handle_hunt_event(session, _key(KeySym.RETURN)) is HuntAction.LEAVE


def test_time_over_close_is_loss() -> None:
    session = _session()
    cfg = load_hunt_clock()
    session.hunter_ring = 1.0
    session.raptor_ring = 0.0
    session.scheduler.world_aut = cfg.duration_aut
    session._check_clock()
    assert session.mode is HuntMode.TIME_OVER
    assert session.time_over_win is False


def test_time_over_raptor_lead_is_loss() -> None:
    session = _session()
    cfg = load_hunt_clock()
    session.hunter_ring = 0.0
    session.raptor_ring = cfg.definitely_margin
    session.scheduler.world_aut = cfg.duration_aut
    session._check_clock()
    assert session.time_over_win is False
    assert session.ring_hud() is RingState.RAPTOR_WINNING
