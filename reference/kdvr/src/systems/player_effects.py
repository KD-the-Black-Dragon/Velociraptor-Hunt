"""Temporary player potion effects: tick, query, apply helpers."""

from __future__ import annotations

import random

from tcod.ecs import Entity, Registry

from src import messages
from src.components import (
    BlocksMovement,
    DigestionStrikes,
    Engulfed,
    Player,
    PlayerEffects,
    Position,
    Predator,
    VoreMercy,
)
from src.events import fire_player_escaped_engulf
from src.log_categories import MessageCategory
from src.map_gen import GameMap
from src.message_log import MessageLog
from src.systems.movement import can_entity_enter_tile, is_blocked_for_mover
from src.systems.naming import entity_log_name


def ensure_player_effects(player: Entity) -> PlayerEffects:
    """Return PlayerEffects on player, creating empty state if missing."""
    effects = player.components.get(PlayerEffects)
    if effects is None:
        effects = PlayerEffects()
        player.components[PlayerEffects] = effects
    return effects


def collect_teleport_destinations(
    player: Entity,
    world: Registry,
    game_map: GameMap,
    *,
    exclude_current: bool = True,
) -> list[Position]:
    """Land-walkable tiles free of blocking NPCs (runes/items/macguffins OK)."""
    origin = player.components.get(Position)
    candidates: list[Position] = []
    for y in range(game_map.height):
        for x in range(game_map.width):
            if exclude_current and origin is not None and origin.x == x and origin.y == y:
                continue
            if not can_entity_enter_tile(game_map, x, y, player):
                continue
            if is_blocked_for_mover(world, x, y, player):
                continue
            candidates.append(Position(x, y))
    if not candidates and exclude_current and origin is not None:
        # Pathological: only current tile is legal.
        if can_entity_enter_tile(game_map, origin.x, origin.y, player):
            if not is_blocked_for_mover(world, origin.x, origin.y, player):
                candidates.append(origin)
    return candidates


def _clear_player_engulfment(
    player: Entity,
    world: Registry,
    message_log: MessageLog | None,
) -> Entity | None:
    """Detach player from predator if engulfed. Returns predator if any."""
    if Engulfed not in player.tags:
        return None
    predator: Entity | None = None
    for entity in world.Q.all_of(components=[Predator]):
        state = entity.components.get(Predator)
        if state is not None and state.prey is player:
            predator = entity
            break
    player.tags.discard(Engulfed)
    player.components.pop(DigestionStrikes, None)
    player.tags.add(BlocksMovement)
    player.tags.add(VoreMercy)
    if predator is not None:
        state = predator.components.get(Predator)
        if state is not None:
            state.failed_struggles = 0
        predator.components.pop(Predator, None)
        if message_log is not None:
            message_log.add(
                messages.vore_escaped(entity_log_name(predator)),
                category=MessageCategory.POSITIVE,
            )
        fire_player_escaped_engulf(player, predator)
    return predator


def fire_delayed_teleport(
    player: Entity,
    world: Registry,
    game_map: GameMap,
    rng: random.Random,
    message_log: MessageLog | None = None,
) -> bool:
    """
    Displace the player to a random legal land tile.

    If engulfed, clears predator links (teleport escape) first.
    Returns True when position changed.
    """
    if Player not in player.tags:
        return False
    was_engulfed = Engulfed in player.tags
    _clear_player_engulfment(player, world, message_log)

    destinations = collect_teleport_destinations(player, world, game_map)
    if not destinations:
        if message_log is not None:
            message_log.add(
                messages.teleport_failed(),
                category=MessageCategory.CAUTION,
            )
        return False

    dest = rng.choice(destinations)
    player.components[Position] = dest
    if message_log is not None:
        if was_engulfed:
            message_log.add(
                messages.teleport_escape(),
                category=MessageCategory.MAGICAL,
            )
        else:
            message_log.add(
                messages.teleport_success(),
                category=MessageCategory.MAGICAL,
            )
    return True


