"""PR3 (hunt-deferred): raptor win on adjacent + raptor FOV."""

from __future__ import annotations

from tcod.event import KeySym

from src.hunt_raptor import HuntRaptor
from src.hunt_session import HuntMode, handle_hunt_event
from tests.test_hunt_pr2 import _key, _open_square, _session


def test_adjacent_and_raptor_sees_hunter_is_instant_swallow() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=5, y=4, facing=4, hp=100, max_hp=100)
    session = _session(paddock=mmap, x=5, y=5, facing=0, raptor=raptor)
    assert session.maybe_raptor_finish() is True
    assert session.mode is HuntMode.SWALLOW
    assert session.swallow_angle in {"front", "side", "behind"}


def test_adjacent_behind_raptor_is_safe() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=5, y=4, facing=0, hp=100, max_hp=100)
    session = _session(paddock=mmap, x=5, y=5, facing=0, raptor=raptor)
    assert session.maybe_raptor_finish() is False
    assert session.mode is HuntMode.PLAY


def test_hunter_step_into_raptor_eyes_finishes_before_raptor_turn() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=5, y=3, facing=4, hp=100, max_hp=100)
    session = _session(paddock=mmap, x=5, y=5, facing=0, raptor=raptor)
    handle_hunt_event(session, _key(KeySym.KP_8))
    assert session.player_y == 4
    assert session.mode is HuntMode.SWALLOW


def test_hunter_step_behind_raptor_does_not_finish_on_the_step() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=5, y=3, facing=0, hp=100, max_hp=100)
    session = _session(paddock=mmap, x=5, y=5, facing=0, raptor=raptor)
    assert session.try_step(0, -1) is True
    assert session.player_y == 4
    assert session.maybe_raptor_finish() is False
    assert session.mode is HuntMode.PLAY


def test_raptor_turning_onto_adjacent_hunter_finishes() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=5, y=4, facing=0, hp=100, max_hp=100)
    session = _session(paddock=mmap, x=5, y=5, facing=0, raptor=raptor)
    assert session.maybe_raptor_finish() is False
    raptor.facing = 4
    assert session.maybe_raptor_finish() is True
    assert session.mode is HuntMode.SWALLOW


def test_wait_while_seen_and_adjacent_still_swallows() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=5, y=4, facing=4, hp=100, max_hp=100)
    session = _session(paddock=mmap, x=5, y=5, facing=0, raptor=raptor)
    handle_hunt_event(session, _key(KeySym.PERIOD))
    assert session.mode is HuntMode.SWALLOW
