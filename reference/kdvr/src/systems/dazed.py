"""NPC Dazed status: apply, stack, and AI-turn tick."""

from __future__ import annotations

import random

from tcod.ecs import Entity

from src import messages
from src.components import Dazed, Player
from src.data.depth_scaling_config import DifficultyProfile
from src.map_gen import GameMap
from src.message_log import MessageCategory, MessageLog
from src.systems.fov import entity_visible_to_player
from src.systems.naming import entity_log_name


def roll_cv_daze_turns(profile: DifficultyProfile, rng: random.Random) -> int:
    """Inclusive roll of Alternate CV daze duration from a difficulty profile."""
    lo = int(profile.cv_daze_min_turns)
    hi = int(profile.cv_daze_max_turns)
    if lo > hi:
        lo, hi = hi, lo
    return rng.randint(lo, hi)


def apply_daze(
    entity: Entity,
    turns: int,
    game_map: GameMap,
    message_log: MessageLog,
) -> None:
    """Apply or stack daze on an NPC. Ignores the player and non-positive turns."""
    if Player in entity.tags or turns <= 0:
        return
    existing = entity.components.get(Dazed)
    if existing is None:
        entity.components[Dazed] = Dazed(remaining=int(turns))
        if entity_visible_to_player(game_map, entity):
            message_log.add(
                messages.npc_appears_dazed(
                    entity_log_name(entity, sentence_start=True)
                ),
                category=MessageCategory.CAUTION,
            )
        return
    existing.remaining += int(turns)


def tick_daze_on_ai_turn(
    monster: Entity,
    game_map: GameMap,
    message_log: MessageLog,
) -> bool:
    """If ``monster`` is dazed, decrement and skip the AI turn.

    Returns True when the monster should skip its action this turn.
    The turn that reduces remaining to 0 still skips; the next turn may act.
    """
    dazed = monster.components.get(Dazed)
    if dazed is None:
        return False
    dazed.remaining -= 1
    if dazed.remaining <= 0:
        monster.components.pop(Dazed, None)
        if entity_visible_to_player(game_map, monster):
            message_log.add(
                messages.npc_no_longer_dazed(
                    entity_log_name(monster, sentence_start=True)
                ),
                category=MessageCategory.POSITIVE,
            )
    return True
