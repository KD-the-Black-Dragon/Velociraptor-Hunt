"""PR3: data-driven runes_per_floor (spawn + map feasibility)."""

from __future__ import annotations

import random
from pathlib import Path

from tcod.ecs import Registry

from src.components import FloorRune, Position
from src.constants import RUNES_PER_FLOOR
from src.data.floor_rune_loader import FloorRuneLoadError, parse_floor_rune_registry
from src.data.floor_rune_registry import FloorRuneRegistry, RuneEffect, FloorRuneDefinition
from src.map_gen import generate_dungeon, validate_rune_sites_feasible
from src.systems.floor_runes import (
    configured_runes_per_floor,
    spawn_floor_rune,
)


def _minimal_registry(*, runes_per_floor: int) -> FloorRuneRegistry:
    effect = RuneEffect(type="natural_ac", amount=1)
    definition = FloorRuneDefinition(
        id="t",
        display_name="test",
        glyph="0",
        fg=(1, 2, 3),
        examine="x",
        weight=1,
        min_depth=1,
        max_depth=1000,
        effect=effect,
    )
    return FloorRuneRegistry(
        schema_version=1,
        runes=(definition,),
        runes_per_floor=runes_per_floor,
    )


class TestLoader:
    def test_parse_runes_per_floor(self) -> None:
        raw = {
            "schema_version": 1,
            "runes_per_floor": 2,
            "runes": [
                {
                    "id": "t",
                    "display_name": "t",
                    "glyph": "0",
                    "fg": [1, 2, 3],
                    "examine": "x",
                    "weight": 1,
                    "min_depth": 1,
                    "max_depth": 10,
                    "effect": {"type": "natural_ac", "amount": 1},
                }
            ],
        }
        reg = parse_floor_rune_registry(raw)
        assert reg.runes_per_floor == 2

    def test_omitted_defaults_to_constant(self) -> None:
        raw = {
            "schema_version": 1,
            "runes": [
                {
                    "id": "t",
                    "display_name": "t",
                    "glyph": "0",
                    "fg": [1, 2, 3],
                    "examine": "x",
                    "weight": 1,
                    "min_depth": 1,
                    "max_depth": 10,
                    "effect": {"type": "natural_ac", "amount": 1},
                }
            ],
        }
        reg = parse_floor_rune_registry(raw)
        assert reg.runes_per_floor == RUNES_PER_FLOOR

    def test_zero_allowed(self) -> None:
        raw = {
            "schema_version": 1,
            "runes_per_floor": 0,
            "runes": [
                {
                    "id": "t",
                    "display_name": "t",
                    "glyph": "0",
                    "fg": [1, 2, 3],
                    "examine": "x",
                    "weight": 1,
                    "min_depth": 1,
                    "max_depth": 10,
                    "effect": {"type": "natural_ac", "amount": 1},
                }
            ],
        }
        reg = parse_floor_rune_registry(raw)
        assert reg.runes_per_floor == 0

    def test_negative_rejected(self) -> None:
        raw = {
            "schema_version": 1,
            "runes_per_floor": -1,
            "runes": [],
        }
        try:
            parse_floor_rune_registry(raw)
            raise AssertionError("expected error")
        except FloorRuneLoadError as exc:
            assert "runes_per_floor" in str(exc)

    def test_stock_file_has_three(self) -> None:
        from src.data.floor_rune_loader import load_floor_rune_registry
        from src.systems.floor_runes import reset_floor_rune_registry_cache

        reset_floor_rune_registry_cache()
        reg = load_floor_rune_registry()
        assert reg.runes_per_floor == 3
        assert configured_runes_per_floor(reg) == 3


class TestSpawnCount:
    def test_spawn_count_two(self) -> None:
        world = Registry()
        game_map = generate_dungeon(80, 45, seed=42, runes_per_floor=2)
        reg = _minimal_registry(runes_per_floor=2)
        placed = spawn_floor_rune(
            world, game_map, 1, rng=random.Random(1), registry=reg, count=2
        )
        assert len(placed) == 2
        positions = {
            (e.components[Position].x, e.components[Position].y) for e in placed
        }
        assert len(positions) == 2

    def test_spawn_count_zero(self) -> None:
        world = Registry()
        game_map = generate_dungeon(80, 45, seed=42, runes_per_floor=0)
        reg = _minimal_registry(runes_per_floor=0)
        placed = spawn_floor_rune(
            world, game_map, 1, rng=random.Random(1), registry=reg, count=0
        )
        assert placed == []
        assert not list(world.Q.all_of(components=[FloorRune]))

    def test_spawn_none_count_uses_registry(self) -> None:
        world = Registry()
        reg = _minimal_registry(runes_per_floor=1)
        game_map = generate_dungeon(80, 45, seed=7, runes_per_floor=1)
        placed = spawn_floor_rune(
            world, game_map, 1, rng=random.Random(2), registry=reg, count=None
        )
        assert len(placed) == 1


class TestMapFeasibilityAligns:
    def test_generate_accepts_zero_runes_budget(self) -> None:
        # Should not hang / always fail when only macguffins need spread sites
        game_map = generate_dungeon(80, 45, seed=99, runes_per_floor=0)
        assert game_map.width == 80

    def test_feasibility_count_matches_argument(self) -> None:
        game_map = generate_dungeon(80, 45, seed=11, runes_per_floor=3)
        assert validate_rune_sites_feasible(game_map, count=3) is True
