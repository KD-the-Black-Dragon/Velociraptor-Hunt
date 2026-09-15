"""PR10: persistent stats, hunt help, leftover HUD."""

from __future__ import annotations

from tcod.event import KeySym, Modifier, Scancode

import tcod.event

from src.app import AppPhase
from src.hunt_help import hunt_help_lines
from src.hunt_session import HuntAction, HuntMode, handle_hunt_event, render_hunt
from src.hunt_stats import HuntStatsStore, hunt_stats_lines
from src.input_handlers import is_help_open_key
from tests.save_test_helpers import app_with_isolated_save
from tests.test_hunt_pr2 import _key, _open_square, _session
from tests.test_hunt_pr5 import _aimed_shotgun
from tests.ui_test_helpers import make_console


def _console_text(console) -> str:
    body = ""
    for y in range(console.height):
        for x in range(console.width):
            ch = int(console.rgba[x, y]["ch"])
            body += chr(ch) if ch else " "
        body += "\n"
    return body


def test_stats_screen_lists_locked_fields(tmp_path) -> None:
    app = app_with_isolated_save(tmp_path)
    while app.menu.highlighted_option != "Stats":
        app.menu.move_down()
    app.handle_event(_key(KeySym.RETURN))
    assert app.phase is AppPhase.STATS
    console = make_console()
    app.render(console)
    body = _console_text(console)
    assert "Total games played" in body
    assert "Games abandoned" in body
    assert "Times raptor tranquilized" in body
    assert "Times digested" in body
    assert "Wins by time over" in body
    assert "Losses by time over" in body
    assert "Rifle" in body
    assert "Shotgun" in body
    assert "Revolver" in body
    assert "One-shot KOs" in body
    app.handle_event(_key(KeySym.ESCAPE))
    assert app.phase is AppPhase.MENU


def test_store_records_outcome_once(tmp_path) -> None:
    store = HuntStatsStore(tmp_path / "hunt_stats.json")
    session = _session(weapon_id="rifle", weapon_name="Bolt-action rifle")
    session.shots_fired = 2
    session.shots_landed = 1
    session.shots_perfect = 1
    session.shots_one_shot = 1
    session.outcome = "tranquilized"
    store.record_session(session)
    store.record_session(session)
    stats = store.load()
    assert stats.games_played == 1
    assert stats.tranquilized == 1
    assert stats.weapons["rifle"].fired == 2
    assert stats.weapons["rifle"].landed == 1
    assert stats.weapons["rifle"].perfect == 1
    assert stats.weapons["rifle"].one_shot_kos == 1


def test_esc_mid_hunt_counts_shots_not_games(tmp_path) -> None:
    app = app_with_isolated_save(tmp_path)
    console = make_console()
    app.handle_event(_key(KeySym.RETURN), console=console)
    app.handle_event(_key(KeySym.RETURN), console=console)
    app.handle_event(_key(KeySym.RETURN), console=console)
    assert app.phase is AppPhase.HUNT
    assert app.hunt is not None
    app.hunt.shots_fired = 3
    app.hunt.shots_landed = 1
    app.handle_event(_key(KeySym.ESCAPE), console=console)
    assert app.phase is AppPhase.MENU
    stats = app.hunt_stats_store.load()
    assert stats.games_played == 0
    assert stats.weapons["rifle"].fired == 0
    assert app.save_coordinator.has_hunt_save()


def test_time_loss_and_digest_are_separate_buckets(tmp_path) -> None:
    store = HuntStatsStore(tmp_path / "hunt_stats.json")
    a = _session(weapon_id="shotgun", weapon_name="Shotgun")
    a.outcome = "time_loss"
    store.record_session(a)
    b = _session(weapon_id="revolver", weapon_name="Revolver")
    b.outcome = "digested"
    store.record_session(b)
    c = _session(weapon_id="shotgun", weapon_name="Shotgun")
    c.outcome = "time_win"
    store.record_session(c)
    stats = store.load()
    assert stats.games_played == 3
    assert stats.time_losses == 1
    assert stats.time_wins == 1
    assert stats.digested == 1
    text = "\n".join(line.text for line in hunt_stats_lines(stats))
    assert "Losses by time over: 1" in text
    assert "Times digested: 1" in text


def test_help_opens_on_f1_and_esc_closes_without_leaving() -> None:
    session = _session(paddock=_open_square())
    f1 = tcod.event.KeyDown(sym=KeySym.F1, scancode=Scancode.UNKNOWN, mod=Modifier.NONE)
    assert is_help_open_key(f1)
    assert handle_hunt_event(session, f1) is HuntAction.NONE
    assert session.help_open
    assert handle_hunt_event(session, _key(KeySym.ESCAPE)) is HuntAction.NONE
    assert not session.help_open
    assert handle_hunt_event(session, _key(KeySym.ESCAPE)) is HuntAction.LEAVE


def test_help_lists_tank_and_aim_keys() -> None:
    text = " ".join(line.text for line in hunt_help_lines())
    assert "Ctrl+4" in text
    assert "deep aim" in text
    assert "F1 or ?" in text


def test_help_works_in_belly() -> None:
    session = _session()
    session.mode = HuntMode.BELLY
    f1 = tcod.event.KeyDown(sym=KeySym.F1, scancode=Scancode.UNKNOWN, mod=Modifier.NONE)
    assert handle_hunt_event(session, f1) is HuntAction.NONE
    assert session.help_open
    assert session.mode is HuntMode.BELLY


def test_tranquilizing_shot_fills_tally() -> None:
    session = _aimed_shotgun(raptor_y=4)
    handle_hunt_event(session, _key(KeySym.F))
    handle_hunt_event(session, _key(KeySym.RETURN))
    session.flush_projectile()
    assert session.shots_fired == 1
    assert session.shots_landed == 1
    assert session.shots_perfect == 1
    assert session.shots_one_shot == 1
    assert session.outcome == "tranquilized"


def test_footer_has_clock_not_key_legend() -> None:
    session = _session(paddock=_open_square(), x=5, y=5, facing=0)
    console = make_console()
    render_hunt(console, session)
    body = _console_text(console)
    assert "Clock" in body
    assert "8 fwd" not in body
    assert "Shift+4/6" not in body
