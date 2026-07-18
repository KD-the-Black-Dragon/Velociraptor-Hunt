from __future__ import annotations

import random

from tcod.ecs import Entity, Registry

from src import messages
from src.components import (
    Alignment,
    Engulfed,
    Fighter,
    Inventory,
    InventoryItemInstance,
    ItemCategory,
    NPCAlignment,
    Player,
    Position,
)
from src.data.item_registry import ItemRegistry, WandDefinition
from src.map_gen import GameMap
from src.message_log import MessageCategory, MessageLog
from src.run_stats import RunStats
from src.systems.combat import perform_wand_attack
from src.systems.fov import can_see
from src.systems.inventory import item_registry


def chebyshev_distance(ax: int, ay: int, bx: int, by: int) -> int:
    return max(abs(ax - bx), abs(ay - by))


def wand_charges(instance: InventoryItemInstance, wand: WandDefinition) -> int:
    if instance.charges is not None:
        return instance.charges
    return wand.charges_start


def slots_for_wands_with_charges(
    inventory: Inventory,
    *,
    registry: ItemRegistry | None = None,
) -> list[tuple[str, InventoryItemInstance]]:
    reg = registry or item_registry()
    rows: list[tuple[str, InventoryItemInstance]] = []
    for letter, instance in _slots_for_wands(inventory):
        wand = reg.get_wand(instance.item_id)
        if wand_charges(instance, wand) > 0:
            rows.append((letter, instance))
    return rows


def _slots_for_wands(inventory: Inventory) -> list[tuple[str, InventoryItemInstance]]:
    from src.systems.inventory import slots_for_category

    return slots_for_category(inventory, ItemCategory.WAND)


def fighter_from_wand(wand: WandDefinition) -> Fighter:
    return Fighter(
        hp=1,
        max_hp=1,
        accuracy=wand.accuracy,
        evade=0,
        ac=0,
        min_damage=wand.min_damage,
        max_damage=wand.max_damage,
    )


def is_valid_wand_target(target: Entity, player: Entity) -> bool:
    """Only evil NPCs may be struck by a wand."""
    if target is player:
        return False
    alignment = target.components.get(NPCAlignment)
    return alignment is not None and alignment.alignment == Alignment.EVIL


def build_evoke_targets(
    world: Registry,
    game_map: GameMap,
    player: Entity,
    wand_range: int,
) -> list[Entity]:
    """Fighters in wand range with line of sight, plus the player tile."""
    player_pos = player.components[Position]
    targets: list[Entity] = [player]
    seen_tiles: set[tuple[int, int]] = {(player_pos.x, player_pos.y)}

    for entity in world.Q.all_of(components=[Position, Fighter]):
        if entity is player:
            continue
        if Engulfed in entity.tags:
            continue
        pos = entity.components[Position]
        if chebyshev_distance(player_pos.x, player_pos.y, pos.x, pos.y) > wand_range:
            continue
        if not can_see(game_map, player_pos.x, player_pos.y, pos.x, pos.y):
            continue
        tile = (pos.x, pos.y)
        if tile in seen_tiles:
            continue
        targets.append(entity)
        seen_tiles.add(tile)
    return targets


def evil_targets_in_range(targets: list[Entity], player: Entity) -> list[Entity]:
    return [entity for entity in targets if is_valid_wand_target(entity, player)]


def default_evoke_target_index(targets: list[Entity], player: Entity) -> int:
    """Nearest evil NPC by Chebyshev distance."""
    player_pos = player.components[Position]
    best_index: int | None = None
    best_distance: int | None = None
    for index, entity in enumerate(targets):
        if not is_valid_wand_target(entity, player):
            continue
        pos = entity.components[Position]
        distance = chebyshev_distance(player_pos.x, player_pos.y, pos.x, pos.y)
        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_index = index
    if best_index is not None:
        return best_index
    return 0


def cycle_evoke_target_index(current: int, target_count: int) -> int:
    if target_count <= 0:
        return 0
    return (current + 1) % target_count


def evoke_target_position(modal_targets: list[Entity], index: int) -> Position | None:
    if not modal_targets or index < 0 or index >= len(modal_targets):
        return None
    return modal_targets[index].components[Position]


def confirm_wand_evoke(
    world: Registry,
    game_map: GameMap,
    player: Entity,
    wand_slot: str,
    target: Entity,
    message_log: MessageLog,
    *,
    registry: ItemRegistry | None = None,
    rng: random.Random | None = None,
    run_stats: RunStats | None = None,
) -> bool:
    """
    Resolve wand attack against target and spend one charge.
    Returns True when the evoke completed (turn should advance).
    """
    if Player not in player.tags:
        return False
    if not is_valid_wand_target(target, player):
        return False

    inventory = player.components[Inventory]
    instance = inventory.slots.get(wand_slot)
    if instance is None or instance.category != ItemCategory.WAND:
        return False

    reg = registry or item_registry()
    wand = reg.get_wand(instance.item_id)
    if wand.effect != "magic_missile":
        return False

    charges = wand_charges(instance, wand)
    if charges <= 0:
        return False

    display = reg.display_name_for(instance.item_id, instance.category)
    attack_rng = rng or random.Random()
    perform_wand_attack(
        player,
        target,
        fighter_from_wand(wand),
        message_log,
        world=world,
        game_map=game_map,
        rng=attack_rng,
        run_stats=run_stats,
    )

    instance.charges = charges - 1
    if instance.charges <= 0:
        inventory.slots[wand_slot] = None
        message_log.add(
            messages.wand_breaks(display),
            category=MessageCategory.DANGER,
        )
    return True