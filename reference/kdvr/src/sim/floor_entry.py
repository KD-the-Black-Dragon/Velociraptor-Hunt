"""Sim-only isolation floor bootstrap and loadout injection (PR6)."""

from __future__ import annotations

import string
from typing import TYPE_CHECKING

from tcod.ecs import Entity

from src.components import EquipState, Inventory, ItemCategory, Player
from src.data.item_registry import ItemRegistry
from src.sim.snapshots import LoadoutProfile
from src.systems.inventory import (
    item_registry,
    make_armor_instance,
    make_potion_instance,
    make_weapon_instance,
    make_wand_instance,
)

if TYPE_CHECKING:
    from src.engine import GameEngine

_PROFILE_POTION_IDS = {
    "heal": "healing_potion",
    "might": "potion_of_might",
    "haste": "potion_of_haste",
    "teleport": "potion_of_teleportation",
}
_DEFAULT_WAND_ID = "wand_of_magic_missile"


def isolation_seed(base_seed: int, depth: int, run_index: int) -> int:
    """Deterministic per-floor isolation seed."""
    mixed = base_seed ^ (depth * 10_007) ^ (run_index * 1_009_031)
    return mixed & 0x7FFF_FFFF


def _registry() -> ItemRegistry:
    return item_registry()


def _closest_weapon_id(target_damage_sum: int, *, registry: ItemRegistry) -> str:
    best_id = registry.weapons[0].id
    best_diff = 10**9
    for weapon in registry.weapons:
        damage_sum = weapon.min_damage + weapon.max_damage
        diff = abs(damage_sum - target_damage_sum)
        if diff < best_diff:
            best_diff = diff
            best_id = weapon.id
    return best_id


def _closest_armor_id(target_ac: int, *, registry: ItemRegistry) -> str:
    best_id = registry.armor[0].id
    best_diff = 10**9
    for armor in registry.armor:
        diff = abs(armor.ac_bonus - target_ac)
        if diff < best_diff:
            best_diff = diff
            best_id = armor.id
    return best_id


def _first_empty_slot(inventory: Inventory) -> str | None:
    for letter in string.ascii_lowercase:
        if inventory.slots.get(letter) is None:
            return letter
    return None


def apply_loadout_profile(player: Entity, loadout: LoadoutProfile) -> None:
    """Replace starter gear with stock items closest to the loadout profile."""
    if Player not in player.tags:
        return

    reg = _registry()
    inventory = player.components[Inventory]
    equip = player.components.setdefault(EquipState, EquipState())
    inventory.slots = {letter: None for letter in string.ascii_lowercase}

    weapon_id = _closest_weapon_id(loadout.weapon_damage_sum, registry=reg)
    armor_id = _closest_armor_id(loadout.armor_ac, registry=reg)
    inventory.slots["a"] = make_weapon_instance(weapon_id)
    inventory.slots["b"] = make_armor_instance(armor_id)
    equip.wielded_slot = "a"
    equip.worn_slot = "b"

    potion_rows = (
        (_PROFILE_POTION_IDS["heal"], loadout.heal_potions),
        (_PROFILE_POTION_IDS["might"], loadout.might_potions),
        (_PROFILE_POTION_IDS["haste"], loadout.haste_potions),
        (_PROFILE_POTION_IDS["teleport"], loadout.teleport_potions),
    )
    for item_id, count in potion_rows:
        if count <= 0:
            continue
        slot = _first_empty_slot(inventory)
        if slot is None:
            break
        inventory.slots[slot] = make_potion_instance(item_id, stack_count=count)

    if loadout.wand_charges > 0:
        slot = _first_empty_slot(inventory)
        if slot is not None:
            wand = reg.get_wand(_DEFAULT_WAND_ID)
            inventory.slots[slot] = make_wand_instance(
                _DEFAULT_WAND_ID,
                charges=min(loadout.wand_charges, wand.charges_max),
            )


def _reset_engine_session(engine: GameEngine) -> None:
    """Clear modals and run counters for a single-floor isolation sim."""
    engine.vore_modal.reset()
    engine.digestion_modal.reset()
    engine.game_over.reset()
    engine.run_stats.reset()
    engine.skipped_this_phase.clear()
    engine.examine_state.reset()
    engine.dismiss_state.reset()
    engine.ground_pickup_modal.reset()
    engine.inventory_modal.reset()
    engine.macguffin_discovery.reset()
    engine.macguffin_victory_confirm.reset()
    engine.close_door_pending = False
    engine.last_come_here_turn = -1
    engine._end_rest_session()
    engine._end_autoexplore_session()
    engine.message_log.clear()


def start_isolation_floor(
    engine: GameEngine,
    *,
    depth: int,
    seed: int,
    loadout: LoadoutProfile,
    log_session_milestones: bool = False,
) -> None:
    """Bootstrap one isolation floor at ``depth`` with injected loadout."""
    _reset_engine_session(engine)
    engine.initialize_isolation_floor(
        depth=depth,
        seed=seed,
        log_session_milestones=log_session_milestones,
    )
    if engine.player is not None:
        apply_loadout_profile(engine.player, loadout)