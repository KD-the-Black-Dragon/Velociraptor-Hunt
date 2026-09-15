"""PR6: rain cycle, mud prints, movement sounds, audio fade stub."""

from __future__ import annotations

from tcod.event import KeySym

from src.hunt_map import HuntTerrain
from src.hunt_session import handle_hunt_event
from src.hunt_weather import fade_audio, load_hunt_weather, rain_index_at, rain_level_at, reset_hunt_weather_cache
from src.hunt_raptor import HuntRaptor
from tests.test_hunt_pr2 import _key, _open_square, _session


def test_rain_ping_pongs_with_aut() -> None:
    reset_hunt_weather_cache()
    cycle = load_hunt_weather().cycle_aut
    assert rain_level_at(0.0).level_id == "light"
    assert rain_index_at(0.0) == 0
    assert rain_index_at(cycle) == 1
    assert rain_index_at(cycle * 2) == 2
    assert rain_index_at(cycle * 3) == 1
    assert rain_level_at(cycle * 2).level_id == "heavy"


def test_heavy_rain_shortens_hunter_cone() -> None:
    reset_hunt_weather_cache()
    session = _session()
    light = len(session.visible)
    session.scheduler.world_aut = load_hunt_weather().cycle_aut * 2
    session.refresh_fov()
    assert rain_level_at(session.world_aut).hunter_vision_penalty > 0
    assert len(session.visible) <= light


def test_step_leaves_mud_print() -> None:
    mmap = _open_square()
    mmap.tiles[4][5] = HuntTerrain.MUD
    session = _session(paddock=mmap, x=5, y=5, facing=0)
    handle_hunt_event(session, _key(KeySym.KP_8))
    assert any(p.x == session.player_x and p.y == session.player_y for p in session.prints)
    assert any(p.owner == "hunter" for p in session.prints)


def test_heavy_rain_shows_prints_outside_fov() -> None:
    reset_hunt_weather_cache()
    cycle = load_hunt_weather().cycle_aut
    assert rain_level_at(cycle * 2).prints_outside_fov is True
    assert rain_level_at(0.0).prints_outside_fov is False


def test_raptor_move_can_be_heard() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=5, y=3, facing=4, hp=100, max_hp=100)
    session = _session(paddock=mmap, x=5, y=5, facing=0, raptor=raptor)

    class HearRng:
        def random(self) -> float:
            return 0.0

        def choice(self, seq):
            return seq[0]

    session.rng = HearRng()
    session._emit_move_sound(5, 3, source="raptor")
    assert "Movement" not in session.notice
    assert any(not m.false_alarm for m in session.sound_marks)


def test_audio_stub_fades_toward_target() -> None:
    faded = fade_audio(0.25, 1.0, 0.3)
    assert 0.25 < faded < 1.0
    session = _session()
    start = session.rain_audio
    session.scheduler.world_aut = 20.0
    session._tick_weather()
    assert session.rain_audio != start or start == rain_level_at(20.0).audio
