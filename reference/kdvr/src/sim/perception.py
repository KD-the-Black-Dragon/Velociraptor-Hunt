"""Sim visibility and threat perception."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tcod.ecs import Entity

from src.components import (
    AI,
    Alignment,
    Fighter,
    FloorRune,
    Item,
    ItemCategory,
    Mobility,
    MobilityType,
    NPCAlignment,
    Position,
)
from src.map_gen import GameMap
from src.systems.naming import entity_type_id

if TYPE_CHECKING:
    from src.engine import GameEngine
    from src.sim.snapshots import FloorVisitTracker

SHARK_THREAT_RADIUS = 6
LOOT_CATEGORIES = frozenset(
    {
        ItemCategory.WEAPON,
        ItemCategory.ARMOR,
        ItemCategory.POTION,
        ItemCategory.WAND,
    }
)


def is_aquatic_evil(entity: Entity) -> bool:
    alignment = entity.components.get(NPCAlignment)
    if alignment is None or alignment.alignment != Alignment.EVIL:
        return False
    if entity_type_id(entity) == "shark":
        return True
    mobility = entity.components.get(Mobility)
    return mobility is not None and mobility.kind == MobilityType.AQUATIC


def is_non_aquatic_evil(entity: Entity) -> bool:
    alignment = entity.components.get(NPCAlignment)
    if alignment is None or alignment.alignment != Alignment.EVIL:
        return False
    return not is_aquatic_evil(entity)


def _tile_visible(game_map: GameMap, x: int, y: int) -> bool:
    if not game_map.in_bounds(x, y):
        return False
    return bool(game_map.visible[y, x])


def _player_position(engine: GameEngine) -> Position | None:
    if engine.player is None:
        return None
    return engine.player.components.get(Position)


def visible_evil_entities(engine: GameEngine) -> list[Entity]:
    player_pos = _player_position(engine)
    if player_pos is None:
        return []
    result: list[Entity] = []
    for entity in engine.world.Q.all_of(components=[AI, Position, NPCAlignment, Fighter]):
        if entity.components[NPCAlignment].alignment != Alignment.EVIL:
            continue
        pos = entity.components[Position]
        if _tile_visible(engine.game_map, pos.x, pos.y):
            result.append(entity)
    return result


def visible_aquatic_evils(engine: GameEngine) -> list[Entity]:
    return [entity for entity in visible_evil_entities(engine) if is_aquatic_evil(entity)]


def visible_non_aquatic_evils(engine: GameEngine) -> list[Entity]:
    return [entity for entity in visible_evil_entities(engine) if is_non_aquatic_evil(entity)]


def aquatic_evils_within_radius(engine: GameEngine, radius: int) -> list[Entity]:
    player_pos = _player_position(engine)
    if player_pos is None:
        return []
    from src.sim.navigation import player_walk_distances

    distances = player_walk_distances(engine.game_map, (player_pos.x, player_pos.y))
    threats: list[Entity] = []
    for entity in visible_aquatic_evils(engine):
        pos = entity.components[Position]
        dist = distances.get((pos.x, pos.y))
        if dist is not None and dist <= radius:
            threats.append(entity)
    return threats


def adjacent_evil_entities(
    engine: GameEngine,
    *,
    aquatic: bool | None = None,
) -> list[Entity]:
    player_pos = _player_position(engine)
    if player_pos is None:
        return []
    adjacent: list[Entity] = []
    for entity in visible_evil_entities(engine):
        if aquatic is True and not is_aquatic_evil(entity):
            continue
        if aquatic is False and not is_non_aquatic_evil(entity):
            continue
        pos = entity.components[Position]
        if abs(pos.x - player_pos.x) <= 1 and abs(pos.y - player_pos.y) <= 1:
            if pos.x == player_pos.x and pos.y == player_pos.y:
                continue
            adjacent.append(entity)
    return adjacent


def _is_policy_loot_item(item: Item) -> bool:
    return item.category in LOOT_CATEGORIES


def visible_loot_positions(engine: GameEngine) -> list[tuple[int, int]]:
    """Distinct tiles with visible weapon/armor/potion/wand floor loot."""
    positions: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    for entity in engine.world.Q.all_of(components=[Item, Position]):
        item = entity.components[Item]
        if not _is_policy_loot_item(item):
            continue
        pos = entity.components[Position]
        coord = (pos.x, pos.y)
        if coord in seen:
            continue
        if _tile_visible(engine.game_map, pos.x, pos.y):
            positions.append(coord)
            seen.add(coord)
    return positions


def visible_loot_at_tile(engine: GameEngine, x: int, y: int) -> bool:
    """True when a policy-loot item is visible on ``(x, y)``."""
    if not _tile_visible(engine.game_map, x, y):
        return False
    from src.systems.inventory import floor_items_at

    for entity in floor_items_at(engine.world, x, y):
        item = entity.components.get(Item)
        if item is not None and _is_policy_loot_item(item):
            return True
    return False


def visible_floor_rune_positions(engine: GameEngine) -> list[tuple[int, int]]:
    positions: list[tuple[int, int]] = []
    for entity in engine.world.Q.all_of(components=[FloorRune, Position]):
        pos = entity.components[Position]
        if _tile_visible(engine.game_map, pos.x, pos.y):
            positions.append((pos.x, pos.y))
    return positions


def floor_runes_this_floor(engine: GameEngine, visit: FloorVisitTracker | None) -> int:
    if visit is None:
        return 0
    return max(0, engine.run_stats.runes_collected - visit.runes_at_start)


def rune_quota_met(engine: GameEngine, visit: FloorVisitTracker | None) -> bool:
    return floor_runes_this_floor(engine, visit) >= engine.runes_per_floor()