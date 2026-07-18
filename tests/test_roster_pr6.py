"""PR6: roster, hire market, deploy, talk, digest refund."""

from __future__ import annotations

import random

import tcod.event
from tcod.event import KeySym, Scancode

from src.app import AppPhase
from src.career import new_career
from src.components import Position
from src.downtime_hub import (
    HubView,
    MatchCard,
    handle_downtime_event,
)
from src.match_session import TalkUiMode, start_match
from src.roster import (
    generate_market,
    load_roster_tuning,
    remove_ally_digest,
    try_hire,
)
from tests.save_test_helpers import app_with_isolated_save
from tests.ui_test_helpers import make_console


def _key(sym: KeySym) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=0)


def test_roster_tuning_loads() -> None:
    t = load_roster_tuning()
    assert t.max_allies == 4
    assert t.max_deployed_allies == 2
    assert t.free_starter_picks == 2
    assert "scrub" in t.tiers


def test_generate_market_tiers() -> None:
    offers = generate_market(random.Random(1), count=5)
    assert len(offers) == 5
    tiers = {o.tier for o in offers}
    assert tiers  # non-empty


def test_try_hire_and_refund() -> None:
    rng = random.Random(2)
    offer = generate_market(rng, count=1)[0]
    offer.hire_cost = 40
    roster, gold, err = try_hire([], offer, gold=100, free=False)
    assert err is None
    assert len(roster) == 1
    assert gold == 60
    roster2, gold2, refund = remove_ally_digest(roster, roster[0].ally_id, gold=gold)
    assert len(roster2) == 0
    assert refund == int(round(40 * 0.7))
    assert gold2 == gold + refund


def test_new_career_forces_starter_picks(tmp_path) -> None:
    app = app_with_isolated_save(tmp_path)
    console = make_console()
    app.handle_event(_key(KeySym.RETURN), console=console)
    app.handle_event(_key(KeySym.RETURN), console=console)
    app.handle_event(_key(KeySym.RETURN), console=console)  # background
    assert app.phase is AppPhase.DOWNTIME
    assert app.career is not None
    assert app.career.starter_picks_done is False
    assert app.downtime_hub.view is HubView.STARTER_PICK


def test_starter_pick_two_completes(tmp_path) -> None:
    app = app_with_isolated_save(tmp_path)
    console = make_console()
    app.handle_event(_key(KeySym.RETURN), console=console)
    app.handle_event(_key(KeySym.RETURN), console=console)
    app.handle_event(_key(KeySym.RETURN), console=console)  # background
    assert app.downtime_hub.view is HubView.STARTER_PICK
    # Hire first free
    app.handle_event(_key(KeySym.RETURN), console=console)
    # After first pick, still starter or stub then starter
    if app.downtime_hub.view is HubView.STUB_NOTICE:
        app.handle_event(_key(KeySym.RETURN), console=console)
    # May need to re-open market
    if app.downtime_hub.view is HubView.STARTER_PICK:
        app.handle_event(_key(KeySym.RETURN), console=console)
    # Complete second
    if app.downtime_hub.view is HubView.STUB_NOTICE:
        app.handle_event(_key(KeySym.RETURN), console=console)
    if app.downtime_hub.view is HubView.STARTER_PICK:
        app.handle_event(_key(KeySym.RETURN), console=console)
    if app.downtime_hub.view is HubView.STUB_NOTICE:
        app.handle_event(_key(KeySym.RETURN), console=console)
    assert app.career is not None
    assert len(app.career.roster) >= 2
    assert app.career.starter_picks_done is True


def test_match_spawns_deployed_allies() -> None:
    career = new_career(player_name="Boss")
    career.starter_picks_done = True
    offers = generate_market(random.Random(3), count=2, free=True)
    for o in offers:
        o.deployed = True
    career.set_allies(offers[:2])
    session = start_match(
        career,
        MatchCard("r1_green_spar", "spar", "green", 0.45),
        seed=1,
    )
    assert len(session.living_allies()) == 2


def test_talk_sets_order() -> None:
    career = new_career(player_name="Boss")
    career.starter_picks_done = True
    offers = generate_market(random.Random(4), count=1, free=True)
    offers[0].deployed = True
    career.set_allies(offers[:1])
    session = start_match(
        career,
        MatchCard("r1_green_spar", "spar", "green", 0.45),
        seed=2,
    )
    assert session.living_allies()
    session.handle_event(_key(KeySym.T))
    assert session.talk_ui is TalkUiMode.PICK_ALLY
    session.handle_event(_key(KeySym.N1))
    assert session.talk_ui is TalkUiMode.PICK_ORDER
    session.handle_event(_key(KeySym.N2))  # defend
    assert session.talk_ui is TalkUiMode.CLOSED
    aid = session.ally_id_by_entity[session.living_allies()[0]]
    assert session.ally_order[aid] == "defend"


def test_red_ally_down_refunds() -> None:
    career = new_career(player_name="Boss")
    career.starter_picks_done = True
    career.gold = 100
    offers = generate_market(random.Random(5), count=1, free=False)
    offers[0].hire_cost = 50
    offers[0].deployed = True
    career.set_allies(offers[:1])
    session = start_match(
        career,
        MatchCard("r1_rats", "rats", "red", 1.0),
        seed=3,
    )
    ally = session.living_allies()[0]
    ally.components[Position] = Position(5, 5)
    session._on_ally_down(ally)
    assert len(career.roster) == 0
    assert career.gold == 100 + int(round(50 * 0.7))
