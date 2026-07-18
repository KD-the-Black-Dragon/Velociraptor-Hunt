"""Build inventory and rune progression for depth-jump starts."""

from __future__ import annotations

import math
import random
import string
from typing import TYPE_CHECKING

from tcod.ecs import Entity

from src.components import EquipState, Fighter, Inventory, ItemCategory, Player
from src.data.depth_jump_start_loader import DepthJumpStartConfig, default_depth_jump_start_config
from src.data.floor_rune_registry import FloorRuneDefinition, FloorRuneRegistry
from src.data.item_registry import (
    ArmorDefinition,
    ItemRegistry,
    PotionDefinition,
    ThrowableDefinition,
    WandDefinition,
    WeaponDefinition,
)
from src.items.strength import pick_strongest, pick_strongest_armor, weapon_strength_key
from src.systems.floor_runes import apply_rune_effect
from src.systems.inventory import (
    STARTER_ARMOR_SLOT,
    STARTER_THROWABLE_SLOT,
    STARTER_WEAPON_SLOT,
    make_armor_instance,
    make_potion_instance,
    make_throwable_instance,
    make_wand_instance,
    make_weapon_instance,
)

if TYPE_CHECKING:
    from src.run_stats import RunStats


def _spawn_eligible(
    item: WeaponDefinition | ArmorDefinition | PotionDefinition | WandDefinition | ThrowableDefinition,
    *,
    floor_depth: int,
) -> bool:
    return (
        item.spawn.weight > 0
        and item.spawn.min_depth <= floor_depth <= item.spawn.max_depth
    )


def eligible_weapons(registry: ItemRegistry, floor_depth: int) -> list[WeaponDefinition]:
    return [weapon for weapon in registry.weapons if _spawn_eligible(weapon, floor_depth=floor_depth)]


def eligible_armor(registry: ItemRegistry, floor_depth: int) -> list[ArmorDefinition]:
    return [piece for piece in registry.armor if _spawn_eligible(piece, floor_depth=floor_depth)]


def eligible_potions(registry: ItemRegistry, floor_depth: int) -> list[PotionDefinition]:
    return [potion for potion in registry.potions if _spawn_eligible(potion, floor_depth=floor_depth)]


def eligible_wands(registry: ItemRegistry, floor_depth: int) -> list[WandDefinition]:
    return [wand for wand in registry.wands if _spawn_eligible(wand, floor_depth=floor_depth)]


def eligible_throwables(registry: ItemRegistry, floor_depth: int) -> list[ThrowableDefinition]:
    return [
        throwable
        for throwable in registry.throwables
        if _spawn_eligible(throwable, floor_depth=floor_depth)
    ]


def _weighted_choice(
    items: list[FloorRuneDefinition],
    *,
    rng: random.Random,
) -> FloorRuneDefinition:
    weights = [max(0, int(item.weight)) for item in items]
    if not items or sum(weights) == 0:
        raise ValueError("weighted choice requires positive total weight")
    return rng.choices(items, weights=weights, k=1)[0]


def _weighted_item_choice(
    items: list[PotionDefinition] | list[WandDefinition],
    *,
    rng: random.Random,
) -> str:
    weights = [max(0, int(item.spawn.weight)) for item in items]
    if not items or sum(weights) == 0:
        raise ValueError("weighted choice requires positive total weight")
    picked = rng.choices(items, weights=weights, k=1)[0]
    return picked.id


def _first_empty_slots(inventory: Inventory, count: int) -> list[str]:
    letters: list[str] = []
    for letter in string.ascii_lowercase:
        if inventory.slots.get(letter) is None:
            letters.append(letter)
            if len(letters) >= count:
                break
    return letters


def simulated_runes_for_floor(
    *,
    runes_per_floor: int,
    config: DepthJumpStartConfig,
    rng: random.Random,
) -> int:
    """How many runes to simulate collecting on one prior floor."""
    base = max(0, int(runes_per_floor))
    if base == 0:
        return 0
    low = math.ceil(
        base * config.simulated_runes_min_numerator / config.simulated_runes_min_denominator
    )
    low = max(0, min(low, base))
    return rng.randint(low, base)


def apply_depth_jump_loadout(
    player: Entity,
    *,
    target_depth: int,
    rng: random.Random,
    registry: ItemRegistry,
    rune_registry: FloorRuneRegistry,
    runes_per_floor: int,
    rune_pieces_multiplier: int,
    run_stats: RunStats | None = None,
    config: DepthJumpStartConfig | None = None,
) -> int:
    """Replace starter gear with synthesized mid-run loadout. Returns simulated rune count."""
    if Player not in player.tags or target_depth < 2:
        return 0

    cfg = config if config is not None else default_depth_jump_start_config()
    loot_depth = target_depth - 1
    inventory = player.components[Inventory]
    equip = player.components.setdefault(EquipState, EquipState())
    inventory.slots.clear()

    weapons = eligible_weapons(registry, loot_depth)
    strongest_weapon = pick_strongest(weapons, key=weapon_strength_key, rng=rng)
    if strongest_weapon is not None:
        inventory.slots[STARTER_WEAPON_SLOT] = make_weapon_instance(strongest_weapon.id)
        equip.wielded_slot = STARTER_WEAPON_SLOT
    else:
        equip.wielded_slot = None

    armor_pool = eligible_armor(registry, loot_depth)
    strongest_armor = pick_strongest_armor(armor_pool, rng=rng)
    if strongest_armor is not None:
        inventory.slots[STARTER_ARMOR_SLOT] = make_armor_instance(strongest_armor.id)
        equip.worn_slot = STARTER_ARMOR_SLOT
    else:
        equip.worn_slot = None

    throwables = eligible_throwables(registry, loot_depth)
    strongest_throwable = pick_strongest(throwables, key=weapon_strength_key, rng=rng)
    if strongest_throwable is not None and cfg.throwable_stack_count > 0:
        inventory.slots[STARTER_THROWABLE_SLOT] = make_throwable_instance(
            strongest_throwable.id,
            stack_count=cfg.throwable_stack_count,
        )

    potion_pool = eligible_potions(registry, loot_depth)
    wand_pool = eligible_wands(registry, loot_depth)
    extra_slots = _first_empty_slots(
        inventory,
        cfg.potion_count + cfg.wand_count,
    )
    slot_index = 0
    for _ in range(cfg.potion_count):
        if not potion_pool or slot_index >= len(extra_slots):
            break
        inventory.slots[extra_slots[slot_index]] = make_potion_instance(
            _weighted_item_choice(potion_pool, rng=rng),
        )
        slot_index += 1
    for _ in range(cfg.wand_count):
        if not wand_pool or slot_index >= len(extra_slots):
            break
        inventory.slots[extra_slots[slot_index]] = make_wand_instance(
            _weighted_item_choice(wand_pool, rng=rng),
        )
        slot_index += 1

    simulated = 0
    for floor in range(1, loot_depth + 1):
        eligible = [
            rune
            for rune in rune_registry.runes
            if rune.weight > 0 and rune.min_depth <= floor <= rune.max_depth
        ]
        if not eligible:
            continue
        count = simulated_runes_for_floor(
            runes_per_floor=runes_per_floor,
            config=cfg,
            rng=rng,
        )
        for _ in range(count):
            definition = _weighted_choice(eligible, rng=rng)
            apply_rune_effect(
                player,
                definition.effect,
                rune_pieces_multiplier=rune_pieces_multiplier,
            )
            simulated += 1
            if run_stats is not None:
                run_stats.record_rune_collected()

    fighter = player.components.get(Fighter)
    if fighter is not None:
        fighter.hp = fighter.max_hp

    return simulated