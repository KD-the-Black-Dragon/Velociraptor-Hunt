from __future__ import annotations

import random

from tcod.ecs import Entity, Registry

from src.components import (
    AI,
    Alignment,
    Engulfed,
    Fighter,
    NPCAlignment,
    Player,
    Position,
    Predator,
    Stunned,
    VoreMercy,
)
from src import messages
from src.run_stats import RunStats
from src.events import (
    fire_entity_defeated,
    fire_player_combat_targeted,
    fire_player_stunned,
)
from src.map_gen import GameMap, Tile
from src.message_log import MessageCategory, MessageLog
from src.systems.fov import entity_visible_to_player
from src.systems.movement import can_entity_enter_tile, try_move
from src.systems.naming import entity_log_name
from src.systems.ranged_path import PathShotStatus, resolve_path_shot


def _ranged_attacker_stats(attacker: Fighter) -> Fighter:
    return Fighter(
        hp=attacker.hp,
        max_hp=attacker.max_hp,
        accuracy=attacker.effective_ranged_accuracy(),
        evade=attacker.evade,
        ac=attacker.ac,
        min_damage=attacker.effective_ranged_min_damage(),
        max_damage=attacker.effective_ranged_max_damage(),
    )


def resolve_attack(
    attacker: Fighter,
    defender: Fighter,
    rng: random.Random,
) -> tuple[bool, int]:
    """
    Hit check: accuracy - continuous_uniform(0, evade) > 0.
    Damage: uniform_int(min_damage, max_damage) - uniform_int(0, ac), floored at 0.
    """
    if defender.evade > 0:
        evade_roll = rng.uniform(0.0, float(defender.evade))
    else:
        evade_roll = 0.0
    hit_value = float(attacker.accuracy) - evade_roll
    if hit_value <= 0:
        return False, 0

    if attacker.min_damage >= attacker.max_damage:
        raw_damage = attacker.min_damage
    else:
        raw_damage = rng.randint(attacker.min_damage, attacker.max_damage)

    ac_roll = rng.randint(0, defender.ac) if defender.ac > 0 else 0
    return True, max(0, raw_damage - ac_roll)


def _is_swappable_npc(entity: Entity) -> bool:
    alignment = entity.components.get(NPCAlignment)
    if alignment is None:
        return False
    return alignment.alignment in (Alignment.GOOD, Alignment.NEUTRAL)


def can_npc_swap(actor: Entity, defender: Entity) -> bool:
    if Player in defender.tags:
        return False
    actor_alignment = _npc_alignment(actor)
    defender_alignment = _npc_alignment(defender)
    if actor_alignment is None or defender_alignment is None:
        return False
    if actor_alignment == Alignment.EVIL and defender_alignment == Alignment.EVIL:
        return False
    if actor_alignment in (Alignment.GOOD, Alignment.NEUTRAL) and defender_alignment in (
        Alignment.GOOD,
        Alignment.NEUTRAL,
    ):
        return True
    return False


def _swap_positions(first: Entity, second: Entity) -> None:
    first_pos = first.components[Position]
    second_pos = second.components[Position]
    first.components[Position] = second_pos
    second.components[Position] = first_pos


def _fighter_at(world: Registry, x: int, y: int, *, exclude: Entity | None = None) -> Entity | None:
    target = Position(x, y)
    candidates = [
        entity
        for entity in world.Q.all_of(tags=[target], components=[Fighter])
        if entity is not exclude and Engulfed not in entity.tags
    ]
    if not candidates:
        return None
    for entity in candidates:
        if entity.components.get(Predator) is not None:
            return entity
    return candidates[0]


def _notify_npc_took_damage(entity: Entity, amount: int) -> None:
    """Side effects when an NPC takes positive damage (spawn freeze clear, etc.)."""
    if amount <= 0 or Player in entity.tags:
        return
    from src.systems.ai.common import clear_spawn_ai_freeze

    clear_spawn_ai_freeze(entity)


