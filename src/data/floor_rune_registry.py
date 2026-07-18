from __future__ import annotations

import attrs


@attrs.define(frozen=True)
class RuneEffect:
    type: str
    amount: float | int | None = None
    accuracy: float | None = None
    min_damage: int | None = None
    max_damage: int | None = None
    # Piece / threshold progression (default 1 = grant full bonus immediately).
    pieces_per_bonus: int = 1
    pieces_granted: int = 1


@attrs.define(frozen=True)
class FloorRuneDefinition:
    id: str
    display_name: str
    glyph: str
    fg: tuple[int, int, int]
    examine: str
    weight: int
    min_depth: int
    max_depth: int
    effect: RuneEffect


@attrs.define(frozen=True)
class FloorRuneRegistry:
    schema_version: int
    runes: tuple[FloorRuneDefinition, ...]
    # How many runes to place per floor (spawn + map feasibility). ≥ 0.
    runes_per_floor: int = 3

    def get(self, rune_id: str) -> FloorRuneDefinition:
        for rune in self.runes:
            if rune.id == rune_id:
                return rune
        raise KeyError(rune_id)

    def eligible_at_depth(self, floor_depth: int) -> tuple[FloorRuneDefinition, ...]:
        return tuple(
            rune
            for rune in self.runes
            if rune.min_depth <= floor_depth <= rune.max_depth
        )