"""Solo Duels career: 1v1 focus; company team path preserved but unused by default."""

from __future__ import annotations

from pathlib import Path

import tcod.event
from tcod.event import KeySym, Scancode

from src.career import (
    CAMPAIGN_STYLE_COMPANY,
    CAMPAIGN_STYLE_SOLO,
    CareerState,
    new_career,
)
from src.downtime_hub import (
    DowntimeHubState,
    HubView,
    downtime_display_lines,
    hub_root_options,
    handle_downtime_event,
)
from src.instant_action import cards_for_kind, resolve_card_id, start_instant_match
from src.match_cards import (
    is_solo_eligible_card,
    load_match_cards_config,
    pick_match_offers,
    reset_match_cards_cache,
)
from src.match_session import start_match
from src.downtime_hub import MatchCard


def _key(sym: KeySym) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=0)


def test_new_career_is_solo_by_default() -> None:
    c = new_career(player_name="Duelist")
    assert c.campaign_style == CAMPAIGN_STYLE_SOLO
    assert c.is_solo()
    assert c.starter_picks_done is True
    assert c.max_deployed_allies == 0
    assert c.roster == []


def test_company_career_still_constructible() -> None:
    c = new_career(player_name="Captain", campaign_style=CAMPAIGN_STYLE_COMPANY)
    assert c.is_company()
    assert c.starter_picks_done is False
    assert c.max_deployed_allies >= 1


def test_career_save_roundtrip_solo() -> None:
    c = new_career(player_name="Duelist")
    c.gold = 55
    d = c.to_dict()
    assert d["campaign_style"] == "solo"
    c2 = CareerState.from_dict(d)
    assert c2.is_solo()
    assert c2.gold == 55
    assert c2.max_deployed_allies == 0


def test_missing_style_loads_as_solo() -> None:
    c = CareerState.from_dict(
        {
            "player_name": "Old",
            "gold": 10,
            "renown": 0,
            "round_index": 1,
            "difficulty_id": "normal",
            "roster": [{"should": "be_cleared_if_solo"}],
        }
    )
    assert c.is_solo()
    assert c.roster == []


def test_solo_hub_options_hide_team() -> None:
    c = new_career(player_name="D")
    opts = hub_root_options(c)
    joined = " ".join(opts)
    assert "Hire" not in joined
    assert "Assign" not in joined
    assert "Select next match" in joined
    company = new_career(player_name="C", campaign_style=CAMPAIGN_STYLE_COMPANY)
    c_opts = hub_root_options(company)
    assert any("Hire" in o for o in c_opts)


def test_solo_hub_skips_starter_gate() -> None:
    c = new_career(player_name="D")
    hub = DowntimeHubState()
    hub.ensure_starter_gate(c)
    assert hub.view is HubView.ROOT
    assert c.starter_picks_done


def test_solo_eligible_card_helper() -> None:
    reset_match_cards_cache()
    cfg = load_match_cards_config()
    assert is_solo_eligible_card(cfg.by_id["d1_rat"])
    assert not is_solo_eligible_card(cfg.by_id["r1_rats"])


def test_solo_match_offers_only_1v1() -> None:
    reset_match_cards_cache()
    offers = pick_match_offers(1, difficulty_id="normal", solo_only=True, rng=__import__("random").Random(1))
    assert offers
    for card in offers:
        assert len(card.enemies) == 1
        assert card.enemies[0][1] == 1
        assert card.max_allies == 0


def test_solo_start_match_one_enemy() -> None:
    c = new_career(player_name="D")
    card = MatchCard(
        card_id="d1_rat",
        title="Dire rat duel",
        kind="red",
        payout_mult=1.0,
        max_allies=0,
        enemies=(("rat", 1),),
    )
    session = start_match(c, card, seed=1)
    assert len(session.living_enemies()) == 1
    assert not session.living_allies()


def test_solo_start_match_clamps_multi_card() -> None:
    """Guard: even if a multi card is forced, solo career spawns one foe."""
    c = new_career(player_name="D")
    card = MatchCard(
        card_id="r1_rats",
        title="3 rats",
        kind="red",
        payout_mult=1.0,
        max_allies=2,
        enemies=(("rat", 3),),
    )
    session = start_match(c, card, seed=1)
    assert len(session.living_enemies()) == 1


def test_instant_action_solo_only_list() -> None:
    red = cards_for_kind("red")
    assert all(is_solo_eligible_card(c) for c in red)
    assert not any(c.card_id == "r1_rats" for c in red)
    card, err = resolve_card_id("red", "r1_rats")
    assert card is None and err


def test_instant_start_uses_solo_career() -> None:
    card, err = resolve_card_id("red", "d1_rat")
    assert not err and card is not None
    session = start_instant_match(card, seed=2)
    assert session.career.is_solo()
    assert len(session.living_enemies()) == 1


def test_solo_display_shows_campaign_label() -> None:
    c = new_career(player_name="D")
    hub = DowntimeHubState()
    text = " ".join(line.text for line in downtime_display_lines(c, hub))
    assert "Solo Duels" in text
