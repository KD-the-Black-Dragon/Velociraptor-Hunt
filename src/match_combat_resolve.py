"""Pure attack resolution for arena matches (no dungeon combat side effects)."""

from __future__ import annotations

import random

from src.components import Fighter


def resolve_attack(
    attacker: Fighter,
    defender: Fighter,
    rng: random.Random,
) -> tuple[bool, int]:
    """Hit check and damage; same math as legacy core, without world hooks."""
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
