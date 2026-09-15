"""PR2: density-driven spawn mechanics and production call-site guard."""

from __future__ import annotations

import ast
import random
from pathlib import Path

from tcod.ecs import Registry

from src.components import DisplayName, Position
from src.data.entity_loader import parse_entity_registry
from src.map_gen import GameMap, Tile, water_positions
from src.spawn import (
    eligible_good_definitions,
    spawn_floor_population,
    valid_spawn_tiles,
)
from tests.spawn_test_helpers import expected_spawn_count, fixed_spawn_config
from tests.test_npc_data_pr1 import _minimal_entity


def _open_spawn_map(*, with_water: bool = False) -> GameMap:
    game_map = GameMap(60, 60)
    game_map.tiles[:, :] = Tile.FLOOR
    if with_water:
        game_map.tiles[10:20, 10:20] = Tile.DEEP_WATER
    game_map.enter_xy = (30, 30)
    return game_map


def test_spawn_floor_population_matches_effective_target() -> None:
    world = Registry()
    game_map = _open_spawn_map()
    config = fixed_spawn_config(density_pct=0.25, density_variance=0.0)
    expected = expected_spawn_count(game_map, 30, 30, floor_depth=1, config=config, rng_seed=42)
    spawned = spawn_floor_population(
        world,
        game_map,
        player_x=30,
        player_y=30,
        floor_depth=1,
        rng=random.Random(42),
        spawn_config=config,
    )
    assert len(spawned) == expected
    assert expected > 0


def test_density_count_unchanged_when_followers_brought_on_floor_without_goods() -> None:
    world = Registry()
    game_map = _open_spawn_map()
    config = fixed_spawn_config(density_pct=0.2, density_variance=0.0)
    baseline = expected_spawn_count(game_map, 30, 30, floor_depth=1, config=config, rng_seed=3)
    spawned = spawn_floor_population(
        world,
        game_map,
        player_x=30,
        player_y=30,
        floor_depth=1,
        rng=random.Random(3),
        spawn_config=config,
        good_followers_brought=2,
    )
    assert len(spawned) == baseline


def test_sharks_may_spawn_on_water_but_are_not_guaranteed() -> None:
    world = Registry()
    game_map = _open_spawn_map(with_water=True)
    config = fixed_spawn_config(density_pct=0.01, density_variance=0.0)
    spawned = spawn_floor_population(
        world,
        game_map,
        player_x=30,
        player_y=30,
        floor_depth=1,
        rng=random.Random(99),
        spawn_config=config,
    )
    for entity in spawned:
        if entity.components[DisplayName].name == "shark":
            pos = entity.components[Position]
            assert game_map.tiles[pos.y, pos.x] == Tile.DEEP_WATER


def test_no_sharks_without_water() -> None:
    world = Registry()
    game_map = _open_spawn_map()
    config = fixed_spawn_config(density_pct=0.5, density_variance=0.0)
    spawned = spawn_floor_population(
        world,
        game_map,
        player_x=30,
        player_y=30,
        floor_depth=1,
        rng=random.Random(0),
        spawn_config=config,
    )
    assert "shark" not in [e.components[DisplayName].name for e in spawned]


def test_eligible_good_definitions_lists_all_goods_with_weight() -> None:
    payload = {
        "schema_version": 1,
        "entities": [
            _minimal_entity(
                id="ally_a",
                display_name="ally a",
                alignment="good",
                spawn={"weight": 3, "min_depth": 1, "max_depth": 10, "terrain": "land"},
            ),
            _minimal_entity(
                id="ally_b",
                display_name="ally b",
                alignment="good",
                spawn={"weight": 4, "min_depth": 1, "max_depth": 10, "terrain": "land"},
            ),
            _minimal_entity(
                id="ally_zero",
                display_name="ally zero",
                alignment="good",
                spawn={"weight": 0, "min_depth": 1, "max_depth": 10, "terrain": "land"},
            ),
        ],
    }
    reg = parse_entity_registry(payload)
    game_map = _open_spawn_map()
    land, _water = valid_spawn_tiles(game_map, 30, 30)
    goods = eligible_good_definitions(
        reg,
        floor_depth=1,
        map_has_water=False,
        land_cands=land,
        water_place_pool=[],
    )
    assert {d.id for d in goods} == {"ally_a", "ally_b"}


def test_spawn_floor_population_only_called_from_engine_in_src() -> None:
    """Production lifecycle: spawn_floor_population only from engine floor path."""
    project_root = Path(__file__).resolve().parent.parent
    src_root = project_root / "src"
    # Floor lifecycle lives in engine_floor (PR4); engine.py delegates.
    allowed_files = {
        src_root / "engine.py",
        src_root / "engine_floor.py",
    }
    spawn_def = src_root / "spawn.py"

    for path in src_root.rglob("*.py"):
        if path == spawn_def:
            continue
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = None
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name != "spawn_floor_population":
                continue
            assert path in allowed_files, (
                f"spawn_floor_population called from {path.relative_to(project_root)}; "
                "only engine.py / engine_floor.py may call it in src/"
            )