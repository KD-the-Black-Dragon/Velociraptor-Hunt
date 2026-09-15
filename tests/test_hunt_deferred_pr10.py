"""PR10 (hunt-deferred): Training Mode, dummy scripts, F2 menu."""

from __future__ import annotations

import tcod.event
from tcod.event import KeySym, Scancode

from src.app import AppPhase
from src.hunt_help import hunt_help_lines
from src.hunt_map import HuntTerrain
from src.hunt_session import HuntMode, HuntSession, handle_hunt_event
from src.hunt_stance import Gait
from src.hunt_stats import HuntStatsStore
from src.hunt_training import (
    TRAINING_MENU_KEY,
    DummyScript,
    generate_training_arena,
    training_menu_rows,
)
from src.menu import MenuAction, build_menu_options, handle_main_menu_event
from tests.save_test_helpers import app_with_isolated_save
from tests.test_hunt_pr2 import _key, _session
from tests.ui_test_helpers import make_console


def _f2() -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=TRAINING_MENU_KEY, scancode=Scancode.UNKNOWN, mod=0)


def _training_session() -> HuntSession:
    return HuntSession(
        hunter_name="",
        weapon_id="rifle",
        weapon_name="Bolt-action rifle",
        training=True,
        seed=1,
    )


def test_menu_lists_training_mode() -> None:
    assert "Training Mode" in build_menu_options()
    from src.menu import MainMenuState

    state = MainMenuState()
    while state.highlighted_option != "Training Mode":
        state.move_down()
    assert handle_main_menu_event(state, _key(KeySym.RETURN)) is MenuAction.TRAINING


def test_training_arena_is_identical_and_has_anchors() -> None:
    a, la = generate_training_arena()
    b, lb = generate_training_arena()
    assert a.tiles == b.tiles
    assert la == lb
    assert a.terrain_at(*la.open_still) is HuntTerrain.OPEN
    assert a.terrain_at(*la.grass_still) is HuntTerrain.GRASS
    assert a.terrain_at(*la.patrol[0]) is HuntTerrain.OPEN
    assert a.terrain_at(*la.patrol[-1]) is HuntTerrain.GRASS


def test_training_starts_from_menu_without_save(tmp_path) -> None:
    app = app_with_isolated_save(tmp_path)
    console = make_console()
    while app.menu.highlighted_option != "Training Mode":
        app.menu.move_down()
    app.handle_event(_key(KeySym.RETURN), console=console)
    assert app.phase is AppPhase.HUNT
    assert app.hunt is not None
    assert app.hunt.training
    assert app.hunt.weapon_id == "rifle"
    assert not app.save_coordinator.has_hunt_save()
    app.handle_event(_key(KeySym.ESCAPE), console=console)
    assert app.phase is AppPhase.MENU
    assert not app.save_coordinator.has_hunt_save()


def test_live_hunt_does_not_open_f2_menu() -> None:
    session = _session()
    handle_hunt_event(session, _f2())
    assert session.training_menu is None


def test_f2_dummy_teleports_and_stop_resume() -> None:
    session = _training_session()
    handle_hunt_event(session, _f2())
    assert session.training_menu is not None
    # skip header, first command is patrol
    handle_hunt_event(session, _key(KeySym.RETURN))
    assert session.training_menu is None
    assert session.dummy_script is DummyScript.PATROL
    assert session.raptor is not None
    assert (session.raptor.x, session.raptor.y) == session.training_layout.patrol[0]

    handle_hunt_event(session, _f2())
    # stop is 4th selectable (patrol, idle_grass, idle_open, stop)
    for _ in range(3):
        handle_hunt_event(session, _key(KeySym.DOWN))
    handle_hunt_event(session, _key(KeySym.RETURN))
    assert session.dummy_script is DummyScript.STOP
    pos = (session.raptor.x, session.raptor.y)
    handle_hunt_event(session, _key(KeySym.PERIOD))
    assert (session.raptor.x, session.raptor.y) == pos

    handle_hunt_event(session, _f2())
    for _ in range(4):
        handle_hunt_event(session, _key(KeySym.DOWN))
    handle_hunt_event(session, _key(KeySym.RETURN))
    assert session.dummy_script is DummyScript.PATROL


def test_f2_swaps_weapon() -> None:
    session = _training_session()
    handle_hunt_event(session, _f2())
    rows = training_menu_rows()
    shotgun_i = next(i for i, (cid, _) in enumerate(rows) if cid == "weapon_shotgun")
    while session.training_menu.highlight != shotgun_i:
        handle_hunt_event(session, _key(KeySym.DOWN))
    handle_hunt_event(session, _key(KeySym.RETURN))
    assert session.weapon_id == "shotgun"
    assert session.ammo > 0


def test_idle_grass_teleport() -> None:
    session = _training_session()
    session.apply_training_command("idle_grass")
    assert (session.raptor.x, session.raptor.y) == session.training_layout.grass_still
    assert session.map.terrain_at(*session.training_layout.grass_still) is HuntTerrain.GRASS


def test_seek_moves_toward_hunter() -> None:
    session = _training_session()
    session.apply_training_command("seek")
    ox, oy = session.raptor.x, session.raptor.y
    handle_hunt_event(session, _key(KeySym.PERIOD))
    dist0 = max(abs(ox - session.player_x), abs(oy - session.player_y))
    dist1 = max(
        abs(session.raptor.x - session.player_x),
        abs(session.raptor.y - session.player_y),
    )
    assert dist1 <= dist0


def test_gait_overlay() -> None:
    session = _training_session()
    session.apply_training_command("gait_run")
    assert session.dummy_gait is Gait.RUN
    assert session.raptor.gait is Gait.RUN


def test_training_swallow_not_recorded(tmp_path) -> None:
    app = app_with_isolated_save(tmp_path)
    console = make_console()
    while app.menu.highlighted_option != "Training Mode":
        app.menu.move_down()
    app.handle_event(_key(KeySym.RETURN), console=console)
    assert app.hunt is not None
    app.hunt.outcome = "digested"
    app.hunt.shots_fired = 3
    app.handle_event(_key(KeySym.ESCAPE), console=console)
    store = HuntStatsStore(app.hunt_stats_store.path)
    stats = store.load("normal")
    assert stats.games_played == 0
    assert stats.digested == 0


def test_training_help_lists_f2() -> None:
    text = " ".join(line.text for line in hunt_help_lines(training=True))
    assert "F2" in text
    live = " ".join(line.text for line in hunt_help_lines(training=False))
    assert "F2 - dummy" not in live


def test_adjacent_dummy_teleport_uses_d14() -> None:
    session = _training_session()
    session.player_x, session.player_y = session.training_layout.open_still
    session.facing = 0
    session.apply_training_command("idle_open")
    # Teleport onto hunter is bounced; standing next to hunter facing them can swallow.
    session.raptor.x = session.player_x
    session.raptor.y = session.player_y - 1
    session.raptor.facing = 4
    session._refresh_raptor_fov()
    assert session.maybe_raptor_finish()
    assert session.mode is HuntMode.SWALLOW
