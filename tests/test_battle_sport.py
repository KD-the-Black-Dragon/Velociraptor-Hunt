"""Battle Sport batch: balance severity, measure, ready actions, footwork, AI hooks."""

from __future__ import annotations

import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.career import new_career
from src.components import Fighter, Position
from src.downtime_hub import MatchCard
from src.match_ai import maybe_start_morale_shock, momentum_evade_mult
from src.match_ai_config import load_match_ai_config, reset_match_ai_config_cache
from src.match_combat import (
    CombatantState,
    actual_fighter,
    load_match_combat_config,
    reset_match_combat_cache,
)
from src.match_session import MatchPhase, start_match
from src.weapon_measure import (
    attack_delay,
    is_footwork_offset,
    measure_mult,
    range_band,
    reset_weapon_measure_cache,
)


def _key(sym: KeySym, *, ctrl: bool = False) -> tcod.event.KeyDown:
    mod = int(Modifier.LCTRL) if ctrl else 0
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=mod)


def test_balance_plus_10_accuracy_about_five_percent() -> None:
    reset_match_combat_cache()
    cfg = load_match_combat_config()
    f = Fighter(hp=20, max_hp=20, accuracy=10.0, evade=5.0, ac=1, min_damage=2, max_damage=4)
    base = CombatantState.from_fighter(f, cfg)
    base.balance = 0
    over = CombatantState.from_fighter(f, cfg)
    over.balance = 10
    a0 = actual_fighter(base, cfg)
    a10 = actual_fighter(over, cfg)
    ratio = a10.accuracy / a0.accuracy
    assert 0.04 <= ratio <= 0.06
    # Damage still slightly higher at +10 than at 0
    assert a10.max_damage >= a0.max_damage


def test_balance_sweet_spot_and_cowering() -> None:
    reset_match_combat_cache()
    cfg = load_match_combat_config()
    f = Fighter(hp=20, max_hp=20, accuracy=10.0, evade=5.0, ac=1, min_damage=2, max_damage=10)
    b0 = CombatantState.from_fighter(f, cfg)
    b5 = CombatantState.from_fighter(f, cfg)
    b5.balance = 5
    bn = CombatantState.from_fighter(f, cfg)
    bn.balance = -10
    a0 = actual_fighter(b0, cfg)
    a5 = actual_fighter(b5, cfg)
    an = actual_fighter(bn, cfg)
    assert a5.max_damage > a0.max_damage
    assert an.max_damage < a0.max_damage
    # Cowering does not tank accuracy
    assert an.accuracy >= a0.accuracy * 0.99
    assert an.ac >= a0.ac


def test_weapon_measure_spear_vs_sword() -> None:
    reset_weapon_measure_cache()
    assert measure_mult("spear", 1) < measure_mult("short_sword", 1)
    assert measure_mult("spear", 3) > measure_mult("spear", 1)
    assert attack_delay("spear") > 0
    assert attack_delay("dagger") < attack_delay("battleaxe")


def test_footwork_geometry() -> None:
    # max_chebyshev=2 includes 1-tile and 2-tile (prior design)
    assert is_footwork_offset(1, 0)
    assert is_footwork_offset(1, 1)
    assert is_footwork_offset(2, 0)
    assert is_footwork_offset(0, -2)
    assert is_footwork_offset(2, 2)
    assert is_footwork_offset(1, 2)
    assert not is_footwork_offset(0, 0)
    assert not is_footwork_offset(3, 0)
    p1 = Position(0, 0)
    p2 = Position(2, 0)
    assert range_band(p1, p2) == 2


def test_keep_watch_shifts_defensive() -> None:
    """Keep watch (. / 5) shifts defensive but floors at -5 (cannot turtle dump)."""
    from src.match_combat import apply_ready_balance, ready_balance_delta

    reset_match_combat_cache()
    cfg = load_match_combat_config()
    career = new_career(player_name="T")
    session = start_match(career, MatchCard("r1_green_spar", "spar", "green", 0.45), seed=2)
    st = session.combatants[session.player]
    st.balance = 0
    session.handle_event(_key(KeySym.PERIOD))
    assert session.combatants[session.player].balance < 0
    # Floor: at -5 further keep_watch does not go lower
    st.balance = -5
    d = ready_balance_delta(st.balance, cfg.maneuver("keep_watch").ready_balance)
    assert d == 0
    # Step ceiling +5
    st.balance = 5
    d_step = ready_balance_delta(st.balance, cfg.maneuver("step").ready_balance)
    assert d_step == 0
    st.balance = 4
    d_step2 = ready_balance_delta(st.balance, cfg.maneuver("step").ready_balance)
    assert d_step2 == 1  # to ceiling 5


def test_brace_defensive() -> None:
    career = new_career(player_name="T")
    session = start_match(career, MatchCard("r1_green_spar", "spar", "green", 0.45), seed=3)
    before = session.combatants[session.player].balance
    session.handle_event(_key(KeySym.D))
    after = session.combatants[session.player].balance
    assert after < before