def apply_struggle_damage(predator: Entity, amount: int) -> None:
    """Flat damage to predator during engulfed struggle (PR 6 uses this)."""
    fighter = predator.components.get(Fighter)
    if fighter is None or amount <= 0:
        return
    fighter.hp -= amount
    _notify_npc_took_damage(predator, amount)


def _npc_alignment(entity: Entity) -> Alignment | None:
    alignment = entity.components.get(NPCAlignment)
    if alignment is None:
        return None
    return alignment.alignment


def _is_npc_only_combat(attacker: Entity, defender: Entity) -> bool:
    return Player not in attacker.tags and Player not in defender.tags


def _npc_combat_visible_to_player(
    game_map: GameMap,
    attacker: Entity,
    defender: Entity,
) -> bool:
    """True when at least one combatant is on a tile in the player's current FOV."""
    return entity_visible_to_player(game_map, attacker) or entity_visible_to_player(
        game_map, defender
    )


def sync_stunned_state(entity: Entity) -> None:
    """Keep stunned tag aligned with HP for player and good/neutral NPCs."""
    fighter = entity.components.get(Fighter)
    if fighter is None:
        return
    if Player in entity.tags:
        if fighter.hp > 0:
            entity.tags.discard(Stunned)
        elif fighter.hp <= 0:
            fighter.hp = 0
            entity.tags.add(Stunned)
        return
    alignment = _npc_alignment(entity)
    if alignment not in (Alignment.GOOD, Alignment.NEUTRAL):
        return
    if fighter.hp > 0:
        entity.tags.discard(Stunned)
    elif fighter.hp <= 0:
        fighter.hp = 0
        entity.tags.add(Stunned)


def heal(entity: Entity, amount: int) -> int:
    """Restore HP up to max. Return actual amount healed."""
    fighter = entity.components.get(Fighter)
    if fighter is None or amount <= 0:
        return 0
    before = fighter.hp
    fighter.hp = min(fighter.max_hp, fighter.hp + amount)
    sync_stunned_state(entity)
    return fighter.hp - before


def _perform_attack(
    attacker: Entity,
    defender: Entity,
    message_log: MessageLog,
    *,
    world: Registry,
    game_map: GameMap,
    rng: random.Random,
    attack_vector: tuple[int, int] | None = None,
    run_stats: RunStats | None = None,
) -> None:
    if VoreMercy in defender.tags:
        return
    if Engulfed in defender.tags:
        return

    from src.systems.inventory import degrade_wielded_weapon_on_hit, effective_fighter

    if Player in attacker.tags:
        attacker_fighter = effective_fighter(attacker)
    else:
        attacker_fighter = attacker.components[Fighter]
    defender_stats = defender.components[Fighter]
    if Player in defender.tags:
        defender_fighter = effective_fighter(defender)
    else:
        defender_fighter = defender_stats
    hit, damage = resolve_attack(attacker_fighter, defender_fighter, rng)

    npc_only = _is_npc_only_combat(attacker, defender)
    log_combat = not npc_only or _npc_combat_visible_to_player(
        game_map, attacker, defender
    )

    if Player in attacker.tags:
        target = entity_log_name(defender)
        if not hit:
            message_log.add(messages.actor_misses_target("You", target))
        elif damage > 0:
            message_log.add(messages.actor_hits_target("You", target, damage))
        else:
            message_log.add(messages.actor_hits_target_no_damage("You", target))
    elif Player in defender.tags:
        fire_player_combat_targeted()
        actor = entity_log_name(attacker, sentence_start=True)
        if not hit:
            message_log.add(messages.actor_misses_target(actor, "you"))
        elif damage > 0:
            message_log.add(messages.actor_hits_target(actor, "you", damage))
        else:
            message_log.add(messages.actor_hits_target_no_damage(actor, "you"))
    elif log_combat:
        actor = entity_log_name(attacker, sentence_start=True)
        target = entity_log_name(defender)
        if not hit:
            message_log.add(messages.actor_misses_target(actor, target))
        elif damage > 0:
            message_log.add(messages.actor_hits_target(actor, target, damage))
        else:
            message_log.add(messages.actor_hits_target_no_damage(actor, target))

    if Player in attacker.tags and hit:
        degrade_wielded_weapon_on_hit(attacker, message_log)

    if not hit or damage <= 0:
        return

    defender_stats.hp -= damage
    _notify_npc_took_damage(defender, damage)

    if attack_vector is not None:
        from src.systems.abilities import try_apply_knockback

        try_apply_knockback(
            attacker,
            defender,
            world,
            game_map,
            message_log,
            attack_vector,
        )

    from src.systems.abilities import try_apply_lifedrain

    try_apply_lifedrain(attacker, defender, game_map, message_log, damage)

    if Player in defender.tags:
        if defender_stats.hp <= 0:
            defender_stats.hp = 0
            if Stunned not in defender.tags:
                defender.tags.add(Stunned)
                message_log.add(
                    messages.player_stunned(),
                    category=MessageCategory.DANGER,
                )
                fire_player_stunned(defender)
        return

    if defender_stats.hp <= 0:
        defender_stats.hp = 0
        alignment = _npc_alignment(defender)
        if alignment in (Alignment.GOOD, Alignment.NEUTRAL):
            if Stunned not in defender.tags:
                defender.tags.add(Stunned)
                if log_combat:
                    stunned_name = entity_log_name(defender, sentence_start=True)
                    message_log.add(
                        messages.npc_stunned(stunned_name),
                        category=MessageCategory.DANGER,
                    )
            return

        from src.systems.vore import release_prey_if_defeated_predator

        release_prey_if_defeated_predator(
            world,
            defender,
            game_map,
            message_log,
            rng=rng,
            rescuer=attacker if Player in attacker.tags else None,
        )
        if log_combat:
            defeated = entity_log_name(defender, sentence_start=True)
            message_log.add(messages.target_defeated(defeated))
        fire_entity_defeated(defender)
        if Player in attacker.tags and run_stats is not None:
            run_stats.record_monster_defeated(defeated_entity=defender)
        defender.clear()


