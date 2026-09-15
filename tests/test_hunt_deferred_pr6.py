"""PR6 (hunt-deferred): run fatigue, not run-mode cone."""

from __future__ import annotations

from tcod.event import KeySym

from src.hunt_combat import compute_damage, loose_factors, weapon_combat
from src.hunt_fatigue import load_hunt_fatigue, reset_hunt_fatigue_cache
from src.hunt_session import handle_hunt_event
from src.hunt_stance import AIM_NONE, Gait
from tests.test_hunt_pr2 import _key, _open_square, _session


def test_run_toggle_does_not_add_fatigue() -> None:
    session = _session(paddock=_open_square(), x=5, y=5, facing=0)
    walk = set(session.visible)
    handle_hunt_event(session, _key(KeySym.R))
    assert session.gait is Gait.RUN
    assert session.run_fatigue == 0
    assert session.visible == walk


def test_run_steps_stack_fatigue_and_shorten_vision() -> None:
    reset_hunt_fatigue_cache()
    session = _session(paddock=_open_square(), x=5, y=8, facing=0)
    handle_hunt_event(session, _key(KeySym.R))
    before = len(session.visible)
    handle_hunt_event(session, _key(KeySym.KP_8))
    assert session.run_fatigue == 1
    assert len(session.visible) < before
    handle_hunt_event(session, _key(KeySym.KP_8))
    assert session.run_fatigue == 2


def test_fatigue_caps() -> None:
    reset_hunt_fatigue_cache()
    cfg = load_hunt_fatigue()
    session = _session(paddock=_open_square(), x=5, y=9, facing=0)
    handle_hunt_event(session, _key(KeySym.R))
    for _ in range(cfg.max_stack + 3):
        handle_hunt_event(session, _key(KeySym.KP_8))
    assert session.run_fatigue == cfg.max_stack


def test_three_waits_recover_one_fatigue() -> None:
    session = _session(paddock=_open_square(), x=5, y=5, facing=0)
    session.run_fatigue = 2
    handle_hunt_event(session, _key(KeySym.PERIOD))
    handle_hunt_event(session, _key(KeySym.PERIOD))
    assert session.run_fatigue == 2
    handle_hunt_event(session, _key(KeySym.PERIOD))
    assert session.run_fatigue == 1


def test_walk_wait_sneak_mix_recovers() -> None:
    session = _session(paddock=_open_square(), x=5, y=8, facing=0)
    session.run_fatigue = 2
    handle_hunt_event(session, _key(KeySym.KP_8))
    handle_hunt_event(session, _key(KeySym.PERIOD))
    assert session.run_fatigue == 2
    handle_hunt_event(session, _key(KeySym.S))
    handle_hunt_event(session, _key(KeySym.KP_8))
    assert session.run_fatigue == 1


def test_three_walk_steps_recover_one_fatigue() -> None:
    session = _session(paddock=_open_square(), x=5, y=8, facing=0)
    session.run_fatigue = 2
    handle_hunt_event(session, _key(KeySym.KP_8))
    handle_hunt_event(session, _key(KeySym.KP_8))
    assert session.run_fatigue == 2
    handle_hunt_event(session, _key(KeySym.KP_8))
    assert session.run_fatigue == 1


def test_run_walk_run_resets_recovery() -> None:
    session = _session(paddock=_open_square(), x=5, y=8, facing=0)
    handle_hunt_event(session, _key(KeySym.R))
    handle_hunt_event(session, _key(KeySym.KP_8))
    assert session.run_fatigue == 1
    handle_hunt_event(session, _key(KeySym.W))
    handle_hunt_event(session, _key(KeySym.KP_8))
    handle_hunt_event(session, _key(KeySym.KP_8))
    assert session.run_fatigue == 1
    handle_hunt_event(session, _key(KeySym.R))
    handle_hunt_event(session, _key(KeySym.KP_8))
    assert session.run_fatigue == 2


def test_quick_holds_fatigue() -> None:
    session = _session(paddock=_open_square(), x=5, y=8, facing=0)
    handle_hunt_event(session, _key(KeySym.R))
    handle_hunt_event(session, _key(KeySym.KP_8))
    handle_hunt_event(session, _key(KeySym.KP_8))
    assert session.run_fatigue == 2
    handle_hunt_event(session, _key(KeySym.Q))
    handle_hunt_event(session, _key(KeySym.KP_8))
    handle_hunt_event(session, _key(KeySym.KP_8))
    handle_hunt_event(session, _key(KeySym.KP_8))
    assert session.run_fatigue == 2
    assert session.gait is Gait.QUICK


def test_shot_factors_and_damage_use_fatigue_not_run_mode() -> None:
    reset_hunt_fatigue_cache()
    rifle = weapon_combat("rifle")
    fresh = compute_damage(
        rifle, range_chebyshev=8, aim_depth=2, hunter_running=False, hunter_fatigue=0,
    )
    tired = compute_damage(
        rifle, range_chebyshev=8, aim_depth=2, hunter_running=False, hunter_fatigue=2,
    )
    assert tired < fresh
    factors = loose_factors(
        rifle,
        range_chebyshev=8,
        aim_depth=AIM_NONE,
        hunter_running=True,
        raptor_visible=True,
        ammo=5,
        hunter_fatigue=2,
    )
    assert "out of breath" in factors
    assert "you are running" not in factors
    mode_only = loose_factors(
        rifle,
        range_chebyshev=8,
        aim_depth=AIM_NONE,
        hunter_running=True,
        raptor_visible=True,
        ammo=5,
        hunter_fatigue=0,
    )
    assert "out of breath" not in mode_only
