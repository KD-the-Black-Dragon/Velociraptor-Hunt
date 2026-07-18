"""Potion of alliance: summon a depth-appropriate good-aligned ally."""

from __future__ import annotations

import random

from tcod.ecs import Entity, Registry

from src.components import Alignment, BlocksMovement, Player, Position
from src.data.entity_loader import load_entity_registry
from src.data.entity_registry import EntityDefinition, EntityRegistry
from src.map_gen import GameMap, can_enter_tile
from src.spawn import spawn_from_definition


def good_summon_pool(
    registry: EntityRegistry,
    *,
    floor_depth: int,
) -> list[EntityDefinition]:
    """Good-aligned defs with positive weight eligible at this depth."""
    pool: list[EntityDefinition] = []
    for definition in registry.entities:
        if definition.alignment != Alignment.GOOD:
            continue
        if definition.spawn.weight <= 0:
            continue
        if not (definition.spawn.min_depth <= floor_depth <= definition.spawn.max_depth):
            continue
        pool.append(definition)
    return pool


def _tile_ok_for_definition(
    world: Registry,
    game_map: GameMap,
    x: int,
    y: int,
    definition: EntityDefinition,
) -> bool:
    if not game_map.in_bounds(x, y):
        return False
    if not can_enter_tile(game_map, x, y, definition.mobility):
        return False
    target = Position(x, y)
    for entity in world.Q.all_of(tags=[target, BlocksMovement]):
        return False
    return True


def find_summon_tile(
    world: Registry,
    game_map: GameMap,
    origin: Position,
    definition: EntityDefinition,
    rng: random.Random,
) -> Position | None:
    """Nearest legal tile to origin (Chebyshev rings); full-map last resort."""
    max_r = max(game_map.width, game_map.height)
    for radius in range(1, max_r + 1):
        ring: list[Position] = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if max(abs(dx), abs(dy)) != radius:
                    continue
                x, y = origin.x + dx, origin.y + dy
                if _tile_ok_for_definition(world, game_map, x, y, definition):
                    ring.append(Position(x, y))
        if ring:
            return rng.choice(ring)

    # Exhaustive scan: closest by Chebyshev
    best: list[Position] = []
    best_dist = 10**9
    for y in range(game_map.height):
        for x in range(game_map.width):
            if not _tile_ok_for_definition(world, game_map, x, y, definition):
                continue
            dist = max(abs(x - origin.x), abs(y - origin.y))
            if dist < best_dist:
                best_dist = dist
                best = [Position(x, y)]
            elif dist == best_dist:
                best.append(Position(x, y))
    if not best:
        return None
    return rng.choice(best)


def try_summon_ally(
    player: Entity,
    world: Registry,
    game_map: GameMap,
    *,
    floor_depth: int,
    difficulty_id: str | None = None,
    rng: random.Random | None = None,
    registry: EntityRegistry | None = None,
) -> Entity | None:
    """
    Spawn one weighted good ally as close as possible to the player.

    Returns the summoned entity, or None if no pool or no free tile.
    """
    if Player not in player.tags:
        return None
    rng = rng or random.Random()
    reg = registry or load_entity_registry()
    pool = good_summon_pool(reg, floor_depth=floor_depth)
    if not pool:
        return None
    weights = [max(0.0, float(d.spawn.weight)) for d in pool]
    if sum(weights) <= 0:
        return None
    definition = rng.choices(pool, weights=weights, k=1)[0]
    origin = player.components[Position]
    tile = find_summon_tile(world, game_map, origin, definition, rng)
    if tile is None:
        return None
    return spawn_from_definition(
        world,
        definition,
        tile.x,
        tile.y,
        floor_depth=floor_depth,
        difficulty_id=difficulty_id,
        roll_prefix=False,
        rng=rng,
    )