def perform_npc_smite_attack(
    attacker: Entity,
    defender: Entity,
    message_log: MessageLog,
    *,
    world: Registry,
    game_map: GameMap,
    rng: random.Random,
) -> None:
    """NPC Smite-targeted attack using ranged_* Fighter stats."""
    if VoreMercy in defender.tags or Engulfed in defender.tags:
        return

    from src.systems.projectile_anim import maybe_queue_smite_projectile

    maybe_queue_smite_projectile(attacker, defender, game_map)

    from src.systems.inventory import effective_fighter

    attacker_fighter = attacker.components[Fighter]
    defender_stats = defender.components[Fighter]
    if Player in defender.tags:
        defender_fighter = effective_fighter(defender)
    else:
        defender_fighter = defender_stats

    hit, damage = resolve_attack(
        _ranged_attacker_stats(attacker_fighter),
        defender_fighter,
        rng,
    )

    if Player in defender.tags:
        fire_player_combat_targeted()

    npc_only = _is_npc_only_combat(attacker, defender)
    log_combat = not npc_only or _npc_combat_visible_to_player(
        game_map, attacker, defender
    )
    if log_combat:
        actor = entity_log_name(attacker, sentence_start=True)
        if Player in defender.tags:
            target = "you"
        else:
            target = entity_log_name(defender)
        if not hit:
            message_log.add(messages.npc_smites_at_target_miss(actor, target))
        elif damage > 0:
            message_log.add(messages.npc_smites_target(actor, target, damage))
        else:
            message_log.add(messages.npc_smites_target_no_damage(actor, target))

    if not hit or damage <= 0:
        return

    defender_stats.hp -= damage
    _notify_npc_took_damage(defender, damage)

    attacker_pos = attacker.components[Position]
    defender_pos = defender.components[Position]
    attack_vector = (defender_pos.x - attacker_pos.x, defender_pos.y - attacker_pos.y)
    from src.systems.abilities import try_apply_knockback

    try_apply_knockback(
        attacker,
        defender,
        world,
        game_map,
        message_log,
        attack_vector,
    )

    from src.systems.abilities import try_apply_lifedrain

    try_apply_lifedrain(attacker, defender, game_map, message_log, damage)

    if Player in defender.tags:
        if defender_stats.hp <= 0:
            defender_stats.hp = 0
            if Stunned not in defender.tags:
                defender.tags.add(Stunned)
                message_log.add(
                    messages.player_stunned(),
                    category=MessageCategory.DANGER,
                )
                fire_player_stunned(defender)
        return

    if defender_stats.hp <= 0:
        defender_stats.hp = 0
        alignment = _npc_alignment(defender)
        if alignment in (Alignment.GOOD, Alignment.NEUTRAL):
            if Stunned not in defender.tags:
                defender.tags.add(Stunned)
                if entity_visible_to_player(game_map, defender):
                    stunned_name = entity_log_name(defender, sentence_start=True)
                    message_log.add(
                        messages.npc_stunned(stunned_name),
                        category=MessageCategory.DANGER,
                    )
            return

        from src.systems.vore import release_prey_if_defeated_predator

        release_prey_if_defeated_predator(
            world,
            defender,
            game_map,
            message_log,
            rng=rng,
            rescuer=None,
        )
        if entity_visible_to_player(game_map, defender):
            defeated = entity_log_name(defender, sentence_start=True)
            message_log.add(messages.target_defeated(defeated))
        fire_entity_defeated(defender)
        defender.clear()


