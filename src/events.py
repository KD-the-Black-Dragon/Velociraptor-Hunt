from __future__ import annotations

from collections.abc import Callable

from tcod.ecs import Entity

on_entity_defeated: list[Callable[[Entity], None]] = []
on_player_stunned: list[Callable[[Entity], None]] = []
on_item_used: list[Callable[[Entity, str], None]] = []
on_player_turn_consumed: list[Callable[[Entity], None]] = []
on_player_combat_targeted: list[Callable[[], None]] = []
on_vore_attempt: list[Callable[[Entity, Entity, bool], None]] = []
on_player_engulfed: list[Callable[[Entity, Entity], None]] = []
on_player_escaped_engulf: list[Callable[[Entity, Entity], None]] = []


def fire_entity_defeated(entity: Entity) -> None:
    for callback in on_entity_defeated:
        callback(entity)


def fire_player_stunned(entity: Entity) -> None:
    for callback in on_player_stunned:
        callback(entity)


def fire_item_used(entity: Entity, item_id: str) -> None:
    for callback in on_item_used:
        callback(entity, item_id)


def fire_player_turn_consumed(entity: Entity) -> None:
    for callback in on_player_turn_consumed:
        callback(entity)


def fire_player_combat_targeted() -> None:
    for callback in on_player_combat_targeted:
        callback()


def fire_vore_attempt(predator: Entity, prey: Entity, *, hit: bool) -> None:
    for callback in on_vore_attempt:
        callback(predator, prey, hit)


def fire_player_engulfed(player: Entity, predator: Entity) -> None:
    for callback in on_player_engulfed:
        callback(player, predator)


def fire_player_escaped_engulf(player: Entity, predator: Entity) -> None:
    for callback in on_player_escaped_engulf:
        callback(player, predator)