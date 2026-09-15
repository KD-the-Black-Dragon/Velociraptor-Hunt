"""PR4 (hunt-deferred): last-known raptor mark and one sound glyph."""

from __future__ import annotations

from src.hunt_clock import load_hunt_clock, reset_hunt_clock_cache
from src.hunt_raptor import HuntRaptor
from src.hunt_session import render_hunt
from src.hunt_weather import SoundMark
from tests.test_hunt_pr2 import _open_square, _session
from tests.test_hunt_pr10 import _console_text
from tests.ui_test_helpers import make_console


def _glyph_at(console, x: int, y: int) -> str:
    ch = int(console.rgba[x, y]["ch"])
    return chr(ch) if ch else " "


def test_clock_duration_matches_data() -> None:
    reset_hunt_clock_cache()
    assert load_hunt_clock().duration_aut == 320.0


def test_never_seen_has_no_last_known() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=5, y=8, facing=4)
    session = _session(paddock=mmap, x=5, y=5, facing=0, raptor=raptor)
    assert not session.raptor_in_sight()
    assert session.last_known_x is None
    assert session.last_known_y is None


def test_last_known_set_when_seen_and_kept_when_lost() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=5, y=2, facing=4)
    session = _session(paddock=mmap, x=5, y=5, facing=0, raptor=raptor)
    assert session.raptor_in_sight()
    assert session.last_known_x == 5
    assert session.last_known_y == 2
    session.facing = 4
    session.refresh_fov()
    assert not session.raptor_in_sight()
    assert session.last_known_x == 5
    assert session.last_known_y == 2


def test_last_known_clears_when_empty_tile_is_in_fov() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=5, y=2, facing=4)
    session = _session(paddock=mmap, x=5, y=5, facing=0, raptor=raptor)
    assert session.last_known_x == 5
    assert session.last_known_y == 2
    raptor.x, raptor.y = 1, 5
    session.refresh_fov()
    assert not session.raptor_in_sight()
    assert (5, 2) in session.visible
    assert session.last_known_x is None
    assert session.last_known_y is None


def test_last_known_clears_live_mark_when_seen_again() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=5, y=2, facing=4)
    session = _session(paddock=mmap, x=5, y=5, facing=0, raptor=raptor)
    session.facing = 4
    session.refresh_fov()
    raptor.x, raptor.y = 6, 2
    session.facing = 0
    session.refresh_fov()
    assert session.raptor_in_sight()
    assert session.last_known_x == 6
    assert session.last_known_y == 2
    console = make_console()
    render_hunt(console, session)
    body = _console_text(console)
    assert "r" in body


def test_render_last_known_is_dim_r_not_live_when_lost() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=5, y=2, facing=4)
    session = _session(paddock=mmap, x=5, y=5, facing=0, raptor=raptor)
    session.facing = 4
    session.refresh_fov()
    console = make_console()
    render_hunt(console, session)
    assert not session.raptor_in_sight()
    body = _console_text(console)
    assert "r" in body


def test_sound_marks_are_one_question_glyph() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=5, y=8, facing=4)
    session = _session(paddock=mmap, x=5, y=5, facing=0, raptor=raptor)
    session.sound_marks = [
        SoundMark(x=6, y=5, false_alarm=False, expires_aut=10.0),
        SoundMark(x=4, y=5, false_alarm=True, expires_aut=10.0),
    ]
    console = make_console()
    render_hunt(console, session)
    body = _console_text(console)
    assert "?" in body


def test_heard_raptor_does_not_write_footer_prose() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=5, y=3, facing=4)
    session = _session(paddock=mmap, x=5, y=5, facing=0, raptor=raptor)

    class HearRng:
        def random(self) -> float:
            return 0.0

        def choice(self, seq):
            return seq[0]

    session.rng = HearRng()
    session.notice = ""
    session._emit_move_sound(5, 3, source="raptor")
    assert session.notice == ""
    assert session.sound_marks
    session._maybe_false_alarm()
    assert "Rain in the canopy" not in session.notice
    assert "Wind from" not in session.notice
    assert not session.notice.startswith("Movement")