def perform_npc_path_attack(
    attacker: Entity,
    intended: Entity,
    message_log: MessageLog,
    *,
    world: Registry,
    game_map: GameMap,
    rng: random.Random,
) -> bool:
    """
    NPC Path-targeted attack along a Bresenham beam.

    Returns True when a shot was attempted (hit or miss); False when blocked or
    no valid line/target.
    """
    shot = resolve_path_shot(world, game_map, attacker, intended)
    if shot.status is not PathShotStatus.HIT or shot.defender is None:
        return False

    defender = shot.defender
    from src.systems.projectile_anim import maybe_queue_npc_path_projectile

    maybe_queue_npc_path_projectile(attacker, defender, game_map)
    if VoreMercy in defender.tags or Engulfed in defender.tags:
        return False

    from src.systems.inventory import effective_fighter

    attacker_fighter = attacker.components[Fighter]
    defender_stats = defender.components[Fighter]
    if Player in defender.tags:
        defender_fighter = effective_fighter(defender)
    else:
        defender_fighter = defender_stats

    hit, damage = resolve_attack(
        _ranged_attacker_stats(attacker_fighter),
        defender_fighter,
        rng,
    )

    if Player in defender.tags:
        fire_player_combat_targeted()

    npc_only = _is_npc_only_combat(attacker, defender)
    log_combat = not npc_only or _npc_combat_visible_to_player(
        game_map, attacker, defender
    )
    if log_combat:
        actor = entity_log_name(attacker, sentence_start=True)
        if Player in defender.tags:
            target = "you"
        else:
            target = entity_log_name(defender)
        if not hit:
            message_log.add(messages.npc_shoots_at_target_miss(actor, target))
        elif damage > 0:
            message_log.add(messages.npc_shoots_target(actor, target, damage))
        else:
            message_log.add(messages.npc_shoots_target_no_damage(actor, target))

    if not hit or damage <= 0:
        return True

    defender_stats.hp -= damage
    _notify_npc_took_damage(defender, damage)

    attacker_pos = attacker.components[Position]
    defender_pos = defender.components[Position]
    attack_vector = (defender_pos.x - attacker_pos.x, defender_pos.y - attacker_pos.y)
    from src.systems.abilities import try_apply_knockback

    try_apply_knockback(
        attacker,
        defender,
        world,
        game_map,
        message_log,
        attack_vector,
    )

    from src.systems.abilities import try_apply_lifedrain

    try_apply_lifedrain(attacker, defender, game_map, message_log, damage)

    if Player in defender.tags:
        if defender_stats.hp <= 0:
            defender_stats.hp = 0
            if Stunned not in defender.tags:
                defender.tags.add(Stunned)
                message_log.add(
                    messages.player_stunned(),
                    category=MessageCategory.DANGER,
                )
                fire_player_stunned(defender)
        return True

    if defender_stats.hp <= 0:
        defender_stats.hp = 0
        alignment = _npc_alignment(defender)
        if alignment in (Alignment.GOOD, Alignment.NEUTRAL):
            if Stunned not in defender.tags:
                defender.tags.add(Stunned)
                if entity_visible_to_player(game_map, defender):
                    stunned_name = entity_log_name(defender, sentence_start=True)
                    message_log.add(
                        messages.npc_stunned(stunned_name),
                        category=MessageCategory.DANGER,
                    )
            return True

        from src.systems.vore import release_prey_if_defeated_predator

        release_prey_if_defeated_predator(
            world,
            defender,
            game_map,
            message_log,
            rng=rng,
            rescuer=None,
        )
        if entity_visible_to_player(game_map, defender):
            defeated = entity_log_name(defender, sentence_start=True)
            message_log.add(messages.target_defeated(defeated))
        fire_entity_defeated(defender)
        defender.clear()

    return True


