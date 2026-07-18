"""Shared floor carving for tests that pin entities to fixed map coordinates."""

from __future__ import annotations

import random
from collections.abc import Iterator

from src.components import AI, BlocksMovement, DisplayName, Position, VoreCapable
from src.data.dungeon_spawn_loader import load_dungeon_spawn_config
from src.engine import GameEngine
from src.map_gen import GameMap, Tile
from src.spawn import count_valid_spawn_tiles, valid_spawn_tiles
from src.data.dungeon_spawn_config import compute_target_npc_count

# Isolated horizontal arena — avoids random spawn/water/stairs collisions.
ARENA_X = 40
ARENA_Y = 22
BUMP_ARENA_Y = 24
FOV_PLAYER_X = ARENA_X - 5
FOV_HIDDEN_Y = ARENA_Y + 15


def carve_floor_rect(
    engine: GameEngine,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
) -> None:
    game_map = engine.game_map
    for y in range(min(y1, y2), max(y1, y2) + 1):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if game_map.in_bounds(x, y):
                game_map.tiles[y, x] = Tile.FLOOR


def carve_floor_tile(engine: GameEngine, x: int, y: int) -> None:
    carve_floor_rect(engine, x, y, x, y)


def isolate_other_ais(engine: GameEngine, *, keep: tuple[object, ...] = ()) -> None:
    """Move every AI except `keep` (and the player) to a distant carved tile."""
    from src.components import AI

    stash_x, stash_y = 70, 40
    carve_floor_tile(engine, stash_x, stash_y)
    player = engine.player
    for entity in engine.world.Q.all_of(components=[AI, Position]):
        if entity is player or entity in keep:
            continue
        entity.components[Position] = Position(stash_x, stash_y)


def carve_horizontal_line(engine: GameEngine, x: int, y: int, length: int) -> list[Position]:
    carve_floor_rect(engine, x, y, x + length - 1, y)
    return [Position(x + offset, y) for offset in range(length)]


def carved_collinear(engine: GameEngine, count: int) -> list[Position]:
    """Deterministic `count` tiles in a row with LOS."""
    isolate_other_ais(engine)
    return carve_horizontal_line(engine, ARENA_X, ARENA_Y, count)


def carve_east_of(engine: GameEngine, origin: Position, length: int) -> None:
    """Carve `length` floor tiles eastward from `origin` (inclusive)."""
    carve_floor_rect(engine, origin.x, origin.y, origin.x + length - 1, origin.y)


def ensure_adjacent_floor(
    engine: GameEngine,
    pos: Position,
    direction: tuple[int, int] = (1, 0),
) -> Position:
    dx, dy = direction
    dest = Position(pos.x + dx, pos.y + dy)
    carve_floor_tile(engine, pos.x, pos.y)
    carve_floor_tile(engine, dest.x, dest.y)
    return dest


def tile_occupied(engine: GameEngine, x: int, y: int) -> bool:
    target = Position(x, y)
    return any(
        entity for entity in engine.world.Q.all_of(tags=[target, BlocksMovement])
    )


def carved_bump_pair(
    engine: GameEngine,
) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    """Actor tile, defender tile, and eastward bump direction on carved floor."""
    isolate_other_ais(engine)
    carve_horizontal_line(engine, ARENA_X, BUMP_ARENA_Y, 2)
    return (ARENA_X, BUMP_ARENA_Y), (ARENA_X + 1, BUMP_ARENA_Y), (1, 0)


def relocate_player(engine: GameEngine, x: int, y: int) -> Position:
    """Carve and move the player to a deterministic tile."""
    carve_floor_tile(engine, x, y)
    player = engine.player
    assert player is not None
    player.components[Position] = Position(x, y)
    return player.components[Position]


def _carve_fov_test_arena(engine: GameEngine) -> None:
    """Open floor box so FOV bump pairs are not blocked by random walls."""
    carve_floor_rect(
        engine,
        FOV_PLAYER_X - 1,
        ARENA_Y - 1,
        FOV_PLAYER_X + 8,
        FOV_HIDDEN_Y + 1,
    )


def carved_fov_bump_pair(
    engine: GameEngine,
    *,
    require_visible: bool,
) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    """Actor/defender tiles on carved floor inside or outside player FOV."""
    from src.systems.fov import update_fov

    _carve_fov_test_arena(engine)
    isolate_other_ais(engine)
    relocate_player(engine, FOV_PLAYER_X, ARENA_Y)
    if require_visible:
        ax, ay = FOV_PLAYER_X + 2, ARENA_Y
    else:
        ax, ay = FOV_PLAYER_X, FOV_HIDDEN_Y
    carve_horizontal_line(engine, ax, ay, 2)
    pos = engine.player.components[Position]
    update_fov(engine.game_map, pos.x, pos.y)
    game_map = engine.game_map
    visible = game_map.visible[ay, ax] or game_map.visible[ay, ax + 1]
    if visible != require_visible:
        raise RuntimeError(
            f"FOV bump pair visibility mismatch: visible={visible} "
            f"require_visible={require_visible}"
        )
    return (ax, ay), (ax + 1, ay), (1, 0)


def carved_hidden_tile(engine: GameEngine) -> tuple[int, int]:
    """Single floor tile guaranteed outside the player's current FOV."""
    from src.systems.fov import update_fov

    _carve_fov_test_arena(engine)
    relocate_player(engine, FOV_PLAYER_X, ARENA_Y)
    hx, hy = ARENA_X, FOV_HIDDEN_Y
    carve_floor_tile(engine, hx, hy)
    update_fov(engine.game_map, FOV_PLAYER_X, ARENA_Y)
    assert not engine.game_map.visible[hy, hx]
    return hx, hy


