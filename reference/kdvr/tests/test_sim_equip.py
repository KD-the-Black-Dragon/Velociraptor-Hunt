"""PR4 tests for sim loot pickup, equip compare, upgrade tracking."""

from __future__ import annotations

import pytest

from src.components import EquipState, Inventory, ItemCategory, Position
from src.engine import GameEngine
from src.sim.inventory_policy import (
    armor_strictly_better_than,
    armor_strictly_better_than_entry,
    capture_loadout_at_entry,
    current_wielded_weapon_id,
    note_visible_upgrade_spawns,
    pickup_and_equip_at_player_tile,
    try_equip_strictly_better,
    weapon_strictly_better_than,
    weapon_strictly_better_than_entry,
)
from src.sim.policy import SimActionKind, SimPolicy
from src.sim.snapshots import FloorTrackingState
from src.spawn import spawn_item_entity
from src.systems.inventory import make_weapon_instance
from tests.map_test_helpers import carve_floor_rect, isolate_other_ais, relocate_player


@pytest.fixture(scope="module", autouse=True)
def _stock_data() -> None:
    from src.sim.data_loader import install_stock_game_data

    install_stock_game_data()


def test_weapon_strictly_better_damage_sum() -> None:
    assert weapon_strictly_better_than("club", "dagger")
    assert not weapon_strictly_better_than("dagger", "club")


def test_armor_strictly_better_ac_bonus() -> None:
    assert armor_strictly_better_than("leather_armor", "robes")
    assert not armor_strictly_better_than("robes", "leather_armor")


def test_weapon_strictly_better_than_entry_uses_floor_entry_stats() -> None:
    engine = GameEngine(save_coordinator=None, skip_new_game=True)
    engine.new_game(seed=10, log_session_milestones=False)
    player = engine.player
    assert player is not None
    entry = capture_loadout_at_entry(player)
    assert entry.weapon_damage_sum == 8  # starter dagger 3+5
    assert weapon_strictly_better_than_entry("club", entry)
    assert not weapon_strictly_better_than_entry("dagger", entry)


def test_armor_strictly_better_than_entry() -> None:
    engine = GameEngine(save_coordinator=None, skip_new_game=True)
    engine.new_game(seed=11, log_session_milestones=False)
    player = engine.player
    assert player is not None
    entry = capture_loadout_at_entry(player)
    assert entry.armor_ac == 1  # robes
    assert armor_strictly_better_than_entry("leather_armor", entry)


def test_pickup_and_equip_wields_strictly_better_weapon() -> None:
    engine = GameEngine(save_coordinator=None, skip_new_game=True)
    engine.new_game(seed=12, log_session_milestones=False)
    carve_floor_rect(engine, 38, 20, 48, 24)
    relocate_player(engine, 40, 22)
    spawn_item_entity(engine.world, ItemCategory.WEAPON, "club", 40, 22)
    isolate_other_ais(engine)
    engine._update_fov()

    pickup_and_equip_at_player_tile(engine, visit=None)
    player = engine.player
    assert player is not None
    assert current_wielded_weapon_id(player) == "club"


def test_note_visible_upgrade_spawns_weapon_flag() -> None:
    engine = GameEngine(save_coordinator=None, skip_new_game=True)
    engine.new_game(seed=13, log_session_milestones=False)
    carve_floor_rect(engine, 38, 20, 48, 24)
    relocate_player(engine, 40, 22)
    spawn_item_entity(engine.world, ItemCategory.WEAPON, "club", 44, 22)
    isolate_other_ais(engine)
    engine._update_fov()

    tracking = FloorTrackingState()
    tracking.begin_floor(
        floor=1,
        seed=13,
        runes_collected=0,
        player=engine.player,
    )
    visit = tracking.visit
    assert visit is not None
    note_visible_upgrade_spawns(engine, visit)
    assert visit.upgrade_weapon_spawned
    assert not visit.upgrade_weapon_taken


def test_try_equip_sets_upgrade_taken_flag() -> None:
    engine = GameEngine(save_coordinator=None, skip_new_game=True)
    engine.new_game(seed=14, log_session_milestones=False)
    player = engine.player
    assert player is not None
    inventory = player.components[Inventory]
    inventory.slots["d"] = make_weapon_instance("club")

    tracking = FloorTrackingState()
    tracking.begin_floor(
        floor=1,
        seed=14,
        runes_collected=0,
        player=player,
    )
    visit = tracking.visit
    assert visit is not None
    assert try_equip_strictly_better(engine, visit=visit)
    assert visit.upgrade_weapon_taken
    assert current_wielded_weapon_id(player) == "club"


def test_policy_moves_toward_visible_loot() -> None:
    engine = GameEngine(save_coordinator=None, skip_new_game=True)
    engine.new_game(seed=15, log_session_milestones=False)
    carve_floor_rect(engine, 38, 20, 50, 24)
    relocate_player(engine, 40, 22)
    spawn_item_entity(engine.world, ItemCategory.POTION, "healing_potion", 44, 22)
    isolate_other_ais(engine)
    engine._update_fov()

    tracking = FloorTrackingState()
    tracking.begin_floor(
        floor=1,
        seed=15,
        runes_collected=0,
        player=engine.player,
    )
    policy = SimPolicy()
    action = policy.decide(engine, tracking=tracking)
    assert action.kind is SimActionKind.MOVE
    assert action.direction[0] > 0  # healing potion east at (44, 22)


def test_snapshot_records_weapon_improved_after_equip() -> None:
    engine = GameEngine(save_coordinator=None, skip_new_game=True)
    engine.new_game(seed=16, log_session_milestones=False)
    player = engine.player
    assert player is not None
    inventory = player.components[Inventory]
    inventory.slots["d"] = make_weapon_instance("club")

    tracking = FloorTrackingState()
    tracking.begin_floor(
        floor=1,
        seed=16,
        runes_collected=0,
        player=player,
    )
    try_equip_strictly_better(engine, visit=tracking.visit)
    snapshot = tracking.finish_visit(
        digested=False,
        descended=True,
        runes_collected=0,
        rune_quota=3,
        player=player,
    )
    assert snapshot is not None
    assert snapshot.weapon_improved
    assert snapshot.upgrade_weapon_taken