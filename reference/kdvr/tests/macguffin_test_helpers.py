"""Isolated macguffin placement fixtures — not live data/ balance."""

from __future__ import annotations

from src.data.macguffin_loader import parse_macguffin_registry
from src.data.macguffin_registry import MacguffinDefinition, MacguffinRegistry
from src.map_gen import GameMap, Tile


def macguffin_placement_arena(*, width: int = 140, height: int = 20) -> GameMap:
    """Long horizontal corridor for multi-object spread placement tests."""
    game_map = GameMap(width, height)
    game_map.tiles[:, :] = Tile.WALL
    mid_y = height // 2
    game_map.tiles[mid_y, 1 : width - 1] = Tile.FLOOR
    game_map.enter_xy = (2, mid_y)
    return game_map


def fixture_macguffin_registry(
    *,
    entries: list[dict] | None = None,
) -> MacguffinRegistry:
    """Pinned catalog for spawn/eligibility tests (not live data/macguffins.json)."""
    if entries is None:
        entries = [
            {
                "id": "early_relic",
                "display_name": "The Early Relic",
                "glyph": "/",
                "fg": [220, 220, 255],
                "examine": "Fixture early.",
                "min_depth": 1,
                "max_depth": 5,
                "score": 10,
            },
            {
                "id": "mid_relic",
                "display_name": "The Mid Relic",
                "glyph": "]",
                "fg": [200, 200, 100],
                "examine": "Fixture mid.",
                "min_depth": 3,
                "max_depth": 10,
                "score": 20,
            },
            {
                "id": "late_relic",
                "display_name": "The Late Relic",
                "glyph": '"',
                "fg": [100, 220, 100],
                "examine": "Fixture late.",
                "min_depth": 6,
                "max_depth": 15,
                "score": 30,
            },
        ]
    return parse_macguffin_registry({"schema_version": 1, "macguffins": entries})


def fixture_macguffin_definition(
    *,
    macguffin_id: str = "fixture_relic",
    min_depth: int = 1,
    max_depth: int = 10,
) -> MacguffinDefinition:
    return MacguffinDefinition(
        id=macguffin_id,
        display_name="The Fixture Relic",
        glyph="!",
        fg=(200, 200, 200),
        examine="Fixture definition.",
        min_depth=min_depth,
        max_depth=max_depth,
        score=10,
    )