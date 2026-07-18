"""PR9: match card pools, economy JSON, green surrender."""

from __future__ import annotations

import tcod.event
from tcod.event import KeySym, Scancode

from src.career import new_career
from src.downtime_hub import MatchCard, stub_cards_for_round
from src.match_cards import (
    compute_loss_payout,
    compute_surrender_payout,
    compute_win_payout,
    eligible_card_defs,
    enemies_for_card,
    green_allowed_for_round,
    load_match_cards_config,
    pick_match_offers,
    reset_match_cards_cache,
)
from src.match_session import MatchEndKind, MatchPhase, start_match


def _key(sym: KeySym) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=0)


def test_match_cards_json_loads() -> None:
    reset_match_cards_cache()
    cfg = load_match_cards_config()
    assert cfg.offer_count == 3
    assert len(cfg.cards) >= 5
    assert "r1_rats" in cfg.by_id
    assert cfg.economy.win_gold_base >= 1
    assert cfg.economy.surrender_min_world_aut > 0


def test_green_rounds_filter() -> None:
    cfg = load_match_cards_config()
    assert green_allowed_for_round(1, difficulty_id="normal", cfg=cfg)
    # Round 2 normal: not in base green list
    assert not green_allowed_for_round(2, difficulty_id="normal", cfg=cfg)
    # Easier gets extra green rounds
    if cfg.green_rounds_easier_extra:
        extra = cfg.green_rounds_easier_extra[0]
        assert green_allowed_for_round(extra, difficulty_id="easier", cfg=cfg)


def test_pick_offers_size_and_kinds() -> None:
    import random

    cfg = load_match_cards_config()
    # Non-green round: all red
    offers = pick_match_offers(2, difficulty_id="normal", rng=random.Random(1), cfg=cfg)
    assert 1 <= len(offers) <= cfg.offer_count
    assert all(c.kind == "red" for c in offers)
    # Green round may include green
    pool = eligible_card_defs(1, difficulty_id="normal", cfg=cfg)
    assert any(c.kind == "green" for c in pool) or any(c.kind == "red" for c in pool)


def test_enemies_for_card_from_catalog() -> None:
    card = MatchCard("r1_rats", "rats", "red", 1.0)
    enemies = enemies_for_card(card)
    assert enemies == (("rat", 3),) or any(e[0] == "rat" for e in enemies)


def test_start_match_spawns_from_card_enemies() -> None:
    card = MatchCard(
        "custom",
        "two bats",
        "red",
        1.0,
        enemies=(("bat", 2),),
    )
    session = start_match(new_career(player_name="T"), card, seed=1)
    assert len(session.enemies) == 2


def test_win_payout_uses_economy() -> None:
    cfg = load_match_cards_config()
    red = MatchCard("x", "x", "red", 2.0)
    gold, renown = compute_win_payout(red, cfg.economy)
    assert gold == max(1, int(round(cfg.economy.win_gold_base * 2.0)))
    assert renown == cfg.economy.win_renown_red
    green = MatchCard("y", "y", "green", 0.5)
    g_gold, g_ren = compute_win_payout(green, cfg.economy)
    assert g_gold < gold
    assert g_ren == cfg.economy.win_renown_green


def test_green_underpays_vs_red_loss_base() -> None:
    cfg = load_match_cards_config()
    # Green win with mult 0.45 vs red win mult 1.0 — green lower
    g, _ = compute_win_payout(MatchCard("g", "g", "green", 0.45), cfg.economy)
    r, _ = compute_win_payout(MatchCard("r", "r", "red", 1.0), cfg.economy)
    assert g < r


def test_surrender_denied_too_early() -> None:
    session = start_match(
        new_career(player_name="T"),
        MatchCard("r1_green_spar", "spar", "green", 0.45),
        seed=2,
    )
    session.scheduler.world_aut = 0.0
    session.awaiting_player = True
    session.handle_event(_key(KeySym.G))
    assert session.phase is MatchPhase.FIGHT
    texts = " ".join(e.text for e in session.message_log.entries()).lower()
    assert "too early" in texts or "cry off" in texts


def test_surrender_denied_on_red() -> None:
    session = start_match(
        new_career(player_name="T"),
        MatchCard("r1_rats", "rats", "red", 1.0),
        seed=3,
    )
    session.scheduler.world_aut = 99.0
    session.awaiting_player = True
    session.handle_event(_key(KeySym.G))
    assert session.phase is MatchPhase.FIGHT
    assert session.end_kind is None
    texts = " ".join(e.text for e in session.message_log.entries()).lower()
    assert "red" in texts or "cannot surrender" in texts


def test_surrender_succeeds_on_green_after_min_aut() -> None:
    cfg = load_match_cards_config()
    session = start_match(
        new_career(player_name="T"),
        MatchCard("r1_green_spar", "spar", "green", 0.45),
        seed=4,
    )
    session.scheduler.world_aut = cfg.economy.surrender_min_world_aut + 1.0
    session.awaiting_player = True
    gold_before = session.career.gold
    round_before = session.career.round_index
    session.handle_event(_key(KeySym.G))
    assert session.phase is MatchPhase.RECAP
    assert session.end_kind is MatchEndKind.SURRENDER
    assert session.career.round_index == round_before + 1
    assert session.career.gold > gold_before
    assert "Surrender" in session.recap_lines[0]


def test_surrender_payout_scales_with_aut() -> None:
    cfg = load_match_cards_config()
    card = MatchCard("r1_green_spar", "spar", "green", 1.0)
    g_early, _, f_early = compute_surrender_payout(
        card, world_aut=cfg.economy.surrender_min_world_aut, economy=cfg.economy
    )
    g_late, _, f_late = compute_surrender_payout(
        card, world_aut=50.0, economy=cfg.economy
    )
    assert f_late >= f_early
    assert g_late >= g_early


def test_stub_cards_for_round_compat() -> None:
    cards = stub_cards_for_round(1, difficulty_id="normal", seed=42)
    assert len(cards) >= 1
    assert len(cards) <= load_match_cards_config().offer_count
    assert all(isinstance(c, MatchCard) for c in cards)


def test_win_settlement_uses_json_base() -> None:
    cfg = load_match_cards_config()
    session = start_match(
        new_career(player_name="T"),
        MatchCard("r1_green_spar", "spar", "green", 1.0, enemies=(("rat", 1),)),
        seed=5,
    )
    # Disable patron bonus so we assert pure match economy
    session.patron_objective = None
    session._finish_win()
    gold, renown = compute_win_payout(session.card, cfg.economy)
    assert session.gold_delta == gold
    assert session.renown_delta == renown
    assert session.end_kind is MatchEndKind.WIN
