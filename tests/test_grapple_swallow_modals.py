"""grapple-swallow-modals: grapple modal copy, 1% swallow escape, conserve strength."""

from __future__ import annotations

from unittest.mock import patch

import tcod.event
from tcod.event import KeySym, Scancode

from src import messages as msg
from src.career import new_career
from src.components import Fighter, Position
from src.downtime_hub import MatchCard
from src.match_render import (
    BG_ALLY_IN_DANGER,
    BG_PREDATOR_ENGULFED,
    BG_PREDATOR_SWALLOWING,
    BG_PREDATOR_WRESTLING,
    apply_grapple_tile_highlights,
    render_map,
)
from src.match_session import (
    MatchEndKind,
    MatchPhase,
    match_footer_text,
    match_grapple_modal_lines,
    match_status_lines,
    match_swallow_modal_lines,
    render_match,
    start_match,
)
from src.roster import generate_market
import random
import tcod.console
from src.match_vore import (
    VoreConfig,
    VorePhase,
    effective_digest_strikes_to_end,
    load_vore_config,
    reset_vore_config_cache,
    swallow_struggle_escape_chance,
)


def _key(sym: KeySym) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=0)


def _red() -> MatchCard:
    return MatchCard("r1_rats", "rats", "red", 1.0)


def test_swallow_escape_chance_is_about_one_percent() -> None:
    reset_vore_config_cache()
    cfg = load_vore_config()
    assert abs(swallow_struggle_escape_chance(cfg) - 0.01) < 1e-9
    assert cfg.swallow_struggle_escape_chance == 0.01


def test_effective_digest_strikes_uncapped_per_conserve() -> None:
    cfg = VoreConfig(digest_strikes_to_end=3)
    assert effective_digest_strikes_to_end(cfg, conserved_strength=0) == 3
    assert effective_digest_strikes_to_end(cfg, conserved_strength=1) == 4
    assert effective_digest_strikes_to_end(cfg, conserved_strength=5) == 8


def test_grapple_modal_named_headline_not_in_status() -> None:
    session = start_match(new_career(player_name="T"), _red(), seed=2)
    enemy = session.living_enemies()[0]
    session.player.components[Fighter].hp = 10
    session._start_grapple(enemy, session.player)
    modal = match_grapple_modal_lines(session)
    assert modal is not None
    joined = " ".join(e.text for e in modal)
    assert "grapples you" in joined.lower()
    assert "Break away" in joined
    status = " ".join(e.text for e in match_status_lines(session))
    assert "grapples you" not in status.lower()
    assert "GRAPPLE — you are held" not in status


def test_swallow_modal_minimal_copy() -> None:
    session = start_match(new_career(player_name="T"), _red(), seed=3)
    enemy = session.living_enemies()[0]
    session._start_grapple(enemy, session.player)
    assert session.grapple is not None
    session.grapple.phase = VorePhase.SWALLOW
    session.grapple.swallow_phase_index = 0
    modal = match_swallow_modal_lines(session)
    assert modal is not None
    joined = " ".join(e.text for e in modal)
    # Narrative present; no phase counters, headlines, or option explanations
    assert "Phase " not in joined
    assert "SWALLOWING" not in joined
    assert "miracle" not in joined.lower()
    assert "1 - struggle | 2 - conserve strength" in joined
    foot = match_footer_text(session)
    assert "1 - struggle" in foot
    assert "2 - conserve strength" in foot


def test_swallow_struggle_uses_fixed_chance_not_grapple_formula() -> None:
    session = start_match(new_career(player_name="T"), _red(), seed=4)
    enemy = session.living_enemies()[0]
    session.player.components[Fighter].hp = 12
    session._start_grapple(enemy, session.player)
    assert session.grapple is not None
    session.grapple.phase = VorePhase.SWALLOW
    # Force fail even if old high odds would succeed
    session.rng.random = lambda: 0.5  # type: ignore[method-assign]
    with patch.object(type(session), "process_npc_until_player", lambda self: None):
        session._prey_swallow_struggle()
    assert session.grapple is not None  # 50% > 1% → fail
    texts = " ".join(e.text for e in session.message_log.entries()).lower()
    assert "thrash" in texts or "gullet" in texts or "claims" in texts


def test_swallow_struggle_miracle_at_zero_roll() -> None:
    session = start_match(new_career(player_name="T"), _red(), seed=5)
    enemy = session.living_enemies()[0]
    session._start_grapple(enemy, session.player)
    assert session.grapple is not None
    session.grapple.phase = VorePhase.SWALLOW
    session.rng.random = lambda: 0.0  # type: ignore[method-assign]
    with patch.object(type(session), "process_npc_until_player", lambda self: None):
        session._prey_swallow_struggle()
    assert session.grapple is None
    texts = " ".join(e.text for e in session.message_log.entries()).lower()
    assert "odds" in texts or "free" in texts


