"""PR9: raptor mind — profile, scramble, circle, hold center, heave."""

from __future__ import annotations

from tcod.event import KeySym

from src.hunt_ai import HuntAiConfig, RaptorSense, certain_time_loss, raptor_act
from src.hunt_clock import RingState
from src.hunt_combat import chebyshev
from src.hunt_facing import facing_toward
from src.hunt_raptor import HuntRaptor, stub_raptor_act
from src.hunt_session import handle_hunt_event
from src.hunt_stance import AIM_FOCUS
from tests.test_hunt_pr2 import _key, _open_square, _session
from tests.test_hunt_pr4 import _FixedRng


def _cfg(**kwargs) -> HuntAiConfig:
    return HuntAiConfig(**kwargs)


def _sense(**kwargs) -> RaptorSense:
    base = dict(
        hunter_x=5,
        hunter_y=5,
        hunter_facing=0,
        hunter_aim_depth=0,
        hunter_weapon_id="shotgun",
        hunter_gait="walk",
        hunter_sees_raptor=False,
        ring=RingState.CLOSE,
        hunter_ring=0.0,
        raptor_ring=0.0,
        clock_remaining=80.0,
        definitely_margin=12.0,
    )
    base.update(kwargs)
    return RaptorSense(**base)


def test_certain_time_loss_needs_an_unreachable_gap() -> None:
    assert not certain_time_loss(12.0, 0.0, 80.0, 12.0)
    assert certain_time_loss(30.0, 0.0, 4.0, 12.0)
    assert not certain_time_loss(20.0, 0.0, 10.0, 12.0)
    assert certain_time_loss(20.0, 0.0, 8.0, 12.0)


def test_unseen_hunter_is_not_a_tile_cheat() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=8, y=8, facing=2)
    raptor.refresh_fov(mmap)
    assert not raptor.sees(2, 2)
    raptor_act(
        raptor, mmap,
        sense=_sense(hunter_x=2, hunter_y=2),
        rng=_FixedRng(0.4),
        cfg=_cfg(),
    )
    assert raptor.mind.last_seen_x is None
    assert raptor.mind.intent in ("scan", "stalk", "wander", "patrol", "hide", "contest", "relay")
    assert raptor.facing != facing_toward(8, 8, 2, 2)


def test_stub_wrapper_still_faces_a_seen_hunter() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=5, y=8, facing=0)
    raptor.refresh_fov(mmap)
    assert raptor.sees(5, 5)
    stub_raptor_act(raptor, mmap, hunter_x=5, hunter_y=5, rng=_FixedRng(0.1))
    assert raptor.facing == facing_toward(5, 8, 5, 5)


def test_staredown_circles_instead_of_charging() -> None:
    mmap = _open_square(21)
    raptor = HuntRaptor(x=10, y=2, facing=4)
    hunter = (10, 10)
    start = chebyshev(raptor.x, raptor.y, *hunter)
    assert start > 4
    for _ in range(8):
        raptor_act(
            raptor, mmap,
            sense=_sense(
                hunter_x=hunter[0],
                hunter_y=hunter[1],
                hunter_facing=0,
                hunter_sees_raptor=True,
                hunter_weapon_id="shotgun",
                clock_remaining=200.0,
                clock_duration=320.0,
            ),
            rng=_FixedRng(0.0),
            cfg=_cfg(danger_close=4),
        )
        dist = chebyshev(raptor.x, raptor.y, *hunter)
        assert dist >= 2
        assert dist >= start - 1
    assert raptor.mind.intent in (
        "circle", "shy", "stalk", "observe", "scan", "cover", "hide", "break",
    )


