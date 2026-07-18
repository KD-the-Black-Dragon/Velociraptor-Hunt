from __future__ import annotations

from typing import Any

import attrs

from src.data.macguffin_registry import MacguffinDefinition


@attrs.define
class MacguffinDiscovery:
    """Run-level record of the most recently found macguffin."""

    macguffin_id: str = ""
    display_name: str = ""
    score: int = 0

    @property
    def active(self) -> bool:
        return bool(self.macguffin_id)

    def record(self, definition: MacguffinDefinition) -> None:
        self.macguffin_id = definition.id
        self.display_name = definition.display_name
        self.score = definition.score

    def reset(self) -> None:
        self.macguffin_id = ""
        self.display_name = ""
        self.score = 0


def encode_macguffin_discovery(discovery: MacguffinDiscovery) -> dict[str, Any]:
    if not discovery.active:
        return {}
    return {
        "macguffin_id": discovery.macguffin_id,
        "display_name": discovery.display_name,
        "score": discovery.score,
    }


def decode_macguffin_discovery(data: object) -> MacguffinDiscovery:
    if not isinstance(data, dict):
        return MacguffinDiscovery()
    macguffin_id = str(data.get("macguffin_id", ""))
    if not macguffin_id:
        return MacguffinDiscovery()
    return MacguffinDiscovery(
        macguffin_id=macguffin_id,
        display_name=str(data.get("display_name", "")),
        score=int(data.get("score", 0)),
    )