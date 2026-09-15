"""PR11: hunt autosave, abandon prompt, per-difficulty stats boards."""

from __future__ import annotations

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.app import AppPhase
from src.hunt_save import hunt_from_snapshot, snapshot_hunt
from src.hunt_session import handle_hunt_event
from src.hunt_stats import HuntStatsScreenState, HuntStatsStore, handle_hunt_stats_event
from src.menu import build_menu_options
from tests.save_test_helpers import app_with_isolated_save
from tests.test_hunt_pr2 import _key, _open_square, _session
from tests.ui_test_helpers import make_console


def _shift_y() -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=KeySym.Y, scancode=Scancode.UNKNOWN, mod=Modifier.SHIFT)


def _enter_hunt(app, console) -> None:
    app.handle_event(_key(KeySym.RETURN), console=console)
    app.handle_event(_key(KeySym.RETURN), console=console)


def test_new_hunt_autosaves_and_continue_resumes(tmp_path) -> None:
    app = app_with_isolated_save(tmp_path)
    console = make_console()
    _enter_hunt(app, console)
    assert app.phase is AppPhase.HUNT
    assert app.hunt is not None
    handle_hunt_event(app.hunt, _key(KeySym.PERIOD))
    x, y, aut = app.hunt.player_x, app.hunt.player_y, app.hunt.world_aut
    app.handle_event(_key(KeySym.ESCAPE), console=console)
    assert app.phase is AppPhase.MENU
    assert app.save_coordinator.has_hunt_save()
    assert "Continue Hunt" in build_menu_options(
        continue_available=app.save_coordinator.has_hunt_save(),
    )
    assert app.menu.highlighted_option == "Continue Hunt"
    app.handle_event(_key(KeySym.RETURN), console=console)
    assert app.phase is AppPhase.HUNT
    assert app.hunt is not None
    assert (app.hunt.player_x, app.hunt.player_y) == (x, y)
    assert app.hunt.world_aut == aut


def test_abandon_prompt_counts_game_and_abandoned(tmp_path) -> None:
    app = app_with_isolated_save(tmp_path)
    console = make_console()
    _enter_hunt(app, console)
    assert app.hunt is not None
    app.hunt.shots_fired = 2
    app.handle_event(_key(KeySym.ESCAPE), console=console)
    while app.menu.highlighted_option != "New Hunt":
        app.menu.move_down()
    app.handle_event(_key(KeySym.RETURN), console=console)
    assert app.new_game_confirm is not None
    app.handle_event(_shift_y(), console=console)
    assert app.phase is AppPhase.WEAPON_SELECT
    assert not app.save_coordinator.has_hunt_save()
    stats = app.hunt_stats_store.load("normal")
    assert stats.games_played == 1
    assert stats.abandoned == 1
    assert stats.weapons["rifle"].fired == 2


def test_window_close_autosaves(tmp_path) -> None:
    app = app_with_isolated_save(tmp_path)
    console = make_console()
    _enter_hunt(app, console)
    assert app.handle_event(tcod.event.Quit(), console=console) is True
    assert app.save_coordinator.has_hunt_save()
    loaded = app.save_coordinator.load_hunt()
    assert loaded is not None
    assert loaded.hunter_name == ""


def test_ctrl_q_autosaves_then_menu_on_confirm(tmp_path) -> None:
    app = app_with_isolated_save(tmp_path)
    console = make_console()
    _enter_hunt(app, console)
    ctrl_q = tcod.event.KeyDown(sym=KeySym.Q, scancode=Scancode.UNKNOWN, mod=Modifier.CTRL)
    app.handle_event(ctrl_q, console=console)
    assert app.quit_confirm is not None
    assert app.save_coordinator.has_hunt_save()
    app.handle_event(_shift_y(), console=console)
    assert app.phase is AppPhase.MENU
    assert app.save_coordinator.has_hunt_save()
    stats = app.hunt_stats_store.load("normal")
    assert stats.games_played == 0
    assert stats.abandoned == 0


def test_stats_cycle_difficulty_boards(tmp_path) -> None:
    store = HuntStatsStore(tmp_path / "hunt_stats.json")
    hard = _session(weapon_id="shotgun", weapon_name="Shotgun")
    hard.difficulty_id = "hard"
    hard.outcome = "tranquilized"
    store.record_session(hard)
    assert store.load("hard").tranquilized == 1
    assert store.load("normal").tranquilized == 0
    app = app_with_isolated_save(tmp_path)
    app.hunt_stats_store = store
    while app.menu.highlighted_option != "Stats":
        app.menu.move_down()
    app.handle_event(_key(KeySym.RETURN))
    assert app.phase is AppPhase.STATS
    app.stats_screen = HuntStatsScreenState(difficulty_id="normal")
    handle_hunt_stats_event(_key(KeySym.RIGHT), app.stats_screen)
    assert app.stats_screen.difficulty_id == "hard"
    console = make_console()
    app.render(console)
    body = ""
    for y in range(console.height):
        for x in range(console.width):
            ch = int(console.rgba[x, y]["ch"])
            body += chr(ch) if ch else " "
    assert "Hard" in body
    assert "Times raptor tranquilized: 1" in body


def test_snapshot_roundtrip_keeps_facing_and_ammo() -> None:
    session = _session(paddock=_open_square(), x=5, y=5, facing=2, weapon_id="revolver")
    session.ammo = 3
    session.difficulty_id = "nightmare"
    snap = snapshot_hunt(session)
    restored = hunt_from_snapshot(snap)
    assert restored.facing == 2
    assert restored.ammo == 3
    assert restored.difficulty_id == "nightmare"
    assert restored.player_x == 5
    assert restored.weapon_id == "revolver"


def test_v1_stats_migrate_onto_normal(tmp_path) -> None:
    path = tmp_path / "hunt_stats.json"
    path.write_text(
        '{"hunt_stats_format_version":1,"games_played":4,"tranquilized":2,'
        '"digested":1,"time_wins":1,"time_losses":0,'
        '"weapons":{"rifle":{"fired":9,"landed":3,"perfect":1,"one_shot_kos":1},'
        '"shotgun":{"fired":0,"landed":0,"perfect":0,"one_shot_kos":0},'
        '"revolver":{"fired":0,"landed":0,"perfect":0,"one_shot_kos":0}}}',
        encoding="utf-8",
    )
    store = HuntStatsStore(path)
    normal = store.load("normal")
    assert normal.games_played == 4
    assert normal.tranquilized == 2
    assert normal.abandoned == 0
    assert store.load("hard").games_played == 0
