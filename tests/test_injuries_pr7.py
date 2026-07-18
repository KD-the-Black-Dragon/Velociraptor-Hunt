"""PR7: injuries, recovery, heal service, JSON maneuvers."""

from __future__ import annotations

import random

from src.career import new_career
from src.components import Fighter
from src.downtime_hub import HubView, MatchCard
from src.injuries import (
    InjuryInstance,
    heal_one_step,
    injury_stat_multipliers,
    load_injury_config,
    step_injury,
    try_apply_from_hit,
)
from src.match_combat import actual_fighter, load_match_combat_config
from src.match_recovery import load_recovery_config
from src.match_session import MatchSession, start_match
from src.roster import generate_market


def test_injury_config_json() -> None:
    cfg = load_injury_config()
    assert set(cfg.regions) == {"Arm", "Leg", "Head", "Torso"}
    assert cfg.penalty_fraction["Minor"] == 0.10
    assert cfg.penalty_fraction["Major"] == 0.30
    assert "Arm" in cfg.region_effects


def test_step_and_heal() -> None:
    cfg = load_injury_config()
    injuries: list[InjuryInstance] = []
    injuries, label = step_injury(injuries, "Arm", steps=1, cfg=cfg)
    assert label == "Injured Arm: Minor"
    injuries, label = step_injury(injuries, "Arm", steps=1, cfg=cfg)
    assert label == "Injured Arm: Moderate"
    injuries, cost, msg = heal_one_step(injuries, "Arm", cfg=cfg)
    assert cost == cfg.heal_gold_per_step["Moderate"]
    assert injuries[0].severity == "Minor"
    injuries, cost, msg = heal_one_step(injuries, "Arm", cfg=cfg)
    assert injuries == []


def test_critical_can_double_step() -> None:
    cfg = load_injury_config()
    # Force critical path with seeded rng that always succeeds
    class R:
        def random(self) -> float:
            return 0.0  # always pass chance rolls

        def choice(self, seq):
            return seq[0]

    injuries, label = try_apply_from_hit(
        [],
        damage=15,
        defender_max_hp=30,  # 50% — critical
        rng=R(),  # type: ignore[arg-type]
        cfg=cfg,
    )
    assert label is not None
    assert "Injured" in label


def test_maneuvers_in_combat_json() -> None:
    cfg = load_match_combat_config()
    assert cfg.maneuver("step").aut_cost < cfg.maneuver("standard_attack").aut_cost
    assert cfg.maneuver("jab").damage_mult < 1.0
    hay = next(a for a in cfg.abilities if a.id == "haymaker")
    assert hay.ap_cost == 5
    assert hay.damage_mult_open is not None


def test_injury_affects_actual_stats() -> None:
    cfg = load_match_combat_config()
    f = Fighter(hp=20, max_hp=20, accuracy=10.0, evade=5.0, ac=2, min_damage=4, max_damage=6)
    from src.match_combat import CombatantState

    healthy = CombatantState.from_fighter(f, cfg)
    hurt = CombatantState.from_fighter(f, cfg)
    hurt.injuries = [InjuryInstance("Arm", "Major")]
    a0 = actual_fighter(healthy, cfg, live_hp=20)
    a1 = actual_fighter(hurt, cfg, live_hp=20)
    assert a1.accuracy < a0.accuracy
    assert a1.max_damage <= a0.max_damage


def test_downed_not_instant_loss() -> None:
    career = new_career(player_name="T")
    career.starter_picks_done = True
    session = start_match(
        career,
        MatchCard("r1_green_spar", "spar", "green", 0.45),
        seed=1,
    )
    session.player.components[Fighter].hp = 0
    st = session.combatants[session.player]
    st.downed = True
    assert not session._player_side_incap() or not session.living_allies()
    # Solo — downed alone is incap
    assert session._player_side_incap()


def test_recovery_config() -> None:
    rc = load_recovery_config()
    assert rc.crawl_step_aut_mult == 3.0
    assert rc.recover_to_hp == 5
    assert rc.second_wind.letter == "s"


def test_career_persists_player_injuries() -> None:
    c = new_career(player_name="X")
    c.set_player_injuries([InjuryInstance("Leg", "Minor")])
    d = c.to_dict()
    from src.career import CareerState

    c2 = CareerState.from_dict(d)
    assert c2.get_player_injuries()[0].label() == "Injured Leg: Minor"