def carved_hidden_line(engine: GameEngine, length: int = 2) -> list[tuple[int, int]]:
    """Horizontal floor line guaranteed outside the player's current FOV."""
    from src.systems.fov import update_fov

    _carve_fov_test_arena(engine)
    relocate_player(engine, FOV_PLAYER_X, ARENA_Y)
    hx, hy = ARENA_X, FOV_HIDDEN_Y
    carve_horizontal_line(engine, hx, hy, length)
    update_fov(engine.game_map, FOV_PLAYER_X, ARENA_Y)
    coords = [(hx + offset, hy) for offset in range(length)]
    assert all(not engine.game_map.visible[y, x] for x, y in coords)
    return coords


def carve_adjacent_line(
    engine: GameEngine,
    pos: Position,
    count: int,
    direction: tuple[int, int] = (1, 0),
) -> list[Position]:
    """Carve `pos` and `count` tiles extending from it in `direction`."""
    dx, dy = direction
    carve_floor_tile(engine, pos.x, pos.y)
    carved: list[Position] = []
    for step in range(1, count + 1):
        x, y = pos.x + dx * step, pos.y + dy * step
        carve_floor_tile(engine, x, y)
        carved.append(Position(x, y))
    return carved


def expected_ai_count(
    game_map: GameMap,
    *,
    floor_depth: int = 1,
    rng_seed: int = 0,
    good_follower_reduction: int = 0,
) -> int:
    """Expected NPC count for a map using stock dungeon_spawn.json (same seed as engine rng at spawn)."""
    enter_x, enter_y = game_map.enter_xy
    land, water = valid_spawn_tiles(game_map, enter_x, enter_y)
    valid_count = count_valid_spawn_tiles(land, water)
    config = load_dungeon_spawn_config()
    target = compute_target_npc_count(
        valid_count,
        floor_depth,
        config,
        random.Random(rng_seed),
    )
    return max(0, target - good_follower_reduction)


def iter_wolves(engine: GameEngine) -> Iterator[object]:
    """Yield spawned wolves (excludes sharks and other vore-capable species)."""
    for entity in engine.world.Q.all_of(tags=[VoreCapable], components=[AI]):
        display = entity.components.get(DisplayName)
        if display is not None and display.name == "wolf":
            yield entity


def ensure_wolf(engine: GameEngine, *, x: int = 72, y: int = 40) -> object:
    """Return a wolf on the map, spawning one if density spawn did not place any."""
    wolves = list(iter_wolves(engine))
    if wolves:
        return wolves[0]
    from src.spawn import spawn_entity_by_id

    carve_floor_tile(engine, x, y)
    return spawn_entity_by_id(engine.world, "wolf", x, y)


def ensure_wolves(
    engine: GameEngine,
    count: int,
    *,
    start_x: int = 70,
    start_y: int = 40,
) -> list[object]:
    """Return at least `count` wolves, spawning extras on carved tiles if needed."""
    wolves = list(iter_wolves(engine))
    if len(wolves) >= count:
        return wolves[:count]

    from src.spawn import spawn_entity_by_id

    x = start_x
    while len(wolves) < count:
        carve_floor_tile(engine, x, start_y)
        wolves.append(spawn_entity_by_id(engine.world, "wolf", x, start_y))
        x += 1
    return wolves[:count]


def first_wolf(engine: GameEngine):
    return ensure_wolf(engine)


def place_adjacent_wolf(engine: GameEngine):
    """Place a vore-capable wolf on carved floor east of the player.

    Spawns a wolf if the floor has none (never relies on ``next(iter_wolves)``).
    """
    from src.systems.fov import update_fov

    player = engine.player
    assert player is not None
    pos = player.components[Position]
    carve_east_of(engine, pos, 2)
    wolf = ensure_wolf(engine, x=pos.x + 1, y=pos.y)
    wolf.components[Position] = Position(pos.x + 1, pos.y)
    isolate_other_ais(engine, keep=(wolf,))
    update_fov(engine.game_map, pos.x, pos.y)
    return wolf


def place_wolf_at(engine: GameEngine, wolf: object, x: int, y: int) -> None:
    carve_floor_tile(engine, x, y)
    wolf.components[Position] = Position(x, y)  # type: ignore[union-attr]


def clear_wolf_abilities(engine: GameEngine) -> None:
    """Remove ability tokens from every wolf (vore/turn-order tests need normal cadence)."""
    from src.components import Abilities

    for wolf in iter_wolves(engine):
        wolf.components.pop(Abilities, None)


def spawn_wolf_with_abilities(
    world,
    x: int,
    y: int,
    abilities: list[str],
):
    """Spawn a wolf and replace abilities with the given raw tokens (tests)."""
    from src.components import Abilities, AbilityState
    from src.data.ability_parser import parse_abilities
    from src.spawn import spawn_entity_by_id

    wolf = spawn_entity_by_id(world, "wolf", x, y)
    wolf.components[AbilityState] = AbilityState()
    parsed = parse_abilities(abilities)
    if parsed:
        wolf.components[Abilities] = Abilities(parsed=parsed)
    else:
        wolf.components.pop(Abilities, None)
    return wolf