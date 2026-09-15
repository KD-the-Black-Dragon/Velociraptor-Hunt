"""PR4: AP, balance, actual stats, abilities, smart bump."""

from __future__ import annotations

import tcod.event
from tcod.event import KeySym, Scancode

from src.career import new_career
from src.components import Fighter
from src.downtime_hub import MatchCard
from src.match_combat import (
    CombatantState,
    actual_fighter,
    awareness_openness,
    choose_bump_profile,
    format_ap_meter,
    format_balance_meter,
    load_match_combat_config,
)
from src.match_session import AbilityUiMode, MatchPhase, start_match


def _key(sym: KeySym) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=0)


def test_match_combat_config_has_seed_abilities() -> None:
    cfg = load_match_combat_config()
    assert cfg.ap_max >= 10
    letters = {a.letter for a in cfg.abilities}
    assert "a" in letters and "b" in letters and "c" in letters


def test_balance_extremes_change_actual_stats() -> None:
    cfg = load_match_combat_config()
    f = Fighter(hp=20, max_hp=20, accuracy=10.0, evade=5.0, ac=1, min_damage=2, max_damage=4)
    base = CombatantState.from_fighter(f, cfg)
    over = CombatantState.from_fighter(f, cfg)
    over.balance = 8
    cow = CombatantState.from_fighter(f, cfg)
    cow.balance = -8
    act_base = actual_fighter(base, cfg)
    act_over = actual_fighter(over, cfg)
    act_cow = actual_fighter(cow, cfg)
    # Overextended: more damage potential, worse accuracy than moderate
    assert act_over.max_damage >= act_base.max_damage
    assert act_over.accuracy <= act_base.accuracy + 0.01
    # Cowering: worse damage
    assert act_cow.max_damage <= act_base.max_damage


def test_smart_bump_profiles() -> None:
    assert choose_bump_profile(0.1) == "jab"
    assert choose_bump_profile(0.5) == "standard"
    assert choose_bump_profile(0.9) == "all_out"
    assert awareness_openness(-5, 20, 20) < awareness_openness(5, 5, 20)


def test_ap_meters_format() -> None:
    assert "#" in format_ap_meter(10, 10)
    assert "N" in format_balance_meter(0) or "|" in format_balance_meter(0)


def test_wait_shifts_balance_defensive() -> None:
    """Keep watch and brace shift defensive; brace can go past watch floor."""
    career = new_career(player_name="T")
    session = start_match(career, MatchCard("r1_green_spar", "spar", "green", 0.45), seed=1)
    before = session.combatants[session.player].balance
    session.handle_event(_key(KeySym.PERIOD))
    after_watch = session.combatants[session.player].balance
    assert after_watch < before
    session.awaiting_player = True
    session.handle_event(_key(KeySym.D))
    assert session.combatants[session.player].balance < after_watch


def test_ability_menu_and_haymaker() -> None:
    career = new_career(player_name="T")
    session = start_match(career, MatchCard("r1_green_spar", "spar", "green", 0.45), seed=3)
    # Place enemy adjacent
    from src.components import Position

    pp = session.player.components[Position]
    enemy = session.living_enemies()[0]
    enemy.components[Position] = Position(pp.x + 1, pp.y)
    session.combatants[session.player].ap = 10
    session.handle_event(_key(KeySym.A))
    assert session.ability_ui is AbilityUiMode.PICK_LETTER
    session.handle_event(_key(KeySym.A))  # haymaker letter a
    # Either attacked or still in fight
    assert session.phase in (MatchPhase.FIGHT, MatchPhase.RECAP)
    # AP spent if attack resolved
    if session.phase is MatchPhase.FIGHT:
        assert session.combatants[session.player].ap < 10 or session.ability_ui is AbilityUiMode.CLOSED


def test_ap_regens_with_world_aut() -> None:
    career = new_career(player_name="T")
    session = start_match(career, MatchCard("r1_green_spar", "spar", "green", 0.45), seed=4)
    st = session.combatants[session.player]
    st.ap = 0
    st.last_world_aut = 0.0
    session.scheduler.world_aut = 3.0
    st.tick_ap(3.0)
    assert st.ap >= 2.5
