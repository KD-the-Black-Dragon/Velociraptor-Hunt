"""PR3: gait (R/S) and aim stances (A / A / D)."""

from __future__ import annotations

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.hunt_aut import load_hunt_aut_costs, tenths
from src.hunt_input import TankCommand, parse_tank_command
from src.hunt_map import load_paddock_config, vision_profile_for
from src.hunt_session import handle_hunt_event
from src.hunt_stance import AIM_DEEP, AIM_FOCUS, AIM_NONE, Gait
from tests.test_hunt_pr2 import _open_square, _session


def _key(sym: KeySym) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=Modifier.NONE)


def _ctrl(sym: KeySym) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=Modifier.LCTRL)


def test_gait_and_aim_keys() -> None:
    assert parse_tank_command(_key(KeySym.Q)) is TankCommand.SET_QUICK
    assert parse_tank_command(_key(KeySym.W)) is TankCommand.SET_WALK
    assert parse_tank_command(_key(KeySym.R)) is TankCommand.SET_RUN
    assert parse_tank_command(_key(KeySym.S)) is TankCommand.SET_SNEAK
    assert parse_tank_command(_key(KeySym.A)) is TankCommand.AIM
    assert parse_tank_command(_key(KeySym.D)) is TankCommand.STAND_DOWN


def test_gait_keys_are_free_and_set_directly() -> None:
    session = _session()
    assert session.gait is Gait.WALK
    handle_hunt_event(session, _key(KeySym.R))
    assert session.gait is Gait.RUN
    assert session.world_aut == 0.0
    handle_hunt_event(session, _key(KeySym.Q))
    assert session.gait is Gait.QUICK
    handle_hunt_event(session, _key(KeySym.S))
    assert session.gait is Gait.SNEAK
    handle_hunt_event(session, _key(KeySym.W))
    assert session.gait is Gait.WALK
    handle_hunt_event(session, _key(KeySym.R))
    assert session.gait is Gait.RUN
    assert load_hunt_aut_costs().gait == 0.0


def _confirm_aim(session) -> None:
    handle_hunt_event(session, _key(KeySym.A))
    handle_hunt_event(session, _key(KeySym.RETURN))


def test_aim_two_depths_then_stand_down() -> None:
    session = _session()
    handle_hunt_event(session, _key(KeySym.A))
    assert session.aim_depth == AIM_NONE
    handle_hunt_event(session, _key(KeySym.RETURN))
    assert session.aim_depth == AIM_FOCUS
    costs = load_hunt_aut_costs()
    assert session.world_aut == costs.aim
    handle_hunt_event(session, _key(KeySym.A))
    assert session.aim_depth == AIM_DEEP
    handle_hunt_event(session, _key(KeySym.A))
    assert session.aim_depth == AIM_DEEP
    assert session.world_aut == tenths(costs.aim * 2)
    handle_hunt_event(session, _key(KeySym.D))
    assert session.aim_depth == AIM_NONE
    handle_hunt_event(session, _key(KeySym.D))
    assert session.aim_depth == AIM_NONE


def test_running_clears_aim_walk_and_sneak_do_not() -> None:
    session = _session()
    _confirm_aim(session)
    handle_hunt_event(session, _key(KeySym.S))
    assert session.aim_depth == AIM_FOCUS
    assert session.gait is Gait.SNEAK
    handle_hunt_event(session, _key(KeySym.W))
    assert session.gait is Gait.WALK
    assert session.aim_depth == AIM_FOCUS
    handle_hunt_event(session, _key(KeySym.R))
    assert session.gait is Gait.RUN
    assert session.aim_depth == AIM_FOCUS
    handle_hunt_event(session, _key(KeySym.KP_8))
    assert session.aim_depth == AIM_NONE


def test_run_sidestep_and_back_slow_to_walk() -> None:
    session = _session()
    handle_hunt_event(session, _key(KeySym.R))
    assert session.gait is Gait.RUN
    x = session.player_x
    handle_hunt_event(session, _ctrl(KeySym.KP_4))
    assert session.gait is Gait.WALK
    assert session.player_x == x - 1
    handle_hunt_event(session, _key(KeySym.R))
    y = session.player_y
    handle_hunt_event(session, _key(KeySym.KP_2))
    assert session.gait is Gait.WALK
    assert session.player_y == y + 1


def test_sneak_allows_back_and_sidestep() -> None:
    session = _session()
    handle_hunt_event(session, _key(KeySym.S))
    y = session.player_y
    handle_hunt_event(session, _key(KeySym.KP_2))
    assert session.gait is Gait.SNEAK
    assert session.player_y == y + 1


def test_run_shortens_cone_aim_lengthens_and_narrows() -> None:
    cfg = load_paddock_config()
    walk = vision_profile_for(gait="walk", aim_depth=0, cfg=cfg)
    run = vision_profile_for(gait="run", aim_depth=0, cfg=cfg)
    aim = vision_profile_for(gait="walk", aim_depth=1, cfg=cfg)
    deep = vision_profile_for(gait="walk", aim_depth=2, cfg=cfg)
    assert run.cone_range == walk.cone_range
    assert aim.cone_range > walk.cone_range
    assert aim.cone_half_degrees < walk.cone_half_degrees
    assert deep.cone_range > aim.cone_range
    assert deep.cone_half_degrees < aim.cone_half_degrees


def test_run_mode_toggle_does_not_shorten_fov() -> None:
    session = _session()
    walk_seen = set(session.visible)
    handle_hunt_event(session, _key(KeySym.R))
    assert session.gait is Gait.RUN
    assert session.run_fatigue == 0
    assert session.visible == walk_seen
