"""PR10: thin patrons — 3 patrons, objectives, gold bonus on hit only."""

from __future__ import annotations

import random

from src.career import CareerState, new_career
from src.downtime_hub import MatchCard
from src.match_session import MatchEndKind, start_match
from src.patrons import (
    ActivePatronObjective,
    MatchPatronStats,
    assign_patron_objective,
    evaluate_objective,
    load_patrons_config,
    objective_eligible,
    reset_patrons_cache,
)


def test_patrons_json_has_three() -> None:
    reset_patrons_cache()
    cfg = load_patrons_config()
    assert len(cfg.patrons) == 3
    assert len(cfg.objectives) >= 3


def test_objective_eligibility_filters_kind_and_allies() -> None:
    cfg = load_patrons_config()
    red_only = [o for o in cfg.objectives if o.requires_kind == "red"]
    if red_only:
        assert objective_eligible(
            red_only[0], card_kind="red", has_deployed_allies=True
        )
        assert not objective_eligible(
            red_only[0], card_kind="green", has_deployed_allies=True
        )
    ally_req = [o for o in cfg.objectives if o.requires_allies]
    if ally_req:
        assert not objective_eligible(
            ally_req[0], card_kind="red", has_deployed_allies=False
        )
        assert objective_eligible(
            ally_req[0], card_kind="red", has_deployed_allies=True
        )


def test_assign_always_returns_eligible() -> None:
    cfg = load_patrons_config()
    for kind in ("red", "green"):
        for has_allies in (False, True):
            obj = assign_patron_objective(
                card_kind=kind,
                has_deployed_allies=has_allies,
                rng=random.Random(0),
                cfg=cfg,
            )
            assert obj is not None
            # Re-check sanity
            raw = next(
                (o for o in cfg.objectives if o.objective_id == obj.objective_id),
                None,
            )
            if raw is not None:
                assert objective_eligible(
                    raw, card_kind=kind, has_deployed_allies=has_allies
                ) or raw.kind == "win"


def test_evaluate_win_hit_and_miss() -> None:
    active = ActivePatronObjective(
        patron_id="vex",
        patron_name="Lady Vex",
        patron_epithet="the Blood Sport",
        objective_id="win_any",
        label="Win the bout",
        bonus_gold=25,
        kind="win",
    )
    hit, bonus, line = evaluate_objective(
        active, MatchPatronStats(end_kind="win", world_aut=5.0)
    )
    assert hit is True
    assert bonus == 25
    assert "met" in line.lower()
    miss, bonus2, line2 = evaluate_objective(
        active, MatchPatronStats(end_kind="loss", world_aut=5.0)
    )
    assert miss is False
    assert bonus2 == 0
    assert "missed" in line2.lower()


def test_evaluate_win_under_aut() -> None:
    active = ActivePatronObjective(
        patron_id="rusk",
        patron_name="Rusk",
        patron_epithet="Coin",
        objective_id="win_fast",
        label="Win fast",
        bonus_gold=40,
        kind="win_under_aut",
        max_aut=10.0,
    )
    ok, b, _ = evaluate_objective(
        active, MatchPatronStats(end_kind="win", world_aut=9.0)
    )
    assert ok and b == 40
    late, b2, _ = evaluate_objective(
        active, MatchPatronStats(end_kind="win", world_aut=11.0)
    )
    assert not late and b2 == 0


def test_evaluate_no_pc_down() -> None:
    active = ActivePatronObjective(
        patron_id="halm",
        patron_name="Halm",
        patron_epithet="Mercy",
        objective_id="no_down",
        label="No collapse",
        bonus_gold=30,
        kind="win_no_pc_down",
    )
    ok, _, _ = evaluate_objective(
        active, MatchPatronStats(end_kind="win", pc_was_downed=False)
    )
    assert ok
    bad, _, _ = evaluate_objective(
        active, MatchPatronStats(end_kind="win", pc_was_downed=True)
    )
    assert not bad


def test_start_match_assigns_patron() -> None:
    session = start_match(
        new_career(player_name="T"),
        MatchCard("r1_rats", "rats", "red", 1.0),
        seed=11,
    )
    assert session.patron_objective is not None
    texts = " ".join(e.text for e in session.message_log.entries())
    assert "Patron:" in texts or session.patron_objective.patron_name in texts


def test_win_grants_patron_bonus_when_objective_is_win() -> None:
    career = new_career(player_name="T")
    session = start_match(
        career,
        MatchCard("r1_green_spar", "spar", "green", 1.0, enemies=(("rat", 1),)),
        seed=12,
    )
    # Force a simple win objective
    session.patron_objective = ActivePatronObjective(
        patron_id="vex",
        patron_name="Lady Vex",
        patron_epithet="Blood",
        objective_id="win_any",
        label="Win the bout",
        bonus_gold=25,
        kind="win",
    )
    gold_before = career.gold
    session._finish_win()
    assert session.end_kind is MatchEndKind.WIN
    # Base win gold + 25 patron
    assert career.gold >= gold_before + 25
    assert any("objective met" in line.lower() for line in session.recap_lines)
    assert "met" in career.last_patron_result.lower()


def test_loss_misses_objective_no_penalty() -> None:
    career = new_career(player_name="T")
    gold_before = career.gold
    session = start_match(
        career,
        MatchCard("r1_green_spar", "spar", "green", 1.0),
        seed=13,
    )
    session.patron_objective = ActivePatronObjective(
        patron_id="vex",
        patron_name="Lady Vex",
        patron_epithet="Blood",
        objective_id="win_any",
        label="Win the bout",
        bonus_gold=25,
        kind="win",
    )
    session._finish_loss()
    # Appearance fee only — no extra 25, and no gold removal beyond none
    assert not any("objective met" in line.lower() for line in session.recap_lines)
    assert any("missed" in line.lower() for line in session.recap_lines)
    assert career.gold >= gold_before  # loss still pays appearance fee on green


def test_career_last_patron_result_persists() -> None:
    c = CareerState(player_name="P", last_patron_result="Lady Vex: objective met (+25 gold)")
    d = c.to_dict()
    c2 = CareerState.from_dict(d)
    assert "Lady Vex" in c2.last_patron_result


def test_talk_objective_tracks_talk() -> None:
    session = start_match(
        new_career(player_name="T"),
        MatchCard("r1_green_spar", "spar", "green", 1.0),
        seed=14,
    )
    session.patron_objective = ActivePatronObjective(
        patron_id="halm",
        patron_name="Halm",
        patron_epithet="Mercy",
        objective_id="talk",
        label="Talk then win",
        bonus_gold=22,
        kind="win_after_talk",
    )
    session.patron_stats.talk_used = True
    hit, bonus, _ = evaluate_objective(
        session.patron_objective,
        MatchPatronStats(end_kind="win", talk_used=True),
    )
    assert hit and bonus == 22
    miss, _, _ = evaluate_objective(
        session.patron_objective,
        MatchPatronStats(end_kind="win", talk_used=False),
    )
    assert not miss
