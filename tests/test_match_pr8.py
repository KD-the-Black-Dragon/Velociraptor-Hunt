"""PR8: grapple HP, multi-phase swallow, green/red digest rules."""

from __future__ import annotations

import tcod.event
from tcod.event import KeySym, Scancode

from src.career import new_career
from src.components import Fighter, Position
from src.downtime_hub import MatchCard
from src.match_session import MatchEndKind, MatchPhase, match_footer_text, start_match
from src.match_vore import (
    VoreConfig,
    VorePhase,
    break_away_chance,
    grab_chance,
    load_vore_config,
    pick_flaunt,
    reset_vore_config_cache,
)
from src.roster import AllyRecord, generate_ally, load_roster_tuning


def _key(sym: KeySym) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=0)


def _red_card() -> MatchCard:
    return MatchCard("r1_rats", "rats", "red", 1.0)


def _green_card() -> MatchCard:
    return MatchCard("r1_green_spar", "spar", "green", 0.45)


def test_load_vore_config_from_json() -> None:
    reset_vore_config_cache()
    cfg = load_vore_config()
    assert cfg.swallow_phases >= 1
    assert cfg.swallow_phase_aut >= 4.0
    assert cfg.digest_strikes_to_end >= 1
    assert len(cfg.flaunt_lines) >= 1


def test_grab_chance_higher_when_hurt() -> None:
    cfg = VoreConfig()
    healthy = grab_chance(prey_hp=20, prey_max_hp=20, prey_downed=False, cfg=cfg)
    hurt = grab_chance(prey_hp=4, prey_max_hp=20, prey_downed=False, cfg=cfg)
    downed = grab_chance(prey_hp=0, prey_max_hp=20, prey_downed=True, cfg=cfg)
    assert hurt > healthy
    assert downed >= hurt


def test_break_away_easier_with_more_grapple_hp() -> None:
    cfg = VoreConfig()
    high = break_away_chance(grapple_hp=10, grapple_hp_max=10, cfg=cfg)
    low = break_away_chance(grapple_hp=1, grapple_hp_max=10, cfg=cfg)
    assert high > low


def test_start_match_loads_vore_cfg() -> None:
    session = start_match(new_career(player_name="T"), _green_card(), seed=1)
    assert session.vore_cfg.swallow_phases >= 1
    assert session.grapple is None


def test_grab_starts_grapple_with_stamina_hp() -> None:
    session = start_match(new_career(player_name="T"), _red_card(), seed=2)
    enemy = session.living_enemies()[0]
    pf = session.player.components[Fighter]
    pf.hp = 8
    session._start_grapple(enemy, session.player)
    assert session.grapple is not None
    assert session.grapple.phase is VorePhase.GRAPPLE
    assert session.grapple.grapple_hp == 8
    assert session.grapple.prey is session.player
    assert "seize" in " ".join(e.text for e in session.message_log.entries()).lower()


def test_red_zero_hp_skips_grapple_war() -> None:
    session = start_match(new_career(player_name="T"), _red_card(), seed=3)
    enemy = session.living_enemies()[0]
    pf = session.player.components[Fighter]
    pf.hp = 0
    st = session.combatants[session.player]
    st.downed = True
    session._start_grapple(enemy, session.player)
    assert session.grapple is not None
    assert session.grapple.grapple_hp == 0
    assert session.grapple.phase is VorePhase.SWALLOW


def test_green_zero_hp_still_grapples() -> None:
    session = start_match(new_career(player_name="T"), _green_card(), seed=4)
    enemy = session.living_enemies()[0]
    pf = session.player.components[Fighter]
    pf.hp = 0
    st = session.combatants[session.player]
    st.downed = True
    session._start_grapple(enemy, session.player)
    assert session.grapple is not None
    # Green does not skip war; still starts in GRAPPLE (ghp at least 1 when hp was 0)
    assert session.grapple.phase is VorePhase.GRAPPLE


def test_predator_secure_reduces_grapple_hp() -> None:
    session = start_match(new_career(player_name="T"), _red_card(), seed=5)
    enemy = session.living_enemies()[0]
    session.player.components[Fighter].hp = 10
    session._start_grapple(enemy, session.player)
    assert session.grapple is not None
    before = session.grapple.grapple_hp
    # Force secure path (not crush)
    session.rng.random = lambda: 0.9  # type: ignore[method-assign]
    session._predator_grapple_act(enemy)
    assert session.grapple is not None
    assert session.grapple.grapple_hp < before or session.grapple.phase is VorePhase.SWALLOW


