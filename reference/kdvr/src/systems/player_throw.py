"""Player Path-targeted throwable attacks."""

from __future__ import annotations

import random
from typing import Final

from tcod.ecs import Entity, Registry
from tcod.event import KeySym

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
    Stunned,
    VoreMercy,
)
from src.constants import PLAYER_ACCURACY
from src.data.item_registry import ItemRegistry, ThrowableDefinition
from src.map_gen import GameMap
from src.message_log import MessageCategory, MessageLog
from src.run_stats import RunStats
from src.systems.combat import resolve_attack
from src.systems.fov import can_see
from src.systems.inventory import item_registry
from src.systems.naming import entity_log_name
from src.systems.projectile_anim import maybe_queue_player_path_projectile
from src.systems.ranged_path import PathShotStatus, fighters_on_tile, resolve_path_shot
from src.systems.wand_evoke import chebyshev_distance

_INVENTORY_SLOT_ORDER = "abcdefghijklmnopqrstuvwxyz"

# West-facing movement keys cycle throw targets backward (numpad4 wraps to farthest).
THROW_TARGET_BACK_KEYS: Final[frozenset[KeySym]] = frozenset({
    KeySym.LEFT,
    KeySym.KP_4,
    KeySym.G,
})


def slots_for_throwables_with_stack(
    inventory: Inventory,
) -> list[tuple[str, InventoryItemInstance]]:
    from src.systems.inventory import slots_for_category

    rows: list[tuple[str, InventoryItemInstance]] = []
    for letter, instance in slots_for_category(inventory, ItemCategory.THROWABLE):
        if instance.stack_count > 0:
            rows.append((letter, instance))
    return rows


def pick_best_throwable_slot(
    inventory: Inventory,
    *,
    registry: ItemRegistry | None = None,
) -> str | None:
    """Highest max_damage, then min_damage, then earliest slot letter."""
    reg = registry or item_registry()
    best_slot: str | None = None
    best_key: tuple[int, int, int] | None = None
    for letter, instance in slots_for_throwables_with_stack(inventory):
        throwable = reg.get_throwable(instance.item_id)
        key = (
            throwable.max_damage,
            throwable.min_damage,
            -_INVENTORY_SLOT_ORDER.index(letter),
        )
        if best_key is None or key > best_key:
            best_key = key
            best_slot = letter
    return best_slot


def fighter_from_throwable(throwable: ThrowableDefinition) -> Fighter:
    return Fighter(
        hp=1,
        max_hp=1,
        accuracy=PLAYER_ACCURACY + throwable.accuracy_bonus,
        evade=0,
        ac=0,
        min_damage=throwable.min_damage,
        max_damage=throwable.max_damage,
    )


def is_valid_throw_target(target: Entity, player: Entity) -> bool:
    """Only evil NPCs may be struck by a throw."""
    if target is player:
        return False
    alignment = target.components.get(NPCAlignment)
    return alignment is not None and alignment.alignment == Alignment.EVIL


def build_throw_target_tiles(
    world: Registry,
    game_map: GameMap,
    player: Entity,
) -> list[Position]:
    """Visible valid throw targets sorted near-to-far (Chebyshev)."""
    player_pos = player.components[Position]
    rows: list[tuple[int, int, int, Position]] = []
    seen_tiles: set[tuple[int, int]] = set()
    for entity in world.Q.all_of(components=[Position, Fighter, NPCAlignment]):
        if not is_valid_throw_target(entity, player):
            continue
        if Engulfed in entity.tags or VoreMercy in entity.tags:
            continue
        pos = entity.components[Position]
        if not can_see(game_map, player_pos.x, player_pos.y, pos.x, pos.y):
            continue
        tile = (pos.x, pos.y)
        if tile in seen_tiles:
            continue
        seen_tiles.add(tile)
        distance = chebyshev_distance(player_pos.x, player_pos.y, pos.x, pos.y)
        rows.append((distance, pos.y, pos.x, pos))
    rows.sort(key=lambda row: (row[0], row[1], row[2]))
    return [pos for _, _, _, pos in rows]


def any_evil_throw_target_in_los(
    world: Registry,
    game_map: GameMap,
    player: Entity,
) -> bool:
    player_pos = player.components[Position]
    for entity in world.Q.all_of(components=[Position, Fighter, NPCAlignment]):
        if not is_valid_throw_target(entity, player):
            continue
        if Engulfed in entity.tags or VoreMercy in entity.tags:
            continue
        pos = entity.components[Position]
        if can_see(game_map, player_pos.x, player_pos.y, pos.x, pos.y):
            return True
    return False


def default_throw_target_index(tiles: list[Position]) -> int:
    """Nearest target — index 0 after near-to-far sort."""
    return 0


