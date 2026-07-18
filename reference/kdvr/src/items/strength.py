"""Shared item strength ordering for gear selection."""

from __future__ import annotations

import random
from typing import Protocol, TypeVar

T = TypeVar("T")


class _WeaponLike(Protocol):
    min_damage: int
    max_damage: int
    accuracy_bonus: float


class _ArmorLike(Protocol):
    ac_bonus: int


def weapon_strength_key(item: _WeaponLike) -> tuple[int, int, float]:
    """Higher is stronger: min damage, then max damage, then accuracy."""
    return (item.min_damage, item.max_damage, item.accuracy_bonus)


def pick_strongest(
    items: list[T],
    *,
    key,
    rng: random.Random,
) -> T | None:
    """Return the strongest item; break ties with ``rng.choice``."""
    if not items:
        return None
    best_key = max(key(item) for item in items)
    tied = [item for item in items if key(item) == best_key]
    return rng.choice(tied)


def pick_strongest_armor(
    items: list[_ArmorLike],
    *,
    rng: random.Random,
) -> _ArmorLike | None:
    if not items:
        return None
    best_ac = max(item.ac_bonus for item in items)
    tied = [item for item in items if item.ac_bonus == best_ac]
    return rng.choice(tied)