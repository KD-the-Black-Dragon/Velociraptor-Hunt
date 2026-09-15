"""Periodic player-engulfed atmospheric log lines from predator data."""

from __future__ import annotations

import random

from tcod.ecs import Entity, Registry

from src.components import Engulfed, Player, Predator
from src.data.narrative_index import get_narrative_index
from src.log_categories import MessageCategory
from src.message_log import MessageLog
from src.systems.naming import entity_type_id
from src.systems.vore import find_predator_holding_prey, format_npc_vore_line

ENGULFED_FLAVOR_EVERY_N_WORLD_PHASES = 3


def maybe_emit_engulfed_flavor(
    world: Registry,
    player: Entity,
    message_log: MessageLog,
    rng: random.Random,
) -> None:
    """After a completed world phase: count hold phases and maybe log flavor.

    Fires on phases 3, 6, 9… of the current engulfment. Missing/empty pools
    are a silent no-op (never logs a blank line).
    """
    if Player not in player.tags or Engulfed not in player.tags:
        return
    predator = find_predator_holding_prey(world, player)
    if predator is None:
        return
    state = predator.components.get(Predator)
    if state is None:
        return

    state.engulfed_flavor_phases += 1
    if state.engulfed_flavor_phases % ENGULFED_FLAVOR_EVERY_N_WORLD_PHASES != 0:
        return

    template = get_narrative_index().pick_engulfed_flavor_line(
        entity_type_id(predator),
        state.narrative_type,
        rng,
    )
    if not template:
        return
    line = format_npc_vore_line(template, predator, player)
    if not line.strip():
        return
    message_log.add(line, category=MessageCategory.SPEECH)