def test_swallow_conserve_increments_and_extends_digest() -> None:
    session = start_match(new_career(player_name="T"), _red(), seed=6)
    enemy = session.living_enemies()[0]
    session._start_grapple(enemy, session.player)
    assert session.grapple is not None
    session.grapple.phase = VorePhase.SWALLOW
    with patch.object(type(session), "process_npc_until_player", lambda self: None):
        session.handle_event(_key(KeySym.N2))
    assert session.grapple is not None
    assert session.grapple.conserved_strength == 1
    # Uncapped — each press adds another
    with patch.object(type(session), "process_npc_until_player", lambda self: None):
        session.handle_event(_key(KeySym.N2))
        session.handle_event(_key(KeySym.N2))
        session.handle_event(_key(KeySym.N2))
    assert session.grapple.conserved_strength == 4

    # Engulfed: need base + conserve before finish
    session.grapple.phase = VorePhase.ENGULFED
    session.grapple.digest_strikes = 0
    need = effective_digest_strikes_to_end(
        session.vore_cfg, conserved_strength=session.grapple.conserved_strength
    )
    assert need == session.vore_cfg.digest_strikes_to_end + session.grapple.conserved_strength
    for _ in range(need - 1):
        session._predator_grapple_act(enemy)
        assert session.phase is MatchPhase.FIGHT
        assert session.grapple is not None
    session._predator_grapple_act(enemy)
    assert session.phase is MatchPhase.RECAP
    assert session.end_kind is MatchEndKind.DIGESTED


def test_direction_keys_do_not_thrash_during_swallow() -> None:
    session = start_match(new_career(player_name="T"), _red(), seed=7)
    enemy = session.living_enemies()[0]
    session._start_grapple(enemy, session.player)
    assert session.grapple is not None
    session.grapple.phase = VorePhase.SWALLOW
    session.awaiting_player = True
    aut_before = session.scheduler._ready_at.get(session.player)
    session.handle_event(_key(KeySym.RIGHT))
    assert session.scheduler._ready_at.get(session.player) == aut_before
    assert session.grapple is not None


def test_predator_grapples_you_message() -> None:
    assert msg.predator_grapples_you("Dire rat") == "Dire rat grapples you!"


def test_grapple_keeps_separate_tiles_swallow_colocates() -> None:
    session = start_match(new_career(player_name="T"), _red(), seed=20)
    enemy = session.living_enemies()[0]
    pp = session.player.components[Position]
    enemy.components[Position] = Position(pp.x + 1, pp.y)
    session.player.components[Fighter].hp = 10
    session._start_grapple(enemy, session.player)
    assert session.grapple is not None
    assert session.grapple.phase is VorePhase.GRAPPLE
    ep = enemy.components[Position]
    pl = session.player.components[Position]
    assert (ep.x, ep.y) != (pl.x, pl.y)
    session._begin_swallow()
    assert session.grapple.phase is VorePhase.SWALLOW
    ep2 = enemy.components[Position]
    pl2 = session.player.components[Position]
    assert (ep2.x, ep2.y) == (pl2.x, pl2.y)


def test_tile_highlights_by_phase() -> None:
    career = new_career(player_name="Boss")
    career.starter_picks_done = True
    offers = generate_market(random.Random(21), count=1, free=True)
    offers[0].deployed = True
    career.set_allies(offers[:1])
    session = start_match(career, _red(), seed=21)
    enemy = session.living_enemies()[0]
    ally = session.living_allies()[0]
    ap = ally.components[Position]
    enemy.components[Position] = Position(ap.x + 1, ap.y)
    session._start_grapple(enemy, ally)
    assert session.grapple is not None
    console = tcod.console.Console(40, 40)
    render_map(console, session.game_map)
    apply_grapple_tile_highlights(
        console, grapple=session.grapple, is_ally=session.is_ally
    )
    ep = enemy.components[Position]
    assert tuple(int(c) for c in console.rgb["bg"][ep.y, ep.x][:3]) == BG_PREDATOR_WRESTLING
    assert tuple(int(c) for c in console.rgb["fg"][ep.y, ep.x][:3]) == BG_PREDATOR_WRESTLING
    ap2 = ally.components[Position]
    assert tuple(int(c) for c in console.rgb["bg"][ap2.y, ap2.x][:3]) == BG_ALLY_IN_DANGER

    session._begin_swallow()
    console2 = tcod.console.Console(40, 40)
    render_match(console2, session)
    ep = enemy.components[Position]
    assert tuple(int(c) for c in console2.rgb["bg"][ep.y, ep.x][:3]) == BG_PREDATOR_SWALLOWING

    session.grapple.phase = VorePhase.ENGULFED
    console3 = tcod.console.Console(40, 40)
    render_match(console3, session)
    assert tuple(int(c) for c in console3.rgb["bg"][ep.y, ep.x][:3]) == BG_PREDATOR_ENGULFED


def test_swallow_footer_has_no_ctrl_q() -> None:
    session = start_match(new_career(player_name="T"), _red(), seed=22)
    enemy = session.living_enemies()[0]
    session._start_grapple(enemy, session.player)
    assert session.grapple is not None
    session.grapple.phase = VorePhase.SWALLOW
    foot = match_footer_text(session)
    assert "Ctrl+Q" not in foot
    assert "ctrl" not in foot.lower()
    assert "1 - struggle" in foot
