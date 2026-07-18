"""Isolated floor rune JSON fixtures for mechanics tests — not live data/ balance."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.data.floor_rune_loader import load_floor_rune_registry
from src.data.floor_rune_registry import FloorRuneRegistry
from src.map_gen import GameMap, Tile


def write_floor_runes(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def load_fixture_registry(path: Path) -> FloorRuneRegistry:
    return load_floor_rune_registry(path)


def _minimal_rune(
    rune_id: str,
    *,
    glyph: str = "0",
    weight: int = 1,
    min_depth: int = 1,
    max_depth: int = 1000,
    effect_type: str = "max_hp",
    amount: int = 5,
) -> dict[str, Any]:
    return {
        "id": rune_id,
        "display_name": rune_id.replace("_", " "),
        "glyph": glyph,
        "fg": [100, 200, 100],
        "examine": f"Test rune {rune_id}.",
        "weight": weight,
        "min_depth": min_depth,
        "max_depth": max_depth,
        "effect": {"type": effect_type, "amount": amount},
    }


def minimal_floor_runes_payload(**overrides: object) -> dict[str, Any]:
    base: dict[str, Any] = {
        "schema_version": 1,
        "runes": [_minimal_rune("test_rune")],
    }
    base.update(overrides)
    return base


def rune_placement_arena(*, width: int = 40, height: int = 20) -> GameMap:
    """Horizontal corridor for path-distance placement tests."""
    game_map = GameMap(width, height)
    game_map.tiles[:, :] = Tile.WALL
    mid_y = height // 2
    game_map.tiles[mid_y, 1 : width - 1] = Tile.FLOOR
    game_map.enter_xy = (2, mid_y)
    return game_map