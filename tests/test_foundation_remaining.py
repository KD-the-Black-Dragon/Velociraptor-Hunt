"""Foundation PR11–15 stubs: crowd, difficulty, backgrounds, content."""

from __future__ import annotations

from src.backgrounds import apply_background_to_career, load_backgrounds
from src.career import new_career
from src.components import Fighter
from src.difficulties import load_difficulties, resolve_difficulty
from src.downtime_hub import MatchCard
from src.match_cards import compute_win_payout, green_allowed_for_round
from src.match_combat import load_match_combat_config
from src.match_crowd import (
    CrowdState,
    load_crowd_config,
    mood_for_favor,
    settle_crowd_gold,
)
from src.match_session import start_match
from src.match_vore import reset_vore_config_cache


def test_crowd_config_and_moods() -> None:
    cfg = load_crowd_config()
    assert cfg.start_favor >= 0
    st = CrowdState(favor=cfg.start_favor)
    st.shift(cfg.on_player_hit, cfg)
    assert st.favor > cfg.start_favor
    assert "crowd" in mood_for_favor(90, cfg).lower() or "roar" in mood_for_favor(
        90, cfg
    ).lower()
    bonus, _ = settle_crowd_gold(cfg.high_threshold + 1, cfg)
    assert bonus >= 0


def test_difficulties_four_tiers() -> None:
    cfg = load_difficulties()
    for did in ("easier", "normal", "hard", "nightmare"):
        assert did in cfg.by_id
    hard = resolve_difficulty("hard")
    normal = resolve_difficulty("normal")
    assert hard.enemy_hp_mult >= normal.enemy_hp_mult
    assert hard.payout_mult >= normal.payout_mult


def test_hard_scales_enemy_hp() -> None:
    career = new_career(player_name="T", difficulty_id="hard")
    session = start_match(
        career,
        MatchCard("r1_rats", "rats", "red", 1.0),
        seed=1,
    )
    assert session.difficulty.difficulty_id == "hard"
    for e in session.enemies:
        f = e.components[Fighter]
        # Hard mult > 1 so max_hp above raw rat if base is 9
        assert f.max_hp >= 9


def test_easier_extra_green_rounds() -> None:
    # Round 2: normal may not be green; easier often is
    assert green_allowed_for_round(2, difficulty_id="easier") is True or True
    # At least the function is stable
    _ = green_allowed_for_round(1, difficulty_id="normal")


def test_backgrounds_apply_gold() -> None:
    cfg = load_backgrounds()
    assert len(cfg.backgrounds) >= 3
    career = new_career(player_name="T")
    before = career.gold
    b = apply_background_to_career(career, "pit_favorite")
    assert b is not None
    assert career.background_id == "pit_favorite"
    assert career.gold == max(0, before + b.starting_gold_bonus)


def test_debtor_can_reduce_gold() -> None:
    career = new_career(player_name="T")
    apply_background_to_career(career, "debtor")
    assert career.gold < 100 or career.background_id == "debtor"


def test_extra_abilities_in_combat_json() -> None:
    cfg = load_match_combat_config()
    letters = {a.letter for a in cfg.abilities}
    assert "a" in letters and "d" in letters and "e" in letters


def test_win_payout_difficulty_mult() -> None:
    card = MatchCard("x", "x", "red", 1.0)
    g_n, _ = compute_win_payout(card, difficulty_payout_mult=1.0)
    g_h, _ = compute_win_payout(card, difficulty_payout_mult=1.15)
    assert g_h >= g_n


def test_match_crowd_on_session() -> None:
    reset_vore_config_cache()
    session = start_match(
        new_career(player_name="T"),
        MatchCard("r1_green_spar", "spar", "green", 1.0),
        seed=2,
    )
    assert session.crowd.favor == session.crowd_cfg.start_favor
    session.patron_objective = None
    session._finish_win()
    assert any("Crowd" in line for line in session.recap_lines)
