from __future__ import annotations

import attrs


@attrs.define(frozen=True)
class MacguffinDefinition:
    id: str
    display_name: str
    glyph: str
    fg: tuple[int, int, int]
    examine: str
    min_depth: int
    max_depth: int
    score: int


@attrs.define(frozen=True)
class MacguffinRegistry:
    schema_version: int
    macguffins: tuple[MacguffinDefinition, ...]

    def get(self, macguffin_id: str) -> MacguffinDefinition:
        for macguffin in self.macguffins:
            if macguffin.id == macguffin_id:
                return macguffin
        raise KeyError(macguffin_id)

    def eligible_at_depth(self, floor_depth: int) -> tuple[MacguffinDefinition, ...]:
        return tuple(
            macguffin
            for macguffin in self.macguffins
            if macguffin.min_depth <= floor_depth <= macguffin.max_depth
        )