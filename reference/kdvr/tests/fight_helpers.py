"""Shared Fighter builders for tests."""

from __future__ import annotations

from src.components import Fighter
from src.constants import (
    PLAYER_AC,
    PLAYER_ACCURACY,
    PLAYER_EVADE,
    PLAYER_MAX_DAMAGE,
    PLAYER_MIN_DAMAGE,
)
from src.data.entity_loader import load_entity_registry


def fighter_from_entity(entity_id: str, *, hp: int | None = None) -> Fighter:
    definition = load_entity_registry().get(entity_id)
    max_hp = definition.max_hp if hp is None else hp
    return Fighter(
        hp=hp if hp is not None else definition.max_hp,
        max_hp=max_hp,
        accuracy=definition.accuracy,
        evade=definition.evade,
        ac=definition.ac,
        min_damage=definition.min_damage,
        max_damage=definition.max_damage,
        ranged_accuracy=definition.ranged_accuracy,
        ranged_min_damage=definition.ranged_min_damage,
        ranged_max_damage=definition.ranged_max_damage,
    )


def fighter_player(*, hp: int = 30, max_hp: int = 30) -> Fighter:
    return Fighter(
        hp=hp,
        max_hp=max_hp,
        accuracy=PLAYER_ACCURACY,
        evade=PLAYER_EVADE,
        ac=PLAYER_AC,
        min_damage=PLAYER_MIN_DAMAGE,
        max_damage=PLAYER_MAX_DAMAGE,
    )


def fighter_inert(*, hp: int = 10, max_hp: int = 10) -> Fighter:
    return Fighter(
        hp=hp,
        max_hp=max_hp,
        accuracy=10.0,
        evade=0,
        ac=0,
        min_damage=0,
        max_damage=0,
    )