from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Protocol

from tcod.ecs import Entity, Registry

from src import messages
from src.components import AI, Alignment, NPCAlignment, Position
from src.map_gen import GameMap
from src.message_log import MessageCategory, MessageLog
from src.systems.ai.targeting import _visible_good_evils
from src.systems.fov import entity_visible_to_player, player_has_visible_evil
from src.systems.naming import entity_log_name
from src.events import on_player_combat_targeted


class DangerInterruptReason(Enum):
    ATTACK = "attack"
    VISIBLE_EVIL = "danger"
    ALLY_ALARM = "ally_alarm"


class AttackInterruptSession(Protocol):
    attack_interrupt: bool

    def clear_attack_interrupt(self) -> None: ...


def _sorted_good_allies(world: Registry, player: Entity) -> list[Entity]:
    allies: list[Entity] = []
    for entity in world.Q.all_of(components=[AI, Position, NPCAlignment]):
        if entity is player:
            continue
        if entity.components[NPCAlignment].alignment != Alignment.GOOD:
            continue
        allies.append(entity)
    return sorted(
        allies,
        key=lambda entity: (
            entity.components[Position].y,
            entity.components[Position].x,
            id(entity),
        ),
    )


def find_good_ally_alarm_shouter(
    game_map: GameMap,
    world: Registry,
    player: Entity,
) -> Entity | None:
    """First good ally in player LOS that sees an evil NPC (LOS)."""
    for ally in _sorted_good_allies(world, player):
        if not entity_visible_to_player(game_map, ally):
            continue
        if _visible_good_evils(ally, world, game_map):
            return ally
    return None


def evaluate_danger_interrupt(
    *,
    player: Entity,
    game_map: GameMap,
    world: Registry,
    message_log: MessageLog,
    attack_interrupt: bool,
) -> DangerInterruptReason | None:
    """Shared danger stops for rest and autoexplore (after a consumed turn)."""
    if attack_interrupt:
        message_log.add(
            messages.rest_interrupted_by_attack(),
            category=MessageCategory.CAUTION,
        )
        return DangerInterruptReason.ATTACK

    if player_has_visible_evil(game_map, world):
        message_log.add(
            messages.rest_danger_approaches(),
            category=MessageCategory.CAUTION,
        )
        return DangerInterruptReason.VISIBLE_EVIL

    alarm_ally = find_good_ally_alarm_shouter(game_map, world, player)
    if alarm_ally is not None:
        name = entity_log_name(alarm_ally, sentence_start=True)
        message_log.add(
            messages.good_ally_shouts_alarm(name),
            category=MessageCategory.CAUTION,
        )
        return DangerInterruptReason.ALLY_ALARM

    return None


def attach_attack_interrupt_listener(
    session: AttackInterruptSession,
) -> Callable[[], None]:
    def _mark_attacked() -> None:
        session.attack_interrupt = True

    on_player_combat_targeted.append(_mark_attacked)
    return _mark_attacked


def detach_attack_interrupt_listener(marker: Callable[[], None]) -> None:
    on_player_combat_targeted.remove(marker)