"""PR3: floor rune catalog, spawn, render, and NPC blocking."""

from __future__ import annotations

import random

import pytest
from tcod.ecs import Registry

from src.components import BlocksMovement, FloorRune, Player, Position
from src.constants import MIN_PAIRWISE_SPREAD_BFS, RUNE_SPAWN_MIN_DISTANCE, RUNES_PER_FLOOR
from src.data.floor_rune_loader import (
    FLOOR_RUNES_PATH,
    FloorRuneLoadError,
    load_floor_rune_registry,
    parse_floor_rune_registry,
)
from src.engine import GameEngine
from src.map_gen import GameMap, Tile
from src.systems.floor_runes import (
    RunePlacementError,
    bfs_path_distance_from,
    choose_rune_placement,
    count_floor_runes,
    rune_candidates_with_path_distance,
    spawn_floor_rune,
)
from src.systems.movement import can_move_to
from tests.rune_test_helpers import (
    minimal_floor_runes_payload,
    rune_placement_arena,
    write_floor_runes,
)


def test_load_default_floor_runes_json() -> None:
    """Smoke: production file parses; balance/counts are not asserted here."""
    registry = load_floor_rune_registry(FLOOR_RUNES_PATH)
    assert registry.schema_version == 1
    assert registry.runes
    for rune in registry.runes:
        assert rune.id
        assert rune.glyph
        assert rune.weight > 0


def test_forbidden_wall_glyph_rejected() -> None:
    payload = minimal_floor_runes_payload(
        runes=[
            {
                "id": "bad_rune",
                "display_name": "bad",
                "glyph": "#",
                "fg": [1, 1, 1],
                "examine": "bad",
                "weight": 1,
                "min_depth": 1,
                "max_depth": 10,
                "effect": {"type": "max_hp", "amount": 1},
            }
        ]
    )
    with pytest.raises(FloorRuneLoadError, match="reserved"):
        parse_floor_rune_registry(payload)


def test_new_game_spawns_three_floor_runes() -> None:
    engine = GameEngine()
    engine.new_game(seed=42)
    assert count_floor_runes(engine.world) == RUNES_PER_FLOOR


def test_descend_spawns_three_floor_runes() -> None:
    from tests.test_dungeon_pr3 import _place_player_on_stairs, _press_descend

    engine = GameEngine()
    engine.new_game(seed=17)
    _place_player_on_stairs(engine)
    _press_descend(engine)
    assert count_floor_runes(engine.world) == RUNES_PER_FLOOR


def test_rune_placed_on_floor_not_stairs() -> None:
    world = Registry()
    game_map = rune_placement_arena()
    mid_y = game_map.height // 2
    stairs_x = game_map.width - 3
    game_map.tiles[mid_y, stairs_x] = Tile.STAIRS_DOWN
    registry = parse_floor_rune_registry(minimal_floor_runes_payload())
    rune = spawn_floor_rune(
        world,
        game_map,
        floor_depth=1,
        rng=random.Random(0),
        registry=registry,
        min_distance=5,
        min_pairwise=5,
        count=1,
    )[0]
    pos = rune.components[Position]
    assert game_map.tiles[pos.y, pos.x] == Tile.FLOOR


def test_rune_entrance_distance_never_relaxes_below_twenty() -> None:
    world = Registry()
    game_map = rune_placement_arena(width=12, height=8)
    candidates = rune_candidates_with_path_distance(game_map, world, game_map.enter_xy)
    with pytest.raises(RunePlacementError, match="entrance min distance"):
        choose_rune_placement(
            candidates,
            min_distance=RUNE_SPAWN_MIN_DISTANCE,
            min_relax_to=MIN_PAIRWISE_SPREAD_BFS,
            rng=random.Random(1),
        )


