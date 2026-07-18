from __future__ import annotations

import random
from functools import lru_cache
from typing import TYPE_CHECKING

from tcod.ecs import Entity, Registry

from src.components import (
    BlocksMovement,
    ExamineDescription,
    Macguffin,
    Player,
    Position,
    Renderable,
)
from src.constants import MIN_PAIRWISE_SPREAD_BFS, RUNE_SPAWN_MIN_DISTANCE
from src.data.macguffin_loader import load_macguffin_registry
from src.data.macguffin_registry import MacguffinDefinition, MacguffinRegistry
from src.map_gen import GameMap
from src.systems.floor_runes import (
    RunePlacementError,
    choose_rune_placement,
    filter_candidates_by_entrance_distance,
    filter_candidates_by_pairwise_spread,
    rune_candidates_with_path_distance,
)

if TYPE_CHECKING:
    from src.engine import GameEngine


@lru_cache(maxsize=1)
def default_macguffin_registry() -> MacguffinRegistry:
    return load_macguffin_registry()


def reset_macguffin_registry_cache() -> None:
    default_macguffin_registry.cache_clear()


def macguffins_per_floor_max() -> int:
    """Worst-case macguffin count per floor for map validation (stock registry size)."""
    return len(default_macguffin_registry().macguffins)


def spawn_macguffin_entity(
    world: Registry,
    definition: MacguffinDefinition,
    x: int,
    y: int,
) -> Entity:
    entity = world[object()]
    entity.components[Position] = Position(x, y)
    entity.components[Renderable] = Renderable(
        ch=ord(definition.glyph),
        fg=definition.fg,
    )
    entity.components[ExamineDescription] = ExamineDescription(text=definition.examine)
    entity.components[Macguffin] = Macguffin(macguffin_id=definition.id)
    entity.tags.add(BlocksMovement)
    return entity


def spawn_macguffins(
    world: Registry,
    game_map: GameMap,
    floor_depth: int,
    *,
    rng: random.Random | None = None,
    registry: MacguffinRegistry | None = None,
    placed_positions: list[tuple[int, int]] | None = None,
    min_distance: int = RUNE_SPAWN_MIN_DISTANCE,
    min_pairwise: int = MIN_PAIRWISE_SPREAD_BFS,
) -> list[Entity]:
    """Place one macguffin per depth-eligible definition on distinct spread tiles."""
    rng = rng or random.Random()
    reg = registry or default_macguffin_registry()
    eligible = reg.eligible_at_depth(floor_depth)
    if not eligible:
        return []

    placed: list[Entity] = []
    occupied_positions = list(placed_positions or [])

    for index, definition in enumerate(eligible):
        candidates = rune_candidates_with_path_distance(
            game_map,
            world,
            game_map.enter_xy,
        )
        candidates = [
            (x, y, dist)
            for x, y, dist in candidates
            if (x, y) not in occupied_positions
        ]
        candidates = filter_candidates_by_entrance_distance(
            candidates,
            minimum=min_pairwise,
        )
        if not candidates:
            raise RunePlacementError("no valid macguffin tiles")

        if index == 0 and not occupied_positions:
            x, y, _achieved = choose_rune_placement(
                candidates,
                min_distance=min_distance,
                min_relax_to=min_pairwise,
                rng=rng,
            )
        else:
            spread_pool = filter_candidates_by_pairwise_spread(
                candidates,
                occupied_positions,
                game_map,
                minimum=min_pairwise,
            )
            if not spread_pool:
                raise RunePlacementError(
                    "insufficient pairwise spread for macguffin placement",
                )
            x, y, _achieved = rng.choice(spread_pool)

        occupied_positions.append((x, y))
        placed.append(spawn_macguffin_entity(world, definition, x, y))

    return placed


def count_floor_macguffins(world: Registry) -> int:
    return len(list(world.Q.all_of(components=[Macguffin])))


def try_begin_macguffin_activation(
    engine: GameEngine,
    player: Entity,
    x: int,
    y: int,
    *,
    registry: MacguffinRegistry | None = None,
) -> bool:
    """Step-on activation for macguffins. Returns True when the victory modal opened."""
    if Player not in player.tags:
        return False
    if engine.macguffin_victory_confirm.active:
        return False

    target = Position(x, y)
    macguffin_entities = list(
        engine.world.Q.all_of(tags=[target], components=[Macguffin]),
    )
    if not macguffin_entities:
        return False

    reg = registry or default_macguffin_registry()
    entity = macguffin_entities[0]
    macguffin = entity.components[Macguffin]
    definition = reg.get(macguffin.macguffin_id)
    engine.macguffin_discovery.record(definition)
    entity.clear()
    engine.macguffin_victory_confirm.open(
        macguffin_id=definition.id,
        display_name=definition.display_name,
        score=definition.score,
    )
    return True