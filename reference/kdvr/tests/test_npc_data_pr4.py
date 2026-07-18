"""PR 4: terrain, depth, and good-follower spawn gates."""

from __future__ import annotations

import random

from tcod.ecs import Registry

from src.components import Alignment, DisplayName, MobilityType, Position
from src.data.entity_loader import load_entity_registry, parse_entity_registry
from src.engine import GameEngine
from src.map_gen import GameMap, Tile
from src.spawn import good_aligned_weight_at_depth, spawn_floor_population
from src.systems.ai import spawn_test_npc
from src.systems.fov import update_fov
from src.systems.movement import entity_mobility
from tests.spawn_test_helpers import expected_spawn_count, fixed_spawn_config
from tests.test_dungeon_pr3 import _good_npcs, _place_player_on_stairs, _press_descend
from tests.test_npc_data_pr1 import _minimal_entity


def _open_spawn_map(*, with_water: bool = False) -> GameMap:
    game_map = GameMap(60, 60)
    game_map.tiles[:, :] = Tile.FLOOR
    if with_water:
        game_map.tiles[10:20, 10:20] = Tile.DEEP_WATER
    game_map.enter_xy = (30, 30)
    return game_map


def test_sharks_only_on_water_tiles() -> None:
    world = Registry()
    game_map = _open_spawn_map(with_water=True)
    config = fixed_spawn_config(density_pct=0.3, density_variance=0.0)
    spawned = spawn_floor_population(
        world,
        game_map,
        player_x=30,
        player_y=30,
        floor_depth=1,
        rng=random.Random(11),
        spawn_config=config,
    )
    sharks = [entity for entity in spawned if entity.components[DisplayName].name == "shark"]
    for shark in sharks:
        pos = shark.components[Position]
        assert game_map.tiles[pos.y, pos.x] == Tile.DEEP_WATER
        assert entity_mobility(shark) == MobilityType.AQUATIC


def test_good_follower_reduction_uses_effective_target() -> None:
    game_map = _open_spawn_map()
    config = fixed_spawn_config(density_pct=0.2, density_variance=0.0)
    baseline = expected_spawn_count(game_map, 30, 30, floor_depth=1, config=config, rng_seed=5)
    reg = load_entity_registry()
    cap = good_aligned_weight_at_depth(reg, floor_depth=1, map_has_water=False)
    reduction = min(2, cap)
    world = Registry()
    spawned = spawn_floor_population(
        world,
        game_map,
        player_x=30,
        player_y=30,
        floor_depth=1,
        rng=random.Random(5),
        spawn_config=config,
        good_follower_reduction=reduction,
    )
    assert len(spawned) == max(0, baseline - reduction)


def test_depth_gates_change_spawned_species() -> None:
    payload = {
        "schema_version": 1,
        "entities": [
            _minimal_entity(
                id="wolf",
                display_name="wolf",
                alignment="evil",
                spawn={"weight": 1, "min_depth": 1, "max_depth": 1, "terrain": "land"},
            ),
            _minimal_entity(
                id="deep_only",
                display_name="deep only",
                alignment="evil",
                spawn={"weight": 1, "min_depth": 2, "max_depth": 100, "terrain": "land"},
            ),
        ],
    }
    reg = parse_entity_registry(payload)
    game_map = _open_spawn_map()
    shallow_config = fixed_spawn_config(density_pct=1.0, density_variance=0.0, max_npcs=1)
    world = Registry()
    spawn_floor_population(
        world,
        game_map,
        30,
        30,
        floor_depth=1,
        rng=random.Random(0),
        registry=reg,
        spawn_config=shallow_config,
    )
    assert [entity.components[DisplayName].name for entity in world.Q.all_of(components=[DisplayName])] == [
        "wolf"
    ]
    deep_only_config = fixed_spawn_config(density_pct=1.0, density_variance=0.0, max_npcs=1)
    spawn_floor_population(
        world,
        game_map,
        30,
        30,
        floor_depth=2,
        rng=random.Random(0),
        registry=reg,
        spawn_config=deep_only_config,
    )
    names = sorted(
        entity.components[DisplayName].name for entity in world.Q.all_of(components=[DisplayName])
    )
    assert names == ["deep only", "wolf"]


def test_descend_with_follower_keeps_good_ally_on_new_floor() -> None:
    from src.components import AI
    from tests.map_test_helpers import isolate_other_ais

    engine = GameEngine()
    engine.new_game(seed=31)
    isolate_other_ais(engine)
    player = engine.player
    assert player is not None
    player_pos = player.components[Position]
    spawn_test_npc(
        engine.world,
        x=player_pos.x + 1,
        y=player_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    update_fov(engine.game_map, player_pos.x, player_pos.y)
    _place_player_on_stairs(engine)
    _press_descend(engine)
    assert len(_good_npcs(engine)) >= 1
    assert len(list(engine.world.Q.all_of(components=[AI]))) > 0