def perform_wand_attack(
    player: Entity,
    defender: Entity,
    wand_fighter: Fighter,
    message_log: MessageLog,
    *,
    world: Registry,
    game_map: GameMap,
    rng: random.Random,
    run_stats: RunStats | None = None,
) -> None:
    """Resolve a player wand attack using wand accuracy and damage."""
    if VoreMercy in defender.tags:
        return
    if Engulfed in defender.tags:
        return

    from src.systems.projectile_anim import maybe_queue_smite_projectile

    maybe_queue_smite_projectile(player, defender, game_map)

    from src.systems.inventory import effective_fighter

    defender_stats = defender.components[Fighter]
    if Player in defender.tags:
        defender_fighter = effective_fighter(defender)
    else:
        defender_fighter = defender_stats
    hit, damage = resolve_attack(wand_fighter, defender_fighter, rng)

    if defender is player:
        target = "you"
    else:
        target = entity_log_name(defender)
    if not hit:
        message_log.add(messages.player_smites_at_target_miss(target))
    elif damage > 0:
        message_log.add(messages.player_smites_target(target, damage))
    else:
        message_log.add(messages.player_smites_target_no_damage(target))

    if not hit or damage <= 0:
        return

    defender_stats.hp -= damage
    _notify_npc_took_damage(defender, damage)

    if Player in defender.tags:
        if defender_stats.hp <= 0:
            defender_stats.hp = 0
            if Stunned not in defender.tags:
                defender.tags.add(Stunned)
                message_log.add(
                    messages.player_stunned(),
                    category=MessageCategory.DANGER,
                )
                fire_player_stunned(defender)
        return

    if defender_stats.hp <= 0:
        defender_stats.hp = 0
        alignment = _npc_alignment(defender)
        if alignment in (Alignment.GOOD, Alignment.NEUTRAL):
            if Stunned not in defender.tags:
                defender.tags.add(Stunned)
                if entity_visible_to_player(game_map, defender):
                    stunned_name = entity_log_name(defender, sentence_start=True)
                    message_log.add(
                        messages.npc_stunned(stunned_name),
                        category=MessageCategory.DANGER,
                    )
            return

        from src.systems.vore import release_prey_if_defeated_predator

        release_prey_if_defeated_predator(
            world,
            defender,
            game_map,
            message_log,
            rng=rng,
            rescuer=player,
        )
        if entity_visible_to_player(game_map, defender):
            defeated = entity_log_name(defender, sentence_start=True)
            message_log.add(messages.target_defeated(defeated))
        fire_entity_defeated(defender)
        if run_stats is not None:
            run_stats.record_monster_defeated(defeated_entity=defender)
        defender.clear()


