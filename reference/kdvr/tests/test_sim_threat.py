"""PR3 tests for sim threat, consumables, rest, bail."""

from __future__ import annotations

import pytest

from src.components import Fighter, Inventory, Position, Stunned
from src.engine import GameEngine
from src.map_gen import GameMap, Tile, stairs_positions
from src.sim.inventory_policy import (
    has_potion_effect,
    try_stunned_recovery,
)
from src.sim.policy import SimActionKind, SimPolicy
from src.sim.snapshots import FloorTrackingState
from src.sim.runner import SimTrajectoryRun
from src.sim.threat import (
    lethal_risk_active,
    rest_imperfection_skips,
    update_bail_for_survival,
)
from tests.entity_test_helpers import spawn_fixture_wolf
from src.systems.combat import sync_stunned_state
from src.systems.inventory import make_potion_instance
from tests.map_test_helpers import carve_floor_rect, isolate_other_ais, relocate_player


@pytest.fixture(scope="module", autouse=True)
def _stock_data() -> None:
    from src.sim.data_loader import install_stock_game_data

    install_stock_game_data()


def test_stunned_recovery_uses_heal_potion() -> None:
    engine = GameEngine(save_coordinator=None, skip_new_game=True)
    engine.new_game(seed=1, log_session_milestones=False)
    player = engine.player
    assert player is not None
    fighter = player.components[Fighter]
    fighter.hp = 0
    player.tags.add(Stunned)
    player.components[Inventory].slots["a"] = make_potion_instance("healing_potion")

    tracking = FloorTrackingState()
    tracking.begin_floor(floor=1, seed=1, runes_collected=0)
    assert try_stunned_recovery(engine, visit=tracking.visit)
    assert fighter.hp > 0
    assert Stunned not in player.tags
    assert tracking.visit is not None
    assert tracking.visit.consumable_heal == 1


def test_stunned_recovery_uses_teleport_without_heal() -> None:
    engine = GameEngine(save_coordinator=None, skip_new_game=True)
    engine.new_game(seed=2, log_session_milestones=False)
    player = engine.player
    assert player is not None
    fighter = player.components[Fighter]
    fighter.hp = 0
    player.tags.add(Stunned)
    player.components[Inventory].slots["b"] = make_potion_instance("potion_of_teleportation")

    tracking = FloorTrackingState()
    tracking.begin_floor(floor=1, seed=2, runes_collected=0)
    assert try_stunned_recovery(engine, visit=tracking.visit)
    assert tracking.visit is not None
    assert tracking.visit.consumable_teleport == 1


def test_lethal_risk_active_when_multiple_evils_visible() -> None:
    engine = GameEngine(save_coordinator=None, skip_new_game=True)
    engine.new_game(seed=3, log_session_milestones=False)
    carve_floor_rect(engine, 40, 20, 55, 24)
    relocate_player(engine, 42, 22)
    wolf_a = spawn_fixture_wolf(engine.world, 44, 22)
    wolf_b = spawn_fixture_wolf(engine.world, 45, 22)
    isolate_other_ais(engine, keep=(wolf_a, wolf_b))
    engine._update_fov()
    assert lethal_risk_active(engine)


def test_bail_latches_without_heal_and_low_hp() -> None:
    engine = GameEngine(save_coordinator=None, skip_new_game=True)
    engine.new_game(seed=4, log_session_milestones=False)
    carve_floor_rect(engine, 40, 20, 50, 24)
    relocate_player(engine, 42, 22)
    fighter = engine.player.components[Fighter]
    fighter.hp = max(1, fighter.max_hp // 5)
    wolf = spawn_fixture_wolf(engine.world, 44, 22)
    isolate_other_ais(engine, keep=(wolf,))
    engine._update_fov()

    tracking = FloorTrackingState()
    tracking.begin_floor(floor=1, seed=4, runes_collected=0)
    visit = tracking.visit
    assert visit is not None
    assert not has_potion_effect(engine.player, "heal")
    update_bail_for_survival(engine, visit)
    assert visit.bail_for_survival


def test_policy_returns_rest_when_hurt_and_safe() -> None:
    engine = GameEngine(save_coordinator=None, skip_new_game=True)
    engine.new_game(seed=5, log_session_milestones=False)
    carve_floor_rect(engine, 30, 18, 50, 26)
    relocate_player(engine, 40, 22)
    isolate_other_ais(engine)
    fighter = engine.player.components[Fighter]
    fighter.hp = max(1, fighter.max_hp - 5)
    engine._update_fov()

    tracking = FloorTrackingState()
    tracking.begin_floor(floor=1, seed=5, runes_collected=0)
    policy = SimPolicy()
    action = policy.decide(engine, tracking=tracking)
    assert action.kind is SimActionKind.REST


def test_policy_stunned_returns_consume() -> None:
    engine = GameEngine(save_coordinator=None, skip_new_game=True)
    engine.new_game(seed=6, log_session_milestones=False)
    fighter = engine.player.components[Fighter]
    fighter.hp = 0
    sync_stunned_state(engine.player)

    tracking = FloorTrackingState()
    tracking.begin_floor(floor=1, seed=6, runes_collected=0)
    policy = SimPolicy()
    action = policy.decide(engine, tracking=tracking)
    assert action.kind is SimActionKind.CONSUME


def test_bail_policy_seeks_stairs_over_runes() -> None:
    engine = GameEngine(save_coordinator=None, skip_new_game=True)
    engine.new_game(seed=8, log_session_milestones=False)
    stairs = stairs_positions(engine.game_map)
    assert stairs
    sx, sy = stairs[0]
    carve_floor_rect(engine, sx - 2, sy, sx + 2, sy)
    relocate_player(engine, sx - 1, sy)
    engine.game_map.tiles[sy, sx] = Tile.STAIRS_DOWN
    engine._update_fov()

    tracking = FloorTrackingState()
    tracking.begin_floor(floor=1, seed=8, runes_collected=0)
    visit = tracking.visit
    assert visit is not None
    visit.bail_for_survival = True

    policy = SimPolicy()
    action = policy.decide(engine, tracking=tracking)
    assert action.kind in (SimActionKind.MOVE, SimActionKind.DESCEND)


def test_trajectory_run_latches_bail_on_pinned_easy_seed() -> None:
    """Integration smoke: PR3 bail on easier seed 4242 (balance-simulator spec)."""
    run = SimTrajectoryRun(
        difficulty_id="easier",
        seed=4242,
        max_turns=8_000,
        floors_max=20,
    )
    result = run.run()
    assert result.depth_reached >= 2, (
        f"expected depth >= 2, got {result.depth_reached} "
        f"(termination={result.termination}, runes={result.runes_collected})"
    )
    assert any(s.bail_for_survival for s in result.floor_snapshots), (
        "expected bail_for_survival on at least one floor snapshot"
    )


def test_rest_imperfection_skips_at_high_hp(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = GameEngine(save_coordinator=None, skip_new_game=True)
    engine.new_game(seed=9, log_session_milestones=False)
    fighter = engine.player.components[Fighter]
    fighter.hp = int(fighter.max_hp * 0.75)

    monkeypatch.setattr(engine.rng, "random", lambda: 0.0)
    assert rest_imperfection_skips(engine)