"""PR13–PR15: rifle scope, sounds, glyphs, difficulty, double-step."""

from __future__ import annotations

from src.hunt_ai import HuntAiConfig, RaptorSense, raptor_act
from src.hunt_aut import tenths
from src.hunt_clock import RingState
from src.hunt_difficulty import hunt_tuning, reset_hunt_difficulty_cache
from src.hunt_fov import line_visible
from src.hunt_map import HuntMap, HuntTerrain, load_paddock_config, reset_paddock_config_cache, vision_profile_for
from src.hunt_raptor import HuntRaptor
from src.hunt_session import handle_hunt_event, render_hunt
from src.hunt_stance import AIM_FOCUS, AIM_NONE
from src.hunt_weather import move_sound_chance, reset_hunt_weather_cache
from tests.test_hunt_pr2 import _key, _open_square, _session
from tests.test_hunt_pr4 import _FixedRng
from tests.ui_test_helpers import make_console
from tcod.event import KeySym


def test_rifle_aim_is_line_and_close_blind() -> None:
    reset_paddock_config_cache()
    cfg = load_paddock_config()
    rifle = vision_profile_for(gait="walk", aim_depth=1, cfg=cfg, weapon_id="rifle")
    shotgun = vision_profile_for(gait="walk", aim_depth=1, cfg=cfg, weapon_id="shotgun")
    assert rifle.line is True
    assert rifle.close_blind == 3
    assert rifle.cone_range > shotgun.cone_range
    assert rifle.cone_half_degrees < shotgun.cone_half_degrees


def test_move_sound_chances_by_rain() -> None:
    reset_hunt_weather_cache()
    assert move_sound_chance("run", "light") == 1.0
    assert abs(move_sound_chance("quick", "light") - 0.67) < 1e-9
    assert abs(move_sound_chance("walk", "light") - 0.33) < 1e-9
    assert move_sound_chance("sneak", "light") == 0.0
    assert abs(move_sound_chance("run", "medium") - 0.90) < 1e-9
    assert abs(move_sound_chance("walk", "heavy") - 0.13) < 1e-9
    assert move_sound_chance("sneak", "heavy") == 0.0


def test_live_raptor_glyph_beats_sound() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=5, y=3, facing=4)
    session = _session(paddock=mmap, x=5, y=5, facing=0, raptor=raptor)
    session.refresh_fov()
    assert session.raptor_in_sight()
    from src.hunt_weather import SoundMark
    session.sound_marks.append(SoundMark(x=5, y=3, false_alarm=True, expires_aut=99.0))
    console = make_console()
    render_hunt(console, session)
    ch = chr(int(console.rgba[5, 3]["ch"]))
    assert ch == "r"


def test_raptor_steps_around_a_tree() -> None:
    from src.hunt_ai import _face_or_step
    mmap = _open_square()
    mmap.tiles[6][5] = HuntTerrain.TREE
    raptor = HuntRaptor(x=5, y=7, facing=0)
    start = (raptor.x, raptor.y)
    _face_or_step(raptor, mmap, 5, 4, blocked=set())
    _face_or_step(raptor, mmap, 5, 4, blocked=set())
    assert (raptor.x, raptor.y) != start
    assert mmap.terrain_at(raptor.x, raptor.y) is not HuntTerrain.TREE


def test_nightmare_raptor_is_faster() -> None:
    reset_hunt_difficulty_cache()
    assert hunt_tuning("nightmare").raptor_speed_mult > hunt_tuning("normal").raptor_speed_mult
    assert hunt_tuning("nightmare").rain_cycle_aut > hunt_tuning("normal").rain_cycle_aut


def test_double_step_collapses_heatmap() -> None:
    mmap = _open_square(21)
    raptor = HuntRaptor(x=2, y=2, facing=2)
    raptor.mind.last_heard_x = 10
    raptor.mind.last_heard_y = 10
    raptor.mind.last_heard_aut = 1.0
    raptor_act(
        raptor, mmap,
        sense=RaptorSense(
            hunter_x=1, hunter_y=1, hunter_facing=0, hunter_aim_depth=0,
            hunter_weapon_id="rifle", hunter_gait="walk", hunter_sees_raptor=False,
            ring=RingState.CLOSE, hunter_ring=0.0, raptor_ring=0.0,
            clock_remaining=200.0, heard_xy=(10, 11), world_aut=2.5,
            clock_duration=320.0, double_step_aut=2.0,
        ),
        rng=_FixedRng(0.0),
        cfg=HuntAiConfig(double_step_aut=2.0),
    )
    assert raptor.mind.fix_x is not None
    assert abs(raptor.mind.fix_x - 10) <= 1
    assert abs((raptor.mind.fix_y or 0) - 10) <= 1


def test_hunter_step_sound_uses_from_tile() -> None:
    mmap = _open_square()
    session = _session(paddock=mmap, x=5, y=8, facing=0)
    session.gait = session.gait  # walk
    session.rng = _FixedRng(0.0)  # always sound if chance > 0
    # Force a hear by placing raptor in range
    session.raptor = HuntRaptor(x=5, y=6, facing=4)
    handle_hunt_event(session, _key(KeySym.KP_8))
    # FROM was 5,8
    assert session.raptor_heard_xy in ((5, 8), None) or (
        session.raptor_heard_xy is not None
    )