def tick_player_effects(
    player: Entity,
    message_log: MessageLog | None = None,
    *,
    world: Registry | None = None,
    game_map: GameMap | None = None,
    rng: random.Random | None = None,
) -> PlayerEffects:
    """
    Decrement active effect counters for one consumed player turn.

    When a buff expires, log a caution (yellow) wear-off message.
    Delayed teleport reaching 0 fires displacement when world/map are provided.
    """
    effects = ensure_player_effects(player)
    if effects.haste_turns > 0:
        effects.haste_turns -= 1
        if effects.haste_turns <= 0 and message_log is not None:
            message_log.add(
                messages.effect_haste_wore_off(),
                category=MessageCategory.CAUTION,
            )
    if effects.might_turns > 0:
        effects.might_turns -= 1
        if effects.might_turns <= 0:
            effects.might_accuracy_bonus = 0.0
            effects.might_min_damage_bonus = 0
            effects.might_max_damage_bonus = 0
            if message_log is not None:
                message_log.add(
                    messages.effect_might_wore_off(),
                    category=MessageCategory.CAUTION,
                )
    if effects.digestion_ward_turns > 0:
        effects.digestion_ward_turns -= 1
        if effects.digestion_ward_turns <= 0 and message_log is not None:
            message_log.add(
                messages.effect_antacid_wore_off(),
                category=MessageCategory.CAUTION,
            )
    if effects.teleport_pending_turns is not None:
        if effects.teleport_pending_turns <= 1:
            effects.teleport_pending_turns = None
            if world is not None and game_map is not None:
                fire_delayed_teleport(
                    player,
                    world,
                    game_map,
                    rng if rng is not None else random.Random(),
                    message_log,
                )
        else:
            effects.teleport_pending_turns -= 1
    return effects


def haste_skips_world_phase(player: Entity) -> bool:
    """
    True when this player action should not run the monster phase.

    Haste is 2 player actions per 1 monster phase: after tick, odd remaining
    turns mean the player just took the first half of a pair (skip world);
    even remaining (or expired) means monsters act.
    """
    effects = player.components.get(PlayerEffects)
    if effects is None or effects.haste_turns <= 0:
        return False
    return effects.haste_turns % 2 == 1


def apply_haste(player: Entity, duration_turns: int) -> None:
    """Set haste duration (refresh replaces remaining)."""
    effects = ensure_player_effects(player)
    effects.haste_turns = max(0, int(duration_turns))


def apply_might(
    player: Entity,
    *,
    duration_turns: int,
    accuracy_bonus: float,
    min_damage_bonus: int,
    max_damage_bonus: int,
) -> None:
    """Set might buff and snapshot combat bonuses (refresh replaces)."""
    effects = ensure_player_effects(player)
    effects.might_turns = max(0, int(duration_turns))
    effects.might_accuracy_bonus = float(accuracy_bonus)
    effects.might_min_damage_bonus = max(0, int(min_damage_bonus))
    effects.might_max_damage_bonus = max(0, int(max_damage_bonus))


def apply_digestion_ward(player: Entity, duration_turns: int) -> None:
    """Set antacid / digestion ward duration (refresh replaces)."""
    effects = ensure_player_effects(player)
    effects.digestion_ward_turns = max(0, int(duration_turns))


def queue_delayed_teleport(player: Entity, delay_turns: int) -> None:
    """Queue or refresh delayed teleport countdown (PR3 fires on zero)."""
    effects = ensure_player_effects(player)
    effects.teleport_pending_turns = max(1, int(delay_turns))


def has_digestion_ward(player: Entity) -> bool:
    effects = player.components.get(PlayerEffects)
    return effects is not None and effects.digestion_ward_turns > 0


def is_player_entity(entity: Entity) -> bool:
    return Player in entity.tags