def test_rune_entrance_distance_relaxes_only_to_twenty() -> None:
    world = Registry()
    game_map = rune_placement_arena(width=40, height=10)
    registry = parse_floor_rune_registry(minimal_floor_runes_payload())
    candidates = rune_candidates_with_path_distance(game_map, world, game_map.enter_xy)
    _x, _y, achieved = choose_rune_placement(
        candidates,
        min_distance=RUNE_SPAWN_MIN_DISTANCE,
        min_relax_to=MIN_PAIRWISE_SPREAD_BFS,
        rng=random.Random(1),
    )
    assert achieved >= MIN_PAIRWISE_SPREAD_BFS
    rune = spawn_floor_rune(
        world,
        game_map,
        floor_depth=1,
        rng=random.Random(1),
        registry=registry,
        min_distance=RUNE_SPAWN_MIN_DISTANCE,
        count=1,
    )[0]
    rune_pos = rune.components[Position]
    rune_dist = next(
        dist for x, y, dist in candidates if (x, y) == (rune_pos.x, rune_pos.y)
    )
    assert rune_dist >= MIN_PAIRWISE_SPREAD_BFS


def test_player_can_step_onto_rune_npc_cannot() -> None:
    from src.spawn import spawn_entity_by_id

    world = Registry()
    game_map = rune_placement_arena(width=45, height=10)
    registry = parse_floor_rune_registry(minimal_floor_runes_payload())
    rune = spawn_floor_rune(
        world,
        game_map,
        floor_depth=1,
        rng=random.Random(3),
        registry=registry,
        min_distance=3,
        min_pairwise=3,
        count=1,
    )[0]
    rune_pos = rune.components[Position]

    player = world[object()]
    player.tags.add(Player)
    player.tags.add(BlocksMovement)
    player.components[Position] = Position(rune_pos.x - 1, rune_pos.y)

    wolf = spawn_entity_by_id(world, "wolf", rune_pos.x - 2, rune_pos.y)

    assert can_move_to(world, game_map, player, player.components[Position], (1, 0))
    assert not can_move_to(world, game_map, wolf, wolf.components[Position], (1, 0))


def test_rune_has_blocks_movement_tag() -> None:
    world = Registry()
    game_map = rune_placement_arena()
    registry = parse_floor_rune_registry(minimal_floor_runes_payload())
    rune = spawn_floor_rune(
        world,
        game_map,
        floor_depth=1,
        rng=random.Random(5),
        registry=registry,
        min_distance=3,
        min_pairwise=3,
        count=1,
    )[0]
    assert BlocksMovement in rune.tags
    assert rune.components[FloorRune].rune_id


def test_bfs_path_distance_cardinal_only() -> None:
    game_map = rune_placement_arena(width=8, height=6)
    distances = bfs_path_distance_from(
        game_map,
        game_map.enter_xy,
        tile_filter=lambda x, y: game_map.tiles[y, x] == Tile.FLOOR,
        cardinal_only=True,
    )
    ex, ey = game_map.enter_xy
    assert distances[(ex + 1, ey)] == 1
    assert distances[(ex + 2, ey)] == 2


def test_no_eligible_runes_raises() -> None:
    world = Registry()
    game_map = rune_placement_arena()
    payload = minimal_floor_runes_payload(
        runes=[
            {
                "id": "deep_rune",
                "display_name": "deep",
                "glyph": "*",
                "fg": [1, 1, 1],
                "examine": "deep",
                "weight": 1,
                "min_depth": 50,
                "max_depth": 100,
                "effect": {"type": "max_hp", "amount": 1},
            }
        ]
    )
    registry = parse_floor_rune_registry(payload)
    with pytest.raises(RunePlacementError, match="no runes eligible"):
        spawn_floor_rune(
            world, game_map, floor_depth=1, registry=registry, min_distance=1, count=1
        )


def test_fixture_registry_from_tmp_path(tmp_path) -> None:
    path = tmp_path / "floor_runes.json"
    write_floor_runes(path, minimal_floor_runes_payload())
    registry = load_floor_rune_registry(path)
    assert registry.get("test_rune").glyph == "0"