"""PR8 (hunt-deferred): visible dart along the shot line, then resolve."""

from __future__ import annotations

from tcod.event import KeySym

from src.hunt_projectile import dart_draw_tiles, load_hunt_projectile
from src.hunt_raptor import HuntRaptor
from src.hunt_session import HuntMode, handle_hunt_event, render_hunt
from src.hunt_stance import Gait
from tests.test_hunt_pr2 import _key, _open_square, _session
from tests.test_hunt_pr5 import _aimed_shotgun
from tests.test_hunt_pr10 import _console_text
from tests.ui_test_helpers import make_console


def _fire_at_visible_raptor(session) -> None:
    handle_hunt_event(session, _key(KeySym.F))
    handle_hunt_event(session, _key(KeySym.RETURN))


def test_confirm_starts_dart_before_damage() -> None:
    session = _aimed_shotgun(raptor_y=4)
    hp = session.raptor.hp
    aut = session.world_aut
    _fire_at_visible_raptor(session)
    assert session.projectile_in_progress()
    assert session.raptor.hp == hp
    assert session.world_aut == aut
    assert session.mode is HuntMode.PLAY
    assert session.ammo == 5


def test_dart_follows_the_shot_tiles() -> None:
    session = _aimed_shotgun(raptor_y=2)
    _fire_at_visible_raptor(session)
    assert session.dart is not None
    tiles = session.dart.tiles
    assert (5, 4) in tiles
    assert tiles[-1] == (5, 2)
    assert (5, 5) not in tiles


def test_input_is_ignored_until_the_dart_lands() -> None:
    session = _aimed_shotgun(raptor_y=2)
    x = session.player_x
    _fire_at_visible_raptor(session)
    handle_hunt_event(session, _key(KeySym.KP_8))
    handle_hunt_event(session, _key(KeySym.R))
    assert session.player_x == x
    assert session.gait is Gait.WALK
    assert session.projectile_in_progress()


def test_flush_applies_the_same_deterministic_hit() -> None:
    session = _aimed_shotgun(raptor_y=4)
    _fire_at_visible_raptor(session)
    session.flush_projectile()
    assert not session.projectile_in_progress()
    assert session.raptor is not None
    assert session.raptor.hp <= 0
    assert session.mode is HuntMode.WIN_BASK


def test_advance_reaches_the_same_resolve_as_flush() -> None:
    flying = _aimed_shotgun(raptor_y=3)
    _fire_at_visible_raptor(flying)
    while flying.projectile_in_progress():
        flying.advance_projectile()
    instant = _aimed_shotgun(raptor_y=3)
    _fire_at_visible_raptor(instant)
    instant.flush_projectile()
    assert flying.raptor.hp == instant.raptor.hp
    assert flying.mode is instant.mode


def test_world_time_does_not_tick_during_the_flight() -> None:
    session = _aimed_shotgun(raptor_y=2)
    _fire_at_visible_raptor(session)
    aut = session.world_aut
    session.advance_projectile()
    assert session.world_aut == aut
    session.flush_projectile()
    assert session.world_aut > aut


def test_kdvr_timing_defaults() -> None:
    cfg = load_hunt_projectile()
    assert cfg.glyph == "*"
    assert cfg.fg == (0, 255, 255)
    assert cfg.frames_per_tile == 1
    assert cfg.frame_sleep_seconds == 0.024


def test_render_draws_the_dart_glyph() -> None:
    mmap = _open_square()
    raptor = HuntRaptor(x=5, y=2, facing=4, hp=100, max_hp=100)
    session = _session(
        paddock=mmap, x=5, y=5, facing=0, raptor=raptor,
        weapon_id="shotgun", weapon_name="Shotgun",
    )
    _fire_at_visible_raptor(session)
    console = make_console()
    render_hunt(console, session)
    body = _console_text(console)
    assert "*" in body
    assert session.dart is not None
    assert dart_draw_tiles(session.dart)


def test_app_fire_event_does_not_autosave_away_the_dart(tmp_path) -> None:
    """Regression: post-key autosave used to flush the dart on the same Enter."""
    from src.app import AppPhase
    from tests.save_test_helpers import app_with_isolated_save
    from tests.test_hunt_pr11 import _enter_hunt

    app = app_with_isolated_save(tmp_path)
    console = make_console()
    _enter_hunt(app, console)
    assert app.phase is AppPhase.HUNT
    assert app.hunt is not None
    session = app.hunt
    session.raptor = HuntRaptor(
        x=session.player_x, y=session.player_y - 1, facing=4, hp=100, max_hp=100,
    )
    session.facing = 0
    session.weapon_id = "shotgun"
    session.weapon_name = "Shotgun"
    session.ammo = 6
    session.refresh_fov()
    app.handle_event(_key(KeySym.F), console=console)
    app.handle_event(_key(KeySym.RETURN), console=console)
    assert app.hunt.projectile_in_progress()
    assert app.hunt.raptor is not None
    assert app.hunt.raptor.hp == 100


def test_blocked_shot_still_flies_then_reports_tree() -> None:
    from src.hunt_map import HuntTerrain

    mmap = _open_square()
    mmap.tiles[3][5] = HuntTerrain.TREE
    raptor = HuntRaptor(x=5, y=2, facing=4, hp=100, max_hp=100)
    session = _session(paddock=mmap, x=5, y=5, facing=0, raptor=raptor)
    hp = session.raptor.hp
    handle_hunt_event(session, _key(KeySym.F))
    session.cursor_x, session.cursor_y = 5, 2
    handle_hunt_event(session, _key(KeySym.RETURN))
    assert session.projectile_in_progress()
    session.flush_projectile()
    assert session.raptor.hp == hp
    assert "tree" in session.notice.lower() or "slams" in session.notice.lower()
