from __future__ import annotations

import attrs


@attrs.define(frozen=True)
class NamesRegistry:
    schema_version: int
    names: dict[str, tuple[str, ...]]

    def pool_for(self, entity_id: str) -> tuple[str, ...] | None:
        pool = self.names.get(entity_id)
        if pool is None or not pool:
            return None
        return pool