def try_action(
    world: Registry,
    game_map: GameMap,
    actor: Entity,
    direction: tuple[int, int],
    message_log: MessageLog,
    *,
    rng: random.Random | None = None,
    skip_turn_entities: set[Entity] | None = None,
    run_stats: RunStats | None = None,
) -> bool:
    """
    Move, swap with a good/neutral NPC, or bump-attack in a direction.
    Return True when a turn was consumed.
    """
    if Player in actor.tags and Stunned in actor.tags:
        return False

    attack_rng = rng or random.Random()
    origin = actor.components[Position]
    dx, dy = direction
    dest_x = origin.x + dx
    dest_y = origin.y + dy

    if not game_map.in_bounds(dest_x, dest_y):
        return False

    defender = _fighter_at(world, dest_x, dest_y, exclude=actor)
    if (
        Player in actor.tags
        and game_map.tiles[dest_y, dest_x] == Tile.DOOR_CLOSED
    ):
        game_map.tiles[dest_y, dest_x] = Tile.DOOR_OPEN
        message_log.add(messages.door_opened())
        return True

    if game_map.tiles[dest_y, dest_x] == Tile.DOOR_CLOSED:
        from src.systems.movement import try_hands_closed_door

        if try_hands_closed_door(
            world,
            game_map,
            actor,
            direction,
            message_log,
            attack_rng,
        ):
            return True

    if defender is not None:
        if Player in actor.tags and _is_swappable_npc(defender):
            _swap_positions(actor, defender)
            message_log.add(messages.player_swap_places(entity_log_name(defender)))
            if skip_turn_entities is not None:
                skip_turn_entities.add(defender)
            return True
        if Player not in actor.tags and Player in defender.tags:
            if _npc_alignment(actor) != Alignment.EVIL:
                return False
        if Player not in actor.tags and can_npc_swap(actor, defender):
            _swap_positions(actor, defender)
            if skip_turn_entities is not None:
                skip_turn_entities.add(defender)
            return True
        _perform_attack(
            actor,
            defender,
            message_log,
            world=world,
            game_map=game_map,
            rng=attack_rng,
            attack_vector=direction,
            run_stats=run_stats,
        )
        return True

    if not try_move(world, game_map, actor, direction, message_log=message_log):
        if (
            Player in actor.tags
            and game_map.tiles[dest_y, dest_x] == Tile.DEEP_WATER
            and not can_entity_enter_tile(game_map, dest_x, dest_y, actor)
        ):
            message_log.add(messages.cant_enter_deep_water())
        return False
    return True


def try_force_attack(
    world: Registry,
    game_map: GameMap,
    actor: Entity,
    direction: tuple[int, int],
    message_log: MessageLog,
    *,
    rng: random.Random | None = None,
    run_stats: RunStats | None = None,
) -> bool:
    """
    Melee the adjacent tile without moving (Ctrl+direction).
    Return True when a turn was consumed.
    """
    if Player not in actor.tags:
        return False

    if Stunned in actor.tags:
        message_log.add(
            messages.stunned_too_tired_to_move(),
            category=MessageCategory.DANGER,
        )
        return True

    attack_rng = rng or random.Random()
    origin = actor.components[Position]
    dx, dy = direction
    dest_x = origin.x + dx
    dest_y = origin.y + dy

    defender = None
    if game_map.in_bounds(dest_x, dest_y):
        defender = _fighter_at(world, dest_x, dest_y, exclude=actor)

    if defender is not None and _npc_alignment(defender) == Alignment.EVIL:
        _perform_attack(
            actor,
            defender,
            message_log,
            world=world,
            game_map=game_map,
            rng=attack_rng,
            attack_vector=direction,
            run_stats=run_stats,
        )
        return True

    message_log.add(messages.attack_empty_air())
    return True


def defeat_cleanup(world: Registry) -> None:
    """Remove defeated evil monsters that somehow remain at 0 HP."""
    for entity in list(world.Q.all_of(components=[Fighter, AI])):
        if Player in entity.tags:
            continue
        alignment = _npc_alignment(entity)
        if alignment in (Alignment.GOOD, Alignment.NEUTRAL):
            continue
        fighter = entity.components[Fighter]
        if fighter.hp <= 0:
            entity.clear()