from __future__ import annotations

import random

from tcod.ecs import Entity

from src.data.rescue_gratitude_registry import RescueGratitudeRegistry
from src.systems.naming import entity_log_name


def pick_rescue_gratitude_line(
    registry: RescueGratitudeRegistry,
    rng: random.Random,
) -> str:
    return rng.choice(registry.lines)


def format_rescue_gratitude(prey: Entity, template: str) -> str:
    return template.replace("{name}", entity_log_name(prey))