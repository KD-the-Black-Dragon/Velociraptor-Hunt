"""match-hud-ux: ally bump no-op, HUD band geometry, reaction modal lines."""

from __future__ import annotations

import random

import tcod.event
from tcod.event import KeySym, Scancode

from src.career import new_career
from src.components import Position
from src.downtime_hub import MatchCard
from src.match_hud_layout import match_hud_bands
from src.match_naming import entity_log_name
from src.match_session import (
    match_log_lines,
    match_reaction_modal_lines,
    match_status_lines,
    start_match,
)
from src import messages as msg
from src.roster import generate_market


def _key(sym: KeySym) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=0)


def _career_with_ally(seed: int = 1):
    career = new_career(player_name="Boss")
    career.starter_picks_done = True
    offers = generate_market(random.Random(seed), count=1, free=True)
    offers[0].deployed = True
    career.set_allies(offers[:1])
    return career


def test_ally_standing_there_message() -> None:
    assert msg.ally_standing_there("Brakus") == "Brakus is standing there."


def test_ally_bump_is_noop_no_aut() -> None:
    career = _career_with_ally(11)
    session = start_match(
        career,
        MatchCard("r1_green_spar", "spar", "green", 0.45),
        seed=11,
    )
    ally = session.living_allies()[0]
    pp = session.player.components[Position]
    ally.components[Position] = Position(pp.x + 1, pp.y)
    aut_before = session.scheduler.world_aut
    ready_before = session.scheduler._ready_at.get(session.player)
    name = entity_log_name(ally, sentence_start=True)

    session.handle_event(_key(KeySym.RIGHT))

    assert session.scheduler.world_aut == aut_before
    assert session.scheduler._ready_at.get(session.player) == ready_before
    assert session.awaiting_player is True
    texts = [e.text for e in session.message_log.entries()]
    assert any(name in t and "standing there" in t for t in texts)
    # Ally still alive / not damaged by bump
    assert ally in session.living_allies()


def test_enemy_bump_still_spends_aut() -> None:
    career = new_career(player_name="Solo")
    career.starter_picks_done = True
    session = start_match(
        career,
        MatchCard("r1_green_spar", "spar", "green", 0.45),
        seed=12,
    )
    enemy = session.living_enemies()[0]
    pp = session.player.components[Position]
    enemy.components[Position] = Position(pp.x + 1, pp.y)
    ready_before = session.scheduler._ready_at[session.player]

    session.handle_event(_key(KeySym.RIGHT))

    # Attack commits AUT (player ready time advances) or fight ends
    if session.phase.name != "RECAP":
        assert session.scheduler._ready_at[session.player] > ready_before or (
            not session.awaiting_player
        )


def test_match_hud_bands_status_right_of_map() -> None:
    bands = match_hud_bands(
        map_w=20,
        map_h=20,
        root_w=80,
        root_h=44,
        reaction_active=False,
    )
    assert bands.status.x == 20
    assert bands.status.y == 0
    assert bands.status.w == 60
    assert bands.status.h == 20
    assert bands.log.y == 20
    assert bands.log.x == 0
    assert bands.log.w == 80
    assert bands.reaction is None


def test_match_hud_bands_reaction_low_right() -> None:
    bands = match_hud_bands(
        map_w=20,
        map_h=20,
        root_w=80,
        root_h=44,
        reaction_active=True,
    )
    assert bands.reaction is not None
    assert bands.reaction.x + bands.reaction.w == 80
    assert bands.reaction.y == bands.log.y
    assert bands.log.w + bands.reaction.w == 80
    assert bands.log.x == 0
    # Reaction does not cover the map
    assert bands.reaction.y >= 20
    # Status still right of map, above log
    assert bands.status.x == 20
    assert bands.status.h == bands.log.y


def test_status_and_log_split_no_incoming_in_log() -> None:
    career = new_career(player_name="T")
    session = start_match(
        career,
        MatchCard("r1_green_spar", "spar", "green", 0.45),
        seed=7,
    )
    status = match_status_lines(session)
    log = match_log_lines(session)
    status_text = " ".join(e.text for e in status)
    log_text = " ".join(e.text for e in log)
    assert "HP " in status_text
    assert "AUT " in status_text
    assert "Bal " in status_text or "AP " in status_text
    assert "INCOMING" not in status_text
    assert "INCOMING" not in log_text
    assert match_reaction_modal_lines(session) is None


def test_reaction_modal_lines_when_pending() -> None:
    career = new_career(player_name="T")
    session = start_match(
        career,
        MatchCard("r1_green_spar", "spar", "green", 0.45),
        seed=7,
    )
    enemy = session.living_enemies()[0]
    pp = session.player.components[Position]
    enemy.components[Position] = Position(pp.x + 1, pp.y)
    session.scheduler._ready_at[enemy] = session.scheduler.world_aut
    session.scheduler._ready_at[session.player] = session.scheduler.world_aut + 10
    session.awaiting_player = False
    session.process_npc_until_player()
    assert session.pending_reaction is not None
    modal = match_reaction_modal_lines(session)
    assert modal is not None
    joined = " ".join(e.text for e in modal)
    assert "INCOMING" in joined
    assert "Dodge" in joined or "dodge" in joined.lower()
    # Status still has meters; log does not carry the modal body
    status_text = " ".join(e.text for e in match_status_lines(session))
    assert "HP " in status_text
    assert "INCOMING" not in status_text
    log_text = " ".join(e.text for e in match_log_lines(session))
    assert "INCOMING" not in log_text
