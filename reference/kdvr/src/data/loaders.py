from __future__ import annotations

import attrs

from src.data.entity_loader import load_entity_registry
from src.data.entity_registry import EntityRegistry
from src.data.item_loader import load_item_registry
from src.data.item_registry import ItemRegistry


@attrs.define(frozen=True)
class GameData:
    """Snapshot of loadable game data files."""

    entities: EntityRegistry
    items: ItemRegistry

    @property
    def warnings(self) -> tuple[str, ...]:
        return self.entities.warnings + self.items.warnings

    @property
    def entity_warnings(self) -> tuple[str, ...]:
        return self.entities.warnings


def load_game_data() -> GameData:
    entities = load_entity_registry()
    items = load_item_registry()
    return GameData(entities=entities, items=items)