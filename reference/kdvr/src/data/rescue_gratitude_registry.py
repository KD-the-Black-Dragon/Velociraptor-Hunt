from __future__ import annotations

import attrs


@attrs.define(frozen=True)
class RescueGratitudeRegistry:
    schema_version: int
    lines: tuple[str, ...]