"""PR9 (hunt-deferred): loss spectacle, belly ring on the raptor, end modals."""

from __future__ import annotations

from tcod.event import KeySym

from src.ui.menu_dialog import DIALOG_BG
from src.hunt_loss import load_hunt_loss
from src.hunt_modals import ENGULFED_OVERLAY_FG
from src.hunt_panel import map_view_size
from src.hunt_raptor import HuntRaptor
from src.hunt_session import HuntAction, HuntMode, handle_hunt_event, render_hunt
from src.messages import hunt_digested_over, hunt_game_over
from tests.test_hunt_pr2 import _key, _open_square, _session
from tests.test_hunt_pr10 import _console_text
from tests.ui_test_helpers import make_console


class _SeqRng:
    def __init__(self, rands: list[float], pick: int = 0) -> None:
        self.rands = list(rands)
        self.pick = pick

    def random(self) -> float:
        return self.rands.pop(0)

    def choice(self, seq):
        return seq[self.pick % len(seq)]


def _belly_session(*, x: int = 2, y: int = 2):
    mmap = _open_square()
    raptor = HuntRaptor(x=x, y=y, facing=4, hp=100, max_hp=100)
    session = _session(paddock=mmap, x=5, y=5, facing=0, raptor=raptor)
    session.begin_swallow()
    handle_hunt_event(session, _key(KeySym.RETURN))
    return session


def test_enter_belly_snaps_hunter_onto_the_raptor() -> None:
    session = _belly_session(x=2, y=2)
    assert session.mode is HuntMode.BELLY
    assert session.raptor is not None
    assert (session.player_x, session.player_y) == (session.raptor.x, session.raptor.y)


def test_belly_ring_sits_on_the_raptor_not_console_center() -> None:
    session = _belly_session(x=2, y=2)
    console = make_console()
    render_hunt(console, session)
    view_w, view_h = map_view_size(console.width, console.height)
    cam_x = max(0, min(2 - view_w // 2, max(0, session.map.width - view_w)))
    cam_y = max(0, min(2 - view_h // 2, max(0, session.map.height - view_h)))
    sx, sy = 2 - cam_x, 2 - cam_y
    assert chr(int(console.rgba[sx, sy]["ch"])) == "@"
    assert chr(int(console.rgba[sx + 1, sy]["ch"])) == "#"
    fg = console.rgba[sx + 1, sy]["fg"]
    assert tuple(int(c) for c in fg[:3]) == ENGULFED_OVERLAY_FG
    cx, cy = console.width // 2, console.height // 2
    assert (sx, sy) != (cx, cy)
    assert chr(int(console.rgba[cx, cy]["ch"]) or 32) != "@"


def test_belly_walk_is_fifty_fifty_and_carries_the_hunter() -> None:
    session = _belly_session(x=5, y=5)
    session.rng = _SeqRng([0.9])  # type: ignore[assignment]
    start = (session.raptor.x, session.raptor.y)
    handle_hunt_event(session, _key(KeySym.PERIOD))
    assert (session.raptor.x, session.raptor.y) == start
    assert (session.player_x, session.player_y) == start

    session.belly_turns = 0
    session.rng = _SeqRng([0.1], pick=0)  # type: ignore[assignment]
    handle_hunt_event(session, _key(KeySym.PERIOD))
    assert (session.raptor.x, session.raptor.y) != start
    assert (session.player_x, session.player_y) == (session.raptor.x, session.raptor.y)
    console = make_console()
    render_hunt(console, session)
    view_w, view_h = map_view_size(console.width, console.height)
    cam_x = max(0, min(5 - view_w // 2, max(0, session.map.width - view_w)))
    cam_y = max(0, min(5 - view_h // 2, max(0, session.map.height - view_h)))
    sx = session.raptor.x - cam_x
    sy = session.raptor.y - cam_y
    assert chr(int(console.rgba[sx, sy]["ch"])) == "@"
    assert (sx, sy) != (start[0] - cam_x, start[1] - cam_y)


def test_digest_and_game_over_keep_the_map_hidden() -> None:
    session = _belly_session()
    session.belly_turns = 99
    handle_hunt_event(session, _key(KeySym.PERIOD))
    console = make_console()
    render_hunt(console, session)
    body = _console_text(console)
    assert "'" not in body
    handle_hunt_event(session, _key(KeySym.RETURN))
    render_hunt(console, session)
    body = _console_text(console)
    assert "'" not in body
    assert hunt_game_over() in body


def test_modal_box_is_opaque_and_text_is_centered() -> None:
    session = _session()
    session.mode = HuntMode.TIME_OVER
    session.win_lines = ("Time over — you hold the ring.",)
    console = make_console()
    render_hunt(console, session)
    title = hunt_game_over()
    found = False
    for y in range(console.height):
        for x in range(console.width):
            if chr(int(console.rgba[x, y]["ch"]) or 32) != title[0]:
                continue
            chunk = "".join(
                chr(int(console.rgba[x + i, y]["ch"]) or 32)
                for i in range(min(len(title), console.width - x))
            )
            if chunk.startswith(title):
                found = True
                bg = tuple(int(c) for c in console.rgba[x, y]["bg"][:3])
                assert bg == DIALOG_BG
                # Title is centered in the box, not stuck on the left border.
                assert x > 4
                break
        if found:
            break
    assert found


def test_belly_darkens_glyphs_not_the_void() -> None:
    session = _belly_session(x=5, y=5)
    console = make_console()
    render_hunt(console, session)
    view_w, view_h = map_view_size(console.width, console.height)
    cam_x = max(0, min(5 - view_w // 2, max(0, session.map.width - view_w)))
    cam_y = max(0, min(5 - view_h // 2, max(0, session.map.height - view_h)))
    hx, hy = 5 - cam_x + 1, 5 - cam_y
    void = tuple(int(c) for c in console.rgba[0, 0]["bg"][:3])
    assert void == (0, 0, 0)
    early = tuple(int(c) for c in console.rgba[hx, hy]["fg"][:3])
    session.belly_turns = load_hunt_loss().belly_turns - 1
    render_hunt(console, session)
    late_void = tuple(int(c) for c in console.rgba[0, 0]["bg"][:3])
    late = tuple(int(c) for c in console.rgba[hx, hy]["fg"][:3])
    assert late_void == (0, 0, 0)
    assert sum(late) < sum(early)


def test_digest_then_centered_game_over() -> None:
    session = _belly_session()
    session.belly_turns = 99
    handle_hunt_event(session, _key(KeySym.PERIOD))
    assert session.mode is HuntMode.DIGEST
    handle_hunt_event(session, _key(KeySym.RETURN))
    assert session.mode is HuntMode.GAME_OVER
    console = make_console()
    render_hunt(console, session)
    body = _console_text(console)
    assert hunt_game_over() in body
    assert hunt_digested_over() in body
    assert handle_hunt_event(session, _key(KeySym.A)) is HuntAction.NONE
    assert handle_hunt_event(session, _key(KeySym.RETURN)) is HuntAction.LEAVE


def test_time_over_and_tranq_results_are_centered_modals() -> None:
    session = _session()
    session.mode = HuntMode.TIME_OVER
    session.win_lines = ("Time over — you hold the ring.",)
    console = make_console()
    render_hunt(console, session)
    body = _console_text(console)
    assert hunt_game_over() in body
    assert "Time over" in body
    session.mode = HuntMode.WIN_RESULTS
    session.win_lines = ("You win!", "Weapon: Shotgun")
    render_hunt(console, session)
    body = _console_text(console)
    assert hunt_game_over() in body
    assert "You win!" in body
