"""Sim inventory policy (PR3 consumables, PR4 loot/equip)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tcod.ecs import Entity

from src.components import EquipState, Inventory, Item, ItemCategory, Player, Position
from src.data.item_registry import ItemRegistry
from src.sim.perception import is_aquatic_evil
from src.sim.snapshots import LoadoutAtEntry
from src.systems.inventory import (
    item_registry,
    pickup_all_items_at,
    quaff_potion_from_slot,
    slots_for_category,
)
from src.systems.item_modals import InventoryModalState, _wear_from_slot, _wield_from_slot
from src.systems.naming import entity_type_id
from src.systems.wand_evoke import (
    build_evoke_targets,
    confirm_wand_evoke,
    default_evoke_target_index,
    evil_targets_in_range,
    slots_for_wands_with_charges,
    wand_charges,
)

if TYPE_CHECKING:
    from src.engine import GameEngine
    from src.sim.snapshots import FloorVisitTracker

_LETHAL_POTION_EFFECTS = ("heal", "might", "haste")
_ACCURACY_SCALE = 100


def _registry() -> ItemRegistry:
    return item_registry()


def potion_slots_for_effect(
    player: Entity,
    effect: str,
    *,
    registry: ItemRegistry | None = None,
) -> list[tuple[str, int]]:
    """Letter slots with potions matching ``effect``, with stack counts."""
    reg = registry or _registry()
    rows: list[tuple[str, int]] = []
    for letter, instance in slots_for_category(
        player.components[Inventory],
        ItemCategory.POTION,
    ):
        potion = reg.get_potion(instance.item_id)
        if potion.effect == effect:
            rows.append((letter, instance.stack_count))
    return rows


def has_potion_effect(player: Entity, effect: str) -> bool:
    return bool(potion_slots_for_effect(player, effect))


def policy_lethal_consumables_available(player: Entity) -> bool:
    """Heal, might, haste potions, or a charged wand (bail lethal-risk set)."""
    if any(has_potion_effect(player, effect) for effect in _LETHAL_POTION_EFFECTS):
        return True
    return bool(slots_for_wands_with_charges(player.components[Inventory]))


def _record_potion_use(visit: FloorVisitTracker | None, effect: str) -> None:
    if visit is None:
        return
    match effect:
        case "heal":
            visit.consumable_heal += 1
        case "might":
            visit.consumable_might += 1
        case "haste":
            visit.consumable_haste += 1
        case "teleport_delay":
            visit.consumable_teleport += 1


def try_quaff_potion_effect(
    engine: GameEngine,
    effect: str,
    *,
    visit: FloorVisitTracker | None,
) -> bool:
    """Quaff first potion matching ``effect``. Returns True if a turn was consumed."""
    player = engine.player
    if player is None:
        return False
    slots = potion_slots_for_effect(player, effect)
    if not slots:
        return False
    slot = slots[0][0]
    if not quaff_potion_from_slot(
        player,
        slot,
        engine.message_log,
        game_map=engine.game_map,
        world=engine.world,
        floor_depth=engine.floor_depth,
        difficulty_id=engine.difficulty_id,
        rng=engine.rng,
        vore_prefs=engine.vore_content_prefs,
    ):
        return False
    _record_potion_use(visit, effect)
    return True


def try_evoke_wand_non_shark(
    engine: GameEngine,
    *,
    visit: FloorVisitTracker | None,
) -> bool:
    """Evoke nearest non-shark evil in range. Returns True if a turn was consumed."""
    player = engine.player
    if player is None:
        return False
    inventory = player.components[Inventory]
    wand_rows = slots_for_wands_with_charges(inventory)
    if not wand_rows:
        return False
    wand_slot, instance = wand_rows[0]
    reg = _registry()
    wand = reg.get_wand(instance.item_id)
    targets = build_evoke_targets(
        engine.world,
        engine.game_map,
        player,
        wand.range,
    )
    evils = evil_targets_in_range(targets, player)
    non_shark = [
        entity
        for entity in evils
        if entity_type_id(entity) != "shark" and not is_aquatic_evil(entity)
    ]
    if not non_shark:
        non_shark = [entity for entity in evils if entity_type_id(entity) != "shark"]
    if not non_shark:
        return False
    index = default_evoke_target_index(non_shark, player)
    target = non_shark[index]
    if not confirm_wand_evoke(
        engine.world,
        engine.game_map,
        player,
        wand_slot,
        target,
        engine.message_log,
        rng=engine.rng,
        run_stats=engine.run_stats,
    ):
        return False
    if visit is not None:
        visit.wand_evokes += 1
    return True


def try_stunned_recovery(
    engine: GameEngine,
    *,
    visit: FloorVisitTracker | None,
) -> bool:
    """Heal potion, else teleport delay potion. Returns True if a turn was consumed."""
    if try_quaff_potion_effect(engine, "heal", visit=visit):
        return True
    return try_quaff_potion_effect(engine, "teleport_delay", visit=visit)


def try_lethal_risk_consumable(
    engine: GameEngine,
    *,
    visit: FloorVisitTracker | None,
) -> bool:
    """Heal → wand (non-shark) → might → haste. Returns True if a turn was consumed."""
    if try_quaff_potion_effect(engine, "heal", visit=visit):
        return True
    if try_evoke_wand_non_shark(engine, visit=visit):
        return True
    if try_quaff_potion_effect(engine, "might", visit=visit):
        return True
    return try_quaff_potion_effect(engine, "haste", visit=visit)


def _weapon_stats(
    item_id: str,
    registry: ItemRegistry,
) -> tuple[int, int]:
    weapon = registry.get_weapon(item_id)
    return (
        weapon.min_damage + weapon.max_damage,
        int(round(weapon.accuracy_bonus * _ACCURACY_SCALE)),
    )


def weapon_strictly_better_than(
    candidate_id: str,
    current_id: str | None,
    *,
    registry: ItemRegistry | None = None,
) -> bool:
    """Higher (min+max) damage; tiebreak accuracy_bonus."""
    reg = registry or _registry()
    c_sum, c_acc = _weapon_stats(candidate_id, reg)
    if current_id is None:
        return True
    cur_sum, cur_acc = _weapon_stats(current_id, reg)
    if c_sum > cur_sum:
        return True
    if c_sum < cur_sum:
        return False
    return c_acc > cur_acc


def weapon_strictly_better_than_entry(
    candidate_id: str,
    entry: LoadoutAtEntry,
    *,
    registry: ItemRegistry | None = None,
) -> bool:
    reg = registry or _registry()
    c_sum, c_acc = _weapon_stats(candidate_id, reg)
    if c_sum > entry.weapon_damage_sum:
        return True
    if c_sum < entry.weapon_damage_sum:
        return False
    return c_acc > entry.weapon_accuracy


def armor_strictly_better_than(
    candidate_id: str,
    current_id: str | None,
    *,
    registry: ItemRegistry | None = None,
) -> bool:
    reg = registry or _registry()
    candidate_ac = reg.get_armor(candidate_id).ac_bonus
    if current_id is None:
        return True
    return candidate_ac > reg.get_armor(current_id).ac_bonus


def armor_strictly_better_than_entry(
    candidate_id: str,
    entry: LoadoutAtEntry,
    *,
    registry: ItemRegistry | None = None,
) -> bool:
    reg = registry or _registry()
    return reg.get_armor(candidate_id).ac_bonus > entry.armor_ac


def current_wielded_weapon_id(player: Entity) -> str | None:
    equip = player.components.get(EquipState)
    if equip is None or equip.wielded_slot is None:
        return None
    instance = player.components[Inventory].slots.get(equip.wielded_slot)
    if instance is None or instance.category != ItemCategory.WEAPON:
        return None
    return instance.item_id


def current_worn_armor_id(player: Entity) -> str | None:
    equip = player.components.get(EquipState)
    if equip is None or equip.worn_slot is None:
        return None
    instance = player.components[Inventory].slots.get(equip.worn_slot)
    if instance is None or instance.category != ItemCategory.ARMOR:
        return None
    return instance.item_id


def capture_loadout_at_entry(player: Entity) -> LoadoutAtEntry:
    """Snapshot wielded/worn stats and consumable tallies at floor entry."""
    reg = _registry()
    inventory = player.components[Inventory]
    entry = LoadoutAtEntry()

    weapon_id = current_wielded_weapon_id(player)
    if weapon_id is not None:
        damage_sum, accuracy = _weapon_stats(weapon_id, reg)
        entry.weapon_damage_sum = damage_sum
        entry.weapon_accuracy = accuracy

    armor_id = current_worn_armor_id(player)
    if armor_id is not None:
        entry.armor_ac = reg.get_armor(armor_id).ac_bonus

    for _slot, instance in slots_for_category(inventory, ItemCategory.POTION):
        potion = reg.get_potion(instance.item_id)
        count = instance.stack_count
        match potion.effect:
            case "heal":
                entry.heal_potions += count
            case "might":
                entry.might_potions += count
            case "haste":
                entry.haste_potions += count
            case "teleport_delay":
                entry.teleport_potions += count

    for _slot, instance in slots_for_category(inventory, ItemCategory.WAND):
        wand = reg.get_wand(instance.item_id)
        entry.wand_charges += wand_charges(instance, wand)

    return entry


def loadout_weapon_improved(entry: LoadoutAtEntry, exit_entry: LoadoutAtEntry) -> bool:
    if exit_entry.weapon_damage_sum > entry.weapon_damage_sum:
        return True
    if exit_entry.weapon_damage_sum < entry.weapon_damage_sum:
        return False
    return exit_entry.weapon_accuracy > entry.weapon_accuracy


def loadout_armor_improved(entry: LoadoutAtEntry, exit_entry: LoadoutAtEntry) -> bool:
    return exit_entry.armor_ac > entry.armor_ac


def note_visible_upgrade_spawns(
    engine: GameEngine,
    visit: FloorVisitTracker | None,
) -> None:
    """Latch spawn flags when a strictly-better upgrade is visible on the floor."""
    if visit is None:
        return
    reg = _registry()
    entry = visit.entry
    for entity in engine.world.Q.all_of(components=[Item, Position]):
        item = entity.components[Item]
        if item.category not in (ItemCategory.WEAPON, ItemCategory.ARMOR):
            continue
        pos = entity.components[Position]
        if not engine.game_map.visible[pos.y, pos.x]:
            continue
        if item.category is ItemCategory.WEAPON:
            if weapon_strictly_better_than_entry(
                item.item_id,
                entry,
                registry=reg,
            ):
                visit.upgrade_weapon_spawned = True
        elif armor_strictly_better_than_entry(item.item_id, entry, registry=reg):
            visit.upgrade_armor_spawned = True


def try_equip_strictly_better(
    engine: GameEngine,
    *,
    visit: FloorVisitTracker | None,
) -> bool:
    """Wield/wear inventory items strictly better than current gear."""
    player = engine.player
    if player is None:
        return False

    reg = _registry()
    inventory = player.components[Inventory]
    modal = InventoryModalState()
    equipped = False

    current_weapon = current_wielded_weapon_id(player)
    best_weapon: tuple[str, str] | None = None
    for slot, instance in slots_for_category(inventory, ItemCategory.WEAPON):
        if not weapon_strictly_better_than(
            instance.item_id,
            current_weapon,
            registry=reg,
        ):
            continue
        if best_weapon is None or weapon_strictly_better_than(
            instance.item_id,
            best_weapon[1],
            registry=reg,
        ):
            best_weapon = (slot, instance.item_id)

    if best_weapon is not None:
        slot, item_id = best_weapon
        if _wield_from_slot(player, slot, engine.message_log, modal):
            equipped = True
            if visit is not None and weapon_strictly_better_than_entry(
                item_id,
                visit.entry,
                registry=reg,
            ):
                visit.upgrade_weapon_taken = True

    current_armor = current_worn_armor_id(player)
    best_armor: tuple[str, str] | None = None
    for slot, instance in slots_for_category(inventory, ItemCategory.ARMOR):
        if not armor_strictly_better_than(instance.item_id, current_armor, registry=reg):
            continue
        if best_armor is None or armor_strictly_better_than(
            instance.item_id,
            best_armor[1],
            registry=reg,
        ):
            best_armor = (slot, instance.item_id)

    if best_armor is not None:
        slot, item_id = best_armor
        if _wear_from_slot(player, slot, engine.message_log, modal):
            equipped = True
            if visit is not None and armor_strictly_better_than_entry(
                item_id,
                visit.entry,
                registry=reg,
            ):
                visit.upgrade_armor_taken = True

    return equipped


def pickup_and_equip_at_player_tile(
    engine: GameEngine,
    *,
    visit: FloorVisitTracker | None,
) -> None:
    """Auto-pickup policy loot on the player tile, then equip strictly-better gear."""
    player = engine.player
    if player is None:
        return
    pos = player.components.get(Position)
    if pos is None:
        return

    pickup_all_items_at(
        engine.world,
        player,
        pos.x,
        pos.y,
        engine.message_log,
    )
    try_equip_strictly_better(engine, visit=visit)