def test_prey_break_away_can_release() -> None:
    from unittest.mock import patch

    session = start_match(new_career(player_name="T"), _red_card(), seed=6)
    enemy = session.living_enemies()[0]
    session.player.components[Fighter].hp = 12
    session._start_grapple(enemy, session.player)
    assert session.grapple is not None
    session.rng.random = lambda: 0.0  # type: ignore[method-assign]  # always succeed
    # Avoid post-release NPC loop re-grabbing under forced 0.0 rolls
    with patch.object(type(session), "process_npc_until_player", lambda self: None):
        session._prey_break_away(spend_aut=True)
    assert session.grapple is None
    texts = " ".join(e.text for e in session.message_log.entries()).lower()
    assert "free" in texts


def test_green_aborts_before_digest() -> None:
    session = start_match(new_career(player_name="T"), _green_card(), seed=7)
    enemy = session.living_enemies()[0]
    session.player.components[Fighter].hp = 5
    session._start_grapple(enemy, session.player)
    assert session.grapple is not None
    session.grapple.phase = VorePhase.SWALLOW
    session.grapple.swallow_phase_index = session.vore_cfg.swallow_phases - 1
    session._predator_grapple_act(enemy)
    # After completing last swallow phase on green, release (no engulf)
    assert session.grapple is None
    texts = " ".join(e.text for e in session.message_log.entries()).lower()
    assert "exhibition" in texts or "let go" in texts


def test_red_digest_ends_career_recap() -> None:
    session = start_match(new_career(player_name="T"), _red_card(), seed=8)
    enemy = session.living_enemies()[0]
    session.player.components[Fighter].hp = 5
    session._start_grapple(enemy, session.player)
    assert session.grapple is not None
    session.grapple.phase = VorePhase.ENGULFED
    session.grapple.digest_strikes = session.vore_cfg.digest_strikes_to_end - 1
    session._predator_grapple_act(enemy)
    assert session.phase is MatchPhase.RECAP
    assert session.end_kind is MatchEndKind.DIGESTED
    assert "digested" in session.recap_lines[0].lower()
    assert session.grapple is None


def test_assist_damage_can_force_release() -> None:
    session = start_match(new_career(player_name="T"), _red_card(), seed=9)
    enemy = session.living_enemies()[0]
    session.player.components[Fighter].hp = 10
    session._start_grapple(enemy, session.player)
    assert session.grapple is not None
    ef = enemy.components[Fighter]
    # One big chunk of assist damage
    need = ef.max_hp * session.vore_cfg.ally_assist_release_damage_fraction
    session._note_assist_damage(enemy, need + 1.0)
    assert session.grapple is None
    texts = " ".join(e.text for e in session.message_log.entries()).lower()
    assert "let go" in texts or "force" in texts


def test_regurgitate_when_predator_critically_hurt() -> None:
    session = start_match(new_career(player_name="T"), _red_card(), seed=10)
    enemy = session.living_enemies()[0]
    session.player.components[Fighter].hp = 10
    session._start_grapple(enemy, session.player)
    assert session.grapple is not None
    ef = enemy.components[Fighter]
    ef.hp = max(1, int(ef.max_hp * session.vore_cfg.regurgitate_predator_hp_fraction) - 1)
    session._predator_grapple_act(enemy)
    assert session.grapple is None
    texts = " ".join(e.text for e in session.message_log.entries()).lower()
    assert "release" in texts or "heave" in texts


def test_grapple_footer_when_held() -> None:
    session = start_match(new_career(player_name="T"), _red_card(), seed=11)
    enemy = session.living_enemies()[0]
    session._start_grapple(enemy, session.player)
    foot = match_footer_text(session)
    assert "Break away" in foot or "Grappled" in foot


def test_engulfed_input_still_works() -> None:
    session = start_match(new_career(player_name="T"), _red_card(), seed=12)
    enemy = session.living_enemies()[0]
    session._start_grapple(enemy, session.player)
    assert session.grapple is not None
    session.grapple.phase = VorePhase.ENGULFED
    session.awaiting_player = True
    session.handle_event(_key(KeySym.PERIOD))
    texts = " ".join(e.text for e in session.message_log.entries()).lower()
    assert "thrash" in texts