def throw_target_position(
    tiles: list[Position],
    index: int,
) -> Position | None:
    if not tiles or index < 0 or index >= len(tiles):
        return None
    return tiles[index]


def cycle_throw_target_index(current: int, target_count: int, *, forward: bool) -> int:
    """Cycle near-to-far; left from index 0 wraps to farthest."""
    if target_count <= 0:
        return 0
    if forward:
        return (current + 1) % target_count
    return (current - 1) % target_count


def _consume_throwable_stack(
    inventory: Inventory,
    slot: str,
    message_log: MessageLog,
    *,
    registry: ItemRegistry,
) -> None:
    instance = inventory.slots.get(slot)
    if instance is None:
        return
    instance.stack_count -= 1
    if instance.stack_count <= 0:
        display = registry.display_name_for(instance.item_id, instance.category)
        inventory.slots[slot] = None
        message_log.add(
            messages.throwable_stack_empty(display),
            category=MessageCategory.CAUTION,
        )


def confirm_player_throw(
    world: Registry,
    game_map: GameMap,
    player: Entity,
    throwable_slot: str,
    target_tile: Position,
    message_log: MessageLog,
    *,
    registry: ItemRegistry | None = None,
    rng: random.Random | None = None,
    run_stats: RunStats | None = None,
) -> bool:
    """
    Resolve a Path throw toward ``target_tile``.
    Returns True when the throw was fired (hit or miss) and the turn should advance.
    """
    if Player not in player.tags:
        return False

    inventory = player.components[Inventory]
    instance = inventory.slots.get(throwable_slot)
    if instance is None or instance.category != ItemCategory.THROWABLE:
        return False
    if instance.stack_count <= 0:
        return False

    reg = registry or item_registry()
    throwable = reg.get_throwable(instance.item_id)
    attack_rng = rng or random.Random()

    occupants = fighters_on_tile(world, target_tile.x, target_tile.y)
    if not occupants:
        message_log.add(messages.throw_no_target_there())
        return False

    intended = occupants[0]
    if not is_valid_throw_target(intended, player):
        message_log.add(messages.not_the_best_target())
        return False

    shot = resolve_path_shot(world, game_map, player, intended)
    if shot.status is PathShotStatus.BLOCKED:
        message_log.add(messages.throw_path_blocked())
        return False
    if shot.status is not PathShotStatus.HIT or shot.defender is None:
        message_log.add(messages.throw_no_target_there())
        return False

    defender = shot.defender
    if VoreMercy in defender.tags or Engulfed in defender.tags:
        message_log.add(messages.throw_no_target_there())
        return False

    defender_stats = defender.components[Fighter]
    hit, damage = resolve_attack(
        fighter_from_throwable(throwable),
        defender_stats,
        attack_rng,
    )

    target = entity_log_name(defender)
    if not hit:
        message_log.add(messages.player_throw_misses_target(target))
    elif damage > 0:
        message_log.add(messages.actor_hits_target("You", target, damage))
    else:
        message_log.add(messages.actor_hits_target_no_damage("You", target))

    maybe_queue_player_path_projectile(player, defender, game_map)
    _consume_throwable_stack(inventory, throwable_slot, message_log, registry=reg)

    if hit and damage > 0:
        attacker_pos = player.components[Position]
        defender_pos = defender.components[Position]
        attack_vector = (
            defender_pos.x - attacker_pos.x,
            defender_pos.y - attacker_pos.y,
        )
        from src.systems.abilities import try_apply_knockback

        try_apply_knockback(
            player,
            defender,
            world,
            game_map,
            message_log,
            attack_vector,
        )

    if not hit or damage <= 0:
        return True

    defender_stats.hp -= damage
    from src.events import fire_entity_defeated, fire_player_combat_targeted

    fire_player_combat_targeted()

    if defender_stats.hp <= 0:
        defender_stats.hp = 0
        alignment = defender.components.get(NPCAlignment)
        if alignment in (Alignment.GOOD, Alignment.NEUTRAL):
            if Stunned not in defender.tags:
                defender.tags.add(Stunned)
        else:
            from src.systems.vore import release_prey_if_defeated_predator

            release_prey_if_defeated_predator(
                world,
                defender,
                game_map,
                message_log,
                rng=attack_rng,
                rescuer=player,
            )
            from src.systems.fov import entity_visible_to_player

            if entity_visible_to_player(game_map, defender):
                defeated = entity_log_name(defender, sentence_start=True)
                message_log.add(messages.target_defeated(defeated))
            fire_entity_defeated(defender)
            if run_stats is not None:
                run_stats.record_monster_defeated(defeated_entity=defender)
            defender.clear()

    return True