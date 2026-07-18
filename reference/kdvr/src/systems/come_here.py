"""Player "Come here!" shout — PR1 plumbing (flags + cooldown; AI in PR2)."""

from __future__ import annotations

from enum import Enum, auto

from tcod.ecs import Entity, Registry

from src.components import (
    AI,
    AIState,
    Alignment,
    Engulfed,
    NPCAlignment,
    Player,
    Position,
)
from src.map_gen import GameMap
from src.message_log import MessageCategory, MessageLog
from src.systems.fov import entity_visible_to_player
from src import messages

# Successful shouts only; measured in player_turn_count units.
COME_HERE_COOLDOWN_TURNS = 4


class ComeHereResult(Enum):
    """Outcome of try_come_here_shout."""

    NONE = auto()
    COOLDOWN = auto()  # spam; no turn
    SHOUTED = auto()  # turn consumed (orders may or may not have been issued)
    ENGULFED_FIZZLE = auto()  # turn consumed; no ally flags


def _get_ai_state(entity: Entity) -> AIState:
    state = entity.components.get(AIState)
    if state is None:
        state = AIState()
        entity.components[AIState] = state
    return state


def good_allies_in_player_fov(
    world: Registry,
    game_map: GameMap,
    player: Entity,
) -> list[Entity]:
    """Good NPCs currently on a player-visible tile (snapshot for shout)."""
    allies: list[Entity] = []
    for entity in world.Q.all_of(components=[AI, Position, NPCAlignment]):
        if entity is player or Player in entity.tags:
            continue
        if entity.components[NPCAlignment].alignment != Alignment.GOOD:
            continue
        if not entity_visible_to_player(game_map, entity):
            continue
        allies.append(entity)
    return allies


def clear_all_come_here(world: Registry) -> None:
    """Drop come-here orders (e.g. floor change)."""
    for entity in world.Q.all_of(components=[AIState]):
        entity.components[AIState].come_here = False


def try_come_here_shout(
    world: Registry,
    game_map: GameMap,
    player: Entity,
    message_log: MessageLog,
    *,
    player_turn_count: int,
    last_come_here_turn: int,
) -> tuple[ComeHereResult, int]:
    """Attempt the Come here! shout.

    Returns ``(result, new_last_come_here_turn)``. On COOLDOWN, last turn is
    unchanged and the caller must not consume a turn. On SHOUTED or
    ENGULFED_FIZZLE, last turn is set to ``player_turn_count`` and the caller
    consumes a turn.
    """
    if Player not in player.tags:
        return ComeHereResult.NONE, last_come_here_turn

    if last_come_here_turn >= 0:
        elapsed = player_turn_count - last_come_here_turn
        if elapsed < COME_HERE_COOLDOWN_TURNS:
            message_log.add(
                messages.come_here_hoarse(),
                category=MessageCategory.ROUTINE,
            )
            return ComeHereResult.COOLDOWN, last_come_here_turn

    if Engulfed in player.tags:
        message_log.add(
            messages.come_here_engulfed_fizzle(),
            category=MessageCategory.SPEECH,
        )
        return ComeHereResult.ENGULFED_FIZZLE, player_turn_count

    message_log.add(
        messages.come_here_shout(),
        category=MessageCategory.SPEECH,
    )
    for ally in good_allies_in_player_fov(world, game_map, player):
        _get_ai_state(ally).come_here = True
    return ComeHereResult.SHOUTED, player_turn_count
