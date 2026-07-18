"""Whole-floor dungeon layout archetypes."""

from __future__ import annotations

import random

from src.map_gen import GameMap
from src.map_gen_layouts.boxy import carve_boxy_layout
from src.map_gen_layouts.common import pick_layout_archetype
from src.map_gen_layouts.hybrid import carve_hybrid_layout
from src.map_gen_layouts.organic import carve_organic_layout

__all__ = [
    "carve_layout",
    "pick_layout_archetype",
]


def carve_layout(
    game_map: GameMap,
    rng: random.Random,
    archetype: str,
    *,
    max_rooms: int,
    room_min_size: int,
    room_max_size: int,
) -> bool:
    game_map.layout_archetype = archetype
    match archetype:
        case "boxy":
            return carve_boxy_layout(
                game_map,
                rng,
                max_rooms=max_rooms,
                room_min_size=room_min_size,
                room_max_size=room_max_size,
            )
        case "organic":
            return carve_organic_layout(game_map, rng)
        case "hybrid":
            return carve_hybrid_layout(
                game_map,
                rng,
                room_min_size=room_min_size,
                room_max_size=room_max_size,
            )
        case _:
            return carve_boxy_layout(
                game_map,
                rng,
                max_rooms=max_rooms,
                room_min_size=room_min_size,
                room_max_size=room_max_size,
            )