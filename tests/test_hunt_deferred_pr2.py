"""PR2 (hunt-deferred): right-side hunt panel."""

from __future__ import annotations

from tcod.event import KeySym

from src.hunt_clock import RingState
from src.hunt_panel import (
    fuzzy_health_label,
    hunter_stat_lines,
    map_view_size,
    raptor_readout,
)
from src.hunt_raptor import HuntRaptor
from src.hunt_stance import Gait
from src.hunt_session import HuntMode, handle_hunt_event, render_hunt
from tests.test_hunt_pr2 import _key, _open_square, _session
from tests.test_hunt_pr10 import _console_text
from tests.ui_test_helpers import make_console


def _row_text(console, y: int) -> str:
    chars: list[str] = []
    for x in range(console.width):
        ch = int(console.rgba[x, y]["ch"])
        chars.append(chr(ch) if ch else " ")
    return "".join(chars)


def _right_text(console) -> str:
    view_w, view_h = map_view_size(console.width, console.height)
    body = ""
    for y in range(view_h):
        body += _row_text(console, y)[view_w:] + "\n"
    return body


def test_hunter_stat_lines_are_lime_fields() -> None:
    lines = hunter_stat_lines(
        facing="N",
        weapon_id="shotgun",
        weapon_name="Shotgun",
        ammo=6,
        gait=Gait.WALK,
        aim_depth=0,
        fatigue=2,
    )
    assert "Facing: N" in lines
    assert "Weapon: Shotgun" in lines
    assert "Ammo: 6" in lines
    assert "Speed: walking" in lines
    assert "Aim level: 0" in lines
    assert "Fatigue: 2" in lines


def test_render_puts_clock_and_ring_on_the_right() -> None:
    session = _session(paddock=_open_square(), x=5, y=5, facing=0)
    console = make_console()
    render_hunt(console, session)
    right = _right_text(console)
    assert "Clock" in right
    assert session.ring_hud().value in right
    assert "Facing:" in right
    assert "Weapon:" in right
    assert "Ammo:" in right
    assert "Speed:" in right
    assert "Aim level:" in right
    assert "Fatigue:" in right
    footer = _row_text(console, console.height - 1)
    assert "Clock" not in footer
    assert session.ring_hud().value not in footer


def test_render_raptor_facing_in_panel_only_when_seen() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=5, y=2, facing=4)
    session = _session(paddock=mmap, x=5, y=5, facing=0, raptor=raptor)
    console = make_console()
    render_hunt(console, session)
    right = _right_text(console)
    assert "Velociraptor" in right
    assert "Distance: 3" in right
    assert "Facing: S!" in right
    assert "State: Standing" in right
    assert "Health: Perfect" in right

    hidden = HuntRaptor(x=5, y=8, facing=2)
    session_h = _session(paddock=_open_square(), x=5, y=5, facing=0, raptor=hidden)
    console_h = make_console()
    render_hunt(console_h, session_h)
    right_h = _right_text(console_h)
    assert "Velociraptor" not in right_h
    footer = _row_text(console_h, console_h.height - 1)
    assert "Velociraptor" not in footer


def test_targeting_factors_live_in_the_panel() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=5, y=2, facing=4)
    session = _session(paddock=mmap, x=5, y=5, facing=0, raptor=raptor)
    handle_hunt_event(session, _key(KeySym.F))
    assert session.mode is HuntMode.TARGETING
    console = make_console()
    render_hunt(console, session)
    right = _right_text(console)
    assert "Range:" in right
    assert "Ammo:" in right
    footer = _row_text(console, console.height - 1)
    assert "Range:" not in footer
    body = _console_text(console)
    assert "Clock" in body


def test_raptor_readout_bang_only_when_it_sees_hunter() -> None:
    mmap = _open_square()
    looking_away = HuntRaptor(x=5, y=2, facing=0)
    looking_away.refresh_fov(mmap)
    lines = raptor_readout(looking_away, 5, 5)
    assert "Facing: N" in lines
    assert "Facing: N!" not in lines
    looking_away.last_move_facing = 2
    looking_away.gait = Gait.RUN
    moved = raptor_readout(looking_away, 5, 5)
    assert "State: Running E" in moved
    assert "Health: Perfect" in moved


def test_fuzzy_health_cores_and_hysteresis() -> None:
    assert fuzzy_health_label(100) == "Perfect"
    assert fuzzy_health_label(90) == "Steady"
    assert fuzzy_health_label(70) == "Rattled"
    assert fuzzy_health_label(40) == "Wavering"
    assert fuzzy_health_label(10) == "Weary"
    assert fuzzy_health_label(77, previous="Steady") == "Steady"
    assert fuzzy_health_label(77, previous="Rattled") == "Rattled"
    assert fuzzy_health_label(77) == "Rattled"
    assert fuzzy_health_label(55, previous="Rattled") == "Rattled"
    assert fuzzy_health_label(55, previous="Wavering") == "Wavering"