def test_scramble_when_it_sees_aim() -> None:
    mmap = _open_square(21)
    raptor = HuntRaptor(x=10, y=2, facing=4)
    here = chebyshev(10, 2, 10, 10)
    raptor_act(
        raptor, mmap,
        sense=_sense(
            hunter_x=10,
            hunter_y=10,
            hunter_aim_depth=AIM_FOCUS,
            hunter_sees_raptor=True,
            hunter_weapon_id="rifle",
            clock_remaining=200.0,
            clock_duration=320.0,
        ),
        rng=_FixedRng(0.0),
        cfg=_cfg(danger_close=4),
    )
    assert raptor.mind.intent in ("cover", "break")
    assert chebyshev(raptor.x, raptor.y, 10, 10) >= here


def test_hold_center_when_raptor_is_definitely_winning() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=1, y=5, facing=2)
    raptor_act(
        raptor, mmap,
        sense=_sense(
            hunter_x=8,
            hunter_y=5,
            hunter_facing=6,
            ring=RingState.RAPTOR_WINNING,
            hunter_ring=0.0,
            raptor_ring=20.0,
            clock_remaining=40.0,
        ),
        rng=_FixedRng(0.9),
        cfg=_cfg(),
    )
    assert raptor.mind.intent in (
        "grass", "stalk", "scan", "hold_center", "observe", "hide", "patrol", "contest",
    )


def test_heave_when_the_clock_is_a_certain_loss() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=1, y=5, facing=2)
    raptor.mind.last_seen_x = 8
    raptor.mind.last_seen_y = 5
    raptor_act(
        raptor, mmap,
        sense=_sense(
            hunter_x=8,
            hunter_y=5,
            hunter_facing=6,
            hunter_aim_depth=AIM_FOCUS,
            hunter_weapon_id="shotgun",
            hunter_ring=40.0,
            raptor_ring=0.0,
            clock_remaining=4.0,
            ring=RingState.HUNTER_WINNING,
        ),
        rng=_FixedRng(0.0),
        cfg=_cfg(),
    )
    assert raptor.mind.intent == "heave"
    assert raptor.x > 1 or raptor.facing == facing_toward(1, 5, 8, 5)


def test_long_stare_is_counted_then_flanked() -> None:
    mmap = _open_square(21)
    raptor = HuntRaptor(x=10, y=18, facing=0)
    raptor.mind.stare_streak = 3
    raptor.mind.observations = 3
    raptor.mind.last_obs_facing = 0
    raptor_act(
        raptor, mmap,
        sense=_sense(
            hunter_x=10,
            hunter_y=10,
            hunter_facing=0,
            hunter_sees_raptor=False,
            clock_remaining=100.0,
            clock_duration=320.0,
            world_aut=220.0,
        ),
        rng=_FixedRng(0.0),
        cfg=_cfg(stare_streak=4, danger_close=4, observe_clock_frac=0.1),
    )
    assert raptor.mind.stare_streak >= 4
    assert raptor.mind.intent in ("flank", "sneak", "sprint_in", "observe", "rush")


def test_edge_camp_profile_holds_center() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=1, y=5, facing=2)
    raptor.mind.observations = 8
    raptor.mind.edge_hits = 8
    raptor_act(
        raptor, mmap,
        sense=_sense(
            hunter_x=8,
            hunter_y=8,
            hunter_facing=4,
            ring=RingState.CLOSE,
        ),
        rng=_FixedRng(0.9),
        cfg=_cfg(habit_observations=8, habit_ratio=0.6, edge_weight=0.9),
    )
    assert raptor.mind.intent in (
        "grass", "stalk", "scan", "hold_center", "observe", "hide", "patrol", "contest",
    )


def test_wait_still_gives_the_raptor_a_mind_turn() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=1, y=1, facing=6)
    session = _session(paddock=mmap, x=5, y=5, facing=0, raptor=raptor)
    handle_hunt_event(session, _key(KeySym.PERIOD))
    assert session.raptor is not None
    assert session.raptor.mind.intent != ""
    from src.hunt_aut import load_hunt_aut_costs
    assert session.world_aut == load_hunt_aut_costs().wait