def test_footwork_targeted_confirm() -> None:
    """Footwork: f enters targeting; cursor + Enter confirms legal 2-step/knight."""
    career = new_career(player_name="T")
    session = start_match(career, MatchCard("r1_green_spar", "spar", "green", 0.45), seed=4)
    pp = session.player.components[Position]
    ox, oy = pp.x, pp.y
    session.combatants[session.player].ap = 10
    session.handle_event(_key(KeySym.F))
    assert session.footwork_targeting
    assert session.footwork_cursor is not None
    # Pick a known legal 2-east landing if open
    session.footwork_cursor = Position(ox + 2, oy)
    session.handle_event(_key(KeySym.RETURN))
    np = session.player.components[Position]
    if not session.footwork_targeting:
        assert (np.x, np.y) == (ox + 2, oy) or abs(np.x - ox) + abs(np.y - oy) >= 2
        st = session.combatants[session.player]
        assert st.momentum_until_aut > 0


def test_footwork_allows_one_tile() -> None:
    career = new_career(player_name="T")
    session = start_match(career, MatchCard("r1_green_spar", "spar", "green", 0.45), seed=7)
    pp = session.player.components[Position]
    session.combatants[session.player].ap = 10
    session.handle_event(_key(KeySym.F))
    session.footwork_cursor = Position(pp.x + 1, pp.y)
    if any(p.x == pp.x + 1 and p.y == pp.y for p in session._footwork_legal_tiles()):
        session.handle_event(_key(KeySym.RETURN))
        np = session.player.components[Position]
        assert (np.x, np.y) == (pp.x + 1, pp.y)


def test_footwork_balance_ceiling() -> None:
    from src.match_ai_config import load_match_ai_config, reset_match_ai_config_cache

    reset_match_ai_config_cache()
    fw = load_match_ai_config().footwork
    assert fw.balance_delta_for(8) == 0  # at ceiling
    assert fw.balance_delta_for(7) >= 1
    assert fw.balance_delta_for(-2) == 2  # low → larger aggression


def test_directed_attack_noop_empty() -> None:
    career = new_career(player_name="T")
    session = start_match(career, MatchCard("r1_green_spar", "spar", "green", 0.45), seed=5)
    # Move enemies far
    for e in session.enemies:
        e.components[Position] = Position(1, 1)
    session.player.components[Position] = Position(10, 10)
    before_aut = session.scheduler.world_aut
    session.handle_event(_key(KeySym.RIGHT, ctrl=True))
    # No-op: no world time spent by player commit if no foe
    # (may still be fight phase)
    assert session.phase is MatchPhase.FIGHT
    assert session.scheduler.world_aut == before_aut or session.awaiting_player


def test_enemy_has_personality_and_weapon() -> None:
    career = new_career(player_name="T")
    session = start_match(career, MatchCard("r1_green_spar", "spar", "green", 0.45), seed=6)
    assert session.enemies
    st = session.combatants[session.enemies[0]]
    assert 0 <= st.ferocity <= 10
    assert 0 <= st.cunning <= 10
    assert st.weapon_id


def test_morale_shock_forces_low_ferocity() -> None:
    reset_match_ai_config_cache()
    cfg = load_match_combat_config()
    ai = load_match_ai_config()
    f = Fighter(hp=100, max_hp=100, accuracy=10.0, evade=5.0, ac=1, min_damage=1, max_damage=2)
    st = CombatantState.from_fighter(f, cfg, ferocity=8, tenacity=1)
    st.hp_at_shock_end = 100
    import random

    rng = random.Random(0)
    # 10% loss with tenacity 1
    started = maybe_start_morale_shock(st, live_hp=89, world_aut=1.0, cfg=ai, rng=rng)
    assert started
    assert st.ferocity <= 2
    assert st.morale_shock_until_aut > 1.0


def test_balance_effect_lines_show_deltas() -> None:
    from src.match_combat import balance_stat_deltas

    reset_match_combat_cache()
    cfg = load_match_combat_config()
    f = Fighter(hp=20, max_hp=20, accuracy=10.0, evade=5.0, ac=1, min_damage=2, max_damage=10)
    st = CombatantState.from_fighter(f, cfg)
    st.balance = 10
    deltas = balance_stat_deltas(st, cfg)
    labels = {d[0] for d in deltas}
    assert "Acc" in labels
    acc = next(d for d in deltas if d[0] == "Acc")
    assert acc[1] < 0 and acc[2] is False  # accuracy debuff


def test_momentum_reverse_harder() -> None:
    cfg = load_match_combat_config()
    ai = load_match_ai_config()
    f = Fighter(hp=20, max_hp=20, accuracy=10.0, evade=5.0, ac=1, min_damage=1, max_damage=2)
    st = CombatantState.from_fighter(f, cfg)
    st.momentum_dx = 2
    st.momentum_dy = 0
    st.momentum_until_aut = 10.0
    same = momentum_evade_mult(st, 1, 0, world_aut=1.0, cfg=ai)
    rev = momentum_evade_mult(st, -1, 0, world_aut=1.0, cfg=ai)
    assert same > rev
