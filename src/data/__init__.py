from __future__ import annotations

from src.data.entity_loader import load_entity_registry
from src.data.entity_registry import EntityDefinition, EntityRegistry
from src.data.loaders import load_game_data
from src.data.loaders import GameData

__all__ = [
    "EntityDefinition",
    "EntityRegistry",
    "GameData",
    "load_entity_registry",
    "load_game_data",
]