"""PR4: one raptor, tank FOV, fair eyes-on stub AI, in-sight facing HUD."""

from __future__ import annotations

from tcod.event import KeySym

from src.hunt_aut import load_hunt_aut_costs
from src.hunt_facing import facing_name, facing_toward
from src.hunt_raptor import HuntRaptor, stub_raptor_act
from src.hunt_session import handle_hunt_event, render_hunt
from tests.test_hunt_pr2 import _key, _open_square, _session
from tests.ui_test_helpers import make_console


class _FixedRng:
    def __init__(self, value: float, choice_index: int = 0) -> None:
        self.value = value
        self.choice_index = choice_index

    def random(self) -> float:
        return self.value

    def choice(self, seq):
        return seq[self.choice_index % len(seq)]

    def randrange(self, n: int) -> int:
        return 0 if n else 0


def test_facing_toward_cardinals() -> None:
    assert facing_name(facing_toward(5, 5, 5, 1)) == "N"
    assert facing_name(facing_toward(5, 5, 8, 5)) == "E"
    assert facing_name(facing_toward(5, 5, 5, 8)) == "S"
    assert facing_name(facing_toward(5, 5, 2, 5)) == "W"


def test_one_raptor_spawns_off_the_hunter() -> None:
    session = _session()
    assert session.raptor is not None
    assert (session.raptor.x, session.raptor.y) != (session.player_x, session.player_y)
    assert session.map.walkable(session.raptor.x, session.raptor.y)


def test_raptor_in_sight_when_ahead_not_when_behind() -> None:
    mmap = _open_square()
    ahead = HuntRaptor(x=5, y=2, facing=4)
    session = _session(paddock=mmap, x=5, y=5, facing=0, raptor=ahead)
    assert session.raptor_in_sight()
    behind = HuntRaptor(x=5, y=8, facing=0)
    session_b = _session(paddock=_open_square(), x=5, y=5, facing=0, raptor=behind)
    assert not session_b.raptor_in_sight()


def test_hud_shows_raptor_facing_only_when_seen() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=5, y=2, facing=4)
    session = _session(paddock=mmap, x=5, y=5, facing=0, raptor=raptor)
    console = make_console()
    render_hunt(console, session)
    body = ""
    for y in range(console.height):
        for x in range(console.width):
            ch = int(console.rgba[x, y]["ch"])
            body += chr(ch) if ch else " "
    assert "Velociraptor" in body
    assert "Facing: S!" in body

    hidden = HuntRaptor(x=5, y=8, facing=2)
    session_h = _session(paddock=_open_square(), x=5, y=5, facing=0, raptor=hidden)
    console_h = make_console()
    render_hunt(console_h, session_h)
    hidden_body = ""
    for y in range(console_h.height):
        for x in range(console_h.width):
            ch = int(console_h.rgba[x, y]["ch"])
            hidden_body += chr(ch) if ch else " "
    assert "Velociraptor" not in hidden_body


def test_stub_ai_does_not_turn_toward_unseen_hunter() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=8, y=8, facing=2)
    raptor.refresh_fov(mmap)
    assert not raptor.sees(5, 5)
    stub_raptor_act(
        raptor, mmap, hunter_x=5, hunter_y=5, rng=_FixedRng(0.4, choice_index=0),
    )
    assert raptor.facing == 1
    assert raptor.facing != facing_toward(8, 8, 5, 5)


def test_stub_ai_can_face_seen_hunter() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=5, y=8, facing=0)
    raptor.refresh_fov(mmap)
    assert raptor.sees(5, 5)
    stub_raptor_act(
        raptor, mmap, hunter_x=5, hunter_y=5, rng=_FixedRng(0.1),
    )
    assert raptor.facing == facing_toward(5, 8, 5, 5)


def test_hunter_wait_gives_raptor_a_turn() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=1, y=1, facing=6)
    session = _session(paddock=mmap, x=5, y=5, facing=0, raptor=raptor)
    fx, fy, ff = session.raptor.x, session.raptor.y, session.raptor.facing
    handle_hunt_event(session, _key(KeySym.PERIOD))
    assert session.raptor is not None
    assert (session.raptor.x, session.raptor.y, session.raptor.facing) != (fx, fy, ff)
    assert session.world_aut == load_hunt_aut_costs().wait
