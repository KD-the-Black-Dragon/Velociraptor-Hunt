"""PR1: dungeon_spawn.json loader and target NPC count API."""

from __future__ import annotations

import json
import random
import statistics
from pathlib import Path

import pytest

from src.components import MobilityType
from src.constants import MAP_HEIGHT, MAP_WIDTH, MAX_ROOMS, ROOM_MAX_SIZE, ROOM_MIN_SIZE
from src.data.dungeon_spawn_config import compute_target_npc_count
from src.data.dungeon_spawn_loader import (
    DUNGEON_SPAWN_PATH,
    DungeonSpawnLoadError,
    load_dungeon_spawn_config,
    parse_dungeon_spawn_config,
)
from src.map_gen import generate_dungeon, water_positions
from src.spawn import _candidate_tiles, _water_candidate_tiles


def _minimal_config(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "schema_version": 1,
        "defaults": {
            "density_pct": 0.02,
            "density_variance": 0.25,
            "min_npcs": 0,
            "max_npcs": 120,
        },
        "depth_bands": [
            {"min_depth": 1, "max_depth": 4, "density_pct": 0.012, "density_variance": 0.35},
        ],
    }
    base.update(overrides)
    return base


def _valid_spawn_tile_count(game_map) -> int:
    enter_x, enter_y = game_map.enter_xy
    land = _candidate_tiles(game_map, enter_x, enter_y, mobility_kind=MobilityType.GROUND)
    water = _water_candidate_tiles(game_map, enter_x, enter_y)
    return len(land) + len(water)


def test_load_default_dungeon_spawn_json_smoke() -> None:
    """Live file must parse; density/min/max are free to retune."""
    config = load_dungeon_spawn_config(DUNGEON_SPAWN_PATH)
    assert config.schema_version == 1
    assert config.defaults.density_pct > 0
    assert len(config.depth_bands) >= 1
    band = config.resolve_band(1)
    assert band.density_pct > 0
    assert band.max_npcs >= band.min_npcs


def test_band_inherits_omitted_fields_from_defaults() -> None:
    raw = _minimal_config(
        depth_bands=[
            {"min_depth": 1, "max_depth": 10, "density_pct": 0.05},
        ],
    )
    config = parse_dungeon_spawn_config(raw)
    band = config.resolve_band(3)
    assert band.density_pct == 0.05
    assert band.density_variance == 0.25
    assert band.max_npcs == 120


def test_resolve_band_falls_back_to_defaults() -> None:
    raw = _minimal_config(depth_bands=[])
    config = parse_dungeon_spawn_config(raw)
    band = config.resolve_band(99)
    assert band.density_pct == config.defaults.density_pct
    assert band.density_variance == config.defaults.density_variance


def test_overlapping_depth_bands_rejected() -> None:
    raw = _minimal_config(
        depth_bands=[
            {"min_depth": 1, "max_depth": 10, "density_pct": 0.01},
            {"min_depth": 5, "max_depth": 15, "density_pct": 0.02},
        ],
    )
    with pytest.raises(DungeonSpawnLoadError, match="overlap"):
        parse_dungeon_spawn_config(raw)


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("density_pct", -0.1, "density_pct"),
        ("density_variance", 1.0, "density_variance"),
        ("min_npcs", -1, "min_npcs"),
        ("max_npcs", 2, "max_npcs"),
    ],
)
def test_invalid_defaults_rejected(field: str, value: object, match: str) -> None:
    defaults = {
        "density_pct": 0.02,
        "density_variance": 0.25,
        "min_npcs": 0,
        "max_npcs": 120,
    }
    defaults[field] = value
    if field == "max_npcs" and value == 2:
        defaults["min_npcs"] = 5
    raw = _minimal_config(defaults=defaults)
    with pytest.raises(DungeonSpawnLoadError, match=match):
        parse_dungeon_spawn_config(raw)


def test_compute_target_npc_count_respects_variance_and_clamps() -> None:
    config = parse_dungeon_spawn_config(_minimal_config())
    rng = random.Random(0)
    target = compute_target_npc_count(1000, floor_depth=1, config=config, rng=rng)
    assert 0 < target <= 1000
    assert target <= 120

    zero_tiles = compute_target_npc_count(0, floor_depth=1, config=config, rng=rng)
    assert zero_tiles == 0


def test_compute_target_npc_count_deterministic_with_seed() -> None:
    config = parse_dungeon_spawn_config(_minimal_config())
    first = compute_target_npc_count(800, floor_depth=1, config=config, rng=random.Random(42))
    second = compute_target_npc_count(800, floor_depth=1, config=config, rng=random.Random(42))
    assert first == second
    assert first > 0


def test_valid_spawn_tile_distribution() -> None:
    """Stock maps yield enough walkable tiles; spawn math stays within tile budget."""
    counts: list[int] = []
    water_map_count = 0
    for seed in range(50):
        game_map = generate_dungeon(
            MAP_WIDTH,
            MAP_HEIGHT,
            max_rooms=MAX_ROOMS,
            room_min_size=ROOM_MIN_SIZE,
            room_max_size=ROOM_MAX_SIZE,
            seed=seed,
        )
        counts.append(_valid_spawn_tile_count(game_map))
        if water_positions(game_map):
            water_map_count += 1

    median_tiles = int(statistics.median(counts))
    # Use inline fixture config — not live data/dungeon_spawn.json tuning values.
    config = parse_dungeon_spawn_config(_minimal_config())
    band = config.resolve_band(1)
    nominal_at_median = round(median_tiles * band.density_pct)

    print(
        f"spawn_tile_distribution: median={median_tiles} "
        f"min={min(counts)} max={max(counts)} "
        f"water_floors={water_map_count}/50 "
        f"fixture_nominal_target~{nominal_at_median}"
    )

    assert median_tiles > 100
    assert 0 < nominal_at_median <= median_tiles


def test_parse_from_tmp_path(tmp_path: Path) -> None:
    path = tmp_path / "dungeon_spawn.json"
    path.write_text(json.dumps(_minimal_config()), encoding="utf-8")
    config = load_dungeon_spawn_config(path)
    assert config.schema_version == 1