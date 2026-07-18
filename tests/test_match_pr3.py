"""PR3: match vertical slice + AUT scheduler."""

from __future__ import annotations

import tcod.event
from tcod.event import KeySym, Scancode

from src.app import AppPhase
from src.aut import AutScheduler, load_aut_costs
from src.career import new_career
from src.components import Fighter, Position
from src.downtime_hub import MatchCard, stub_cards_for_round
from src.match_map import SAND_PIT_HEIGHT, SAND_PIT_WIDTH, build_sand_pit_map
from src.match_session import MatchEndKind, MatchPhase, start_match
from tests.save_test_helpers import app_with_isolated_save
from tests.ui_test_helpers import make_console


def _key(sym: KeySym) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=0)


def test_aut_player_wins_ties() -> None:
    sched = AutScheduler()
    player = object()
    enemy = object()
    sched.register(player, ready_at=0.0)
    sched.register(enemy, ready_at=0.0)
    nxt = sched.next_actor([player, enemy], player=player)
    assert nxt is player
    sched.commit_action(player, 1.0)
    nxt2 = sched.next_actor([player, enemy], player=player)
    assert nxt2 is enemy
    assert sched.world_aut == 0.0


def test_aut_costs_load() -> None:
    costs = load_aut_costs()
    assert costs.step < costs.standard_attack
    assert costs.jab_attack <= costs.standard_attack


def test_sand_pit_size() -> None:
    m = build_sand_pit_map()
    assert m.width == SAND_PIT_WIDTH
    assert m.height == SAND_PIT_HEIGHT


def test_start_match_spawns_enemies() -> None:
    career = new_career(player_name="Gladiator")
    card = MatchCard("r1_rats", "3 dire rats", "red", 1.0)
    session = start_match(career, card, seed=1)
    assert session.phase is MatchPhase.FIGHT
    assert len(session.living_enemies()) == 3
    assert session.player.components[Fighter].hp > 0
    assert session.awaiting_player


def test_player_step_advances_aut() -> None:
    career = new_career(player_name="Gladiator")
    card = MatchCard("r1_green_spar", "spar", "green", 0.45)
    session = start_match(career, card, seed=2)
    before = session.scheduler.world_aut
    pos = session.player.components[Position]
    # Move toward open sand (east)
    session.handle_event(_key(KeySym.RIGHT))
    # After player acts, NPCs may run; player should eventually await again
    assert session.awaiting_player or session.phase is MatchPhase.RECAP
    assert session.scheduler.ready_at(session.player) > before or session.phase is MatchPhase.RECAP
    # Player moved or fought
    new_pos = session.player.components[Position]
    assert (new_pos.x, new_pos.y) != (pos.x, pos.y) or session.phase is MatchPhase.RECAP


def test_defeat_all_enemies_wins() -> None:
    career = new_career(player_name="Gladiator")
    card = MatchCard("r1_green_spar", "spar", "green", 0.45)
    session = start_match(career, card, seed=99)
    # Brute force: set enemy HP to 0 and finish
    for e in session.living_enemies():
        e.components[Fighter].hp = 0
        session.scheduler.unregister(e)
    session._finish_win()
    assert session.phase is MatchPhase.RECAP
    assert session.end_kind is MatchEndKind.WIN
    assert session.career.gold > 100
    assert session.career.round_index == 2


def test_hub_select_match_enters_match_phase(tmp_path) -> None:
    app = app_with_isolated_save(tmp_path)
    console = make_console()
    app.handle_event(_key(KeySym.RETURN), console=console)
    app.handle_event(_key(KeySym.RETURN), console=console)
    app.handle_event(_key(KeySym.RETURN), console=console)  # background
    assert app.phase is AppPhase.DOWNTIME
    assert app.career is not None
    # Skip starter gate for this navigation test
    app.career.starter_picks_done = True
    app.downtime_hub.reset_to_root()

    # Navigate to Select next match
    from src.downtime_hub import HUB_ROOT_OPTIONS

    select_idx = next(i for i, o in enumerate(HUB_ROOT_OPTIONS) if o.startswith("Select"))
    app.downtime_hub.highlight = select_idx
    app.handle_event(_key(KeySym.RETURN), console=console)
    assert app.downtime_hub.view.name == "MATCH_SELECT"
    app.handle_event(_key(KeySym.RETURN), console=console)
    assert app.phase is AppPhase.MATCH
    assert app.match_session is not None
    assert len(app.match_session.living_enemies()) >= 1
