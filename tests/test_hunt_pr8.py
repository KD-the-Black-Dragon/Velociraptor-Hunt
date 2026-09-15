"""PR8: melee swallow, belly, digest; end screens dismiss on Enter/Esc only."""

from __future__ import annotations

from tcod.event import KeySym

from src.hunt_loss import attack_angle, load_hunt_loss
from src.hunt_raptor import HuntRaptor
from src.hunt_session import HuntAction, HuntMode, handle_hunt_event
from tests.test_hunt_pr2 import _key, _open_square, _session


def test_attack_angle_front_side_behind() -> None:
    assert attack_angle(5, 5, 0, 5, 2) == "front"
    assert attack_angle(5, 5, 0, 5, 8) == "behind"
    assert attack_angle(5, 5, 0, 8, 5) == "side"


def test_end_screens_need_enter_or_esc() -> None:
    session = _session()
    session.mode = HuntMode.WIN_RESULTS
    assert handle_hunt_event(session, _key(KeySym.A)) is HuntAction.NONE
    assert handle_hunt_event(session, _key(KeySym.PERIOD)) is HuntAction.NONE
    assert handle_hunt_event(session, _key(KeySym.RETURN)) is HuntAction.LEAVE
    session.mode = HuntMode.TIME_OVER
    assert handle_hunt_event(session, _key(KeySym.B)) is HuntAction.NONE
    assert handle_hunt_event(session, _key(KeySym.ESCAPE)) is HuntAction.LEAVE


def test_adjacent_raptor_swallows_on_its_turn() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=5, y=4, facing=4, hp=100, max_hp=100)
    session = _session(paddock=mmap, x=5, y=5, facing=0, raptor=raptor)
    handle_hunt_event(session, _key(KeySym.PERIOD))
    assert session.mode is HuntMode.SWALLOW
    assert session.swallow_angle in {"front", "side", "behind"}
    assert session.win_lines


def test_swallow_to_belly_to_digest() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=5, y=4, facing=4, hp=100, max_hp=100)
    session = _session(paddock=mmap, x=5, y=5, facing=0, raptor=raptor)
    session.begin_swallow()
    assert session.mode is HuntMode.SWALLOW
    handle_hunt_event(session, _key(KeySym.RETURN))
    assert session.mode is HuntMode.BELLY
    n = load_hunt_loss().belly_turns
    for _ in range(n):
        handle_hunt_event(session, _key(KeySym.PERIOD))
    assert session.mode is HuntMode.DIGEST
    assert handle_hunt_event(session, _key(KeySym.A)) is HuntAction.NONE
    assert handle_hunt_event(session, _key(KeySym.ESCAPE)) is HuntAction.NONE
    assert session.mode is HuntMode.GAME_OVER
    assert handle_hunt_event(session, _key(KeySym.ESCAPE)) is HuntAction.LEAVE


def test_belly_ignores_leave_and_fire() -> None:
    session = _session()
    session.mode = HuntMode.BELLY
    assert handle_hunt_event(session, _key(KeySym.ESCAPE)) is HuntAction.NONE
    assert session.mode is HuntMode.BELLY
    assert handle_hunt_event(session, _key(KeySym.F)) is HuntAction.NONE
    assert session.mode is HuntMode.BELLY