def test_beast_ally_vore_flag() -> None:
    tuning = load_roster_tuning()
    # Force wolf (beast) via many rolls; also direct record
    rec = AllyRecord(
        ally_id="x",
        name="W",
        species_id="wolf",
        tier="scrub",
        hire_cost=10,
        vore_capable=True,
    )
    assert rec.vore_capable is True
    assert "wolf" in tuning.beast_vore_species
    # kobold anthro default
    k = AllyRecord(
        ally_id="y",
        name="K",
        species_id="kobold",
        tier="scrub",
        hire_cost=5,
        vore_capable=False,
    )
    assert k.vore_capable is False
    # generate respects species list
    found_beast = False
    found_anthro = False
    for seed in range(40):
        a = generate_ally(__import__("random").Random(seed), free=True, tuning=tuning)
        if a.species_id in tuning.beast_vore_species:
            assert a.vore_capable is True
            found_beast = True
        else:
            assert a.vore_capable is False
            found_anthro = True
        if found_beast and found_anthro:
            break
    assert found_beast or found_anthro  # at least one path exercised


def test_flaunt_line_nonempty() -> None:
    import random

    cfg = load_vore_config()
    line = pick_flaunt(random.Random(0), cfg)
    assert isinstance(line, str) and len(line) > 5


def test_grab_clears_pending_reaction() -> None:
    from src.match_tactics import PendingReaction

    session = start_match(new_career(player_name="T"), _red_card(), seed=20)
    enemy = session.living_enemies()[0]
    other = session.living_enemies()[1] if len(session.living_enemies()) > 1 else enemy
    session.pending_reaction = PendingReaction(
        attacker=other,
        attack_aut_cost=1.2,
        style_label="attack",
        announce="A foe swings at you!",
    )
    session._start_grapple(enemy, session.player)
    assert session.grapple is not None
    assert session.pending_reaction is None


def test_other_enemy_cannot_damage_grappled_prey() -> None:
    session = start_match(new_career(player_name="T"), _red_card(), seed=21)
    enemies = session.living_enemies()
    assert len(enemies) >= 2
    predator, bystander = enemies[0], enemies[1]
    pf = session.player.components[Fighter]
    pf.hp = 20
    session._start_grapple(predator, session.player)
    hp_before = pf.hp
    # Bystander melee is hard-gated — no damage
    session._melee(
        bystander,
        session.player,
        cost=1.2,
        damage_mult=10.0,
        accuracy_mult=99.0,
    )
    assert pf.hp == hp_before
    assert session._attacker_may_hit(predator, session.player) is True
    assert session._attacker_may_hit(bystander, session.player) is False


def test_other_enemies_do_not_open_reaction_while_pc_held() -> None:
    session = start_match(new_career(player_name="T"), _red_card(), seed=22)
    enemies = session.living_enemies()
    assert len(enemies) >= 2
    predator, bystander = enemies[0], enemies[1]
    session._start_grapple(predator, session.player)
    assert session.grapple is not None
    session.pending_reaction = None
    # Bystander would normally swing; obscured prey → wait, no reaction
    pp = session.player.components[Position]
    bystander.components[Position] = Position(pp.x + 1, pp.y)
    session._npc_act(bystander)
    assert session.pending_reaction is None
    # PC is not a valid free target while held
    assert session._is_obscured_prey(session.player)


def test_grapple_input_beats_stale_reaction_modal() -> None:
    from src.match_tactics import PendingReaction

    session = start_match(new_career(player_name="T"), _red_card(), seed=23)
    enemy = session.living_enemies()[0]
    session._start_grapple(enemy, session.player)
    # Force a stale modal (should never stick in play; input path clears it)
    session.pending_reaction = PendingReaction(
        attacker=enemy,
        attack_aut_cost=1.2,
        style_label="attack",
        announce="stale swing",
    )
    session.awaiting_player = True
    session.rng.random = lambda: 0.99  # type: ignore[method-assign]  # fail break
    from unittest.mock import patch

    with patch.object(type(session), "process_npc_until_player", lambda self: None):
        session.handle_event(_key(KeySym.N1))
    assert session.pending_reaction is None
    foot = match_footer_text(session)
    assert "Break away" in foot or "Grappled" in foot or session.grapple is None
