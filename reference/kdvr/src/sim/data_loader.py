"""Load stock ``data/`` for balance simulation (mods disabled)."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from src.constants import DATA_DIR
from src.data.depth_scaling_loader import (
    DEPTH_SCALING_PATH,
    load_depth_scaling_config,
    reset_depth_scaling_cache,
)
from src.data.dungeon_spawn_loader import (
    DUNGEON_SPAWN_PATH,
    load_dungeon_spawn_config,
)
from src.data.entity_loader import (
    ENTITIES_PATH,
    load_entity_registry,
    reset_entity_registry_cache,
)
from src.data.floor_rune_loader import FLOOR_RUNES_PATH, load_floor_rune_registry
from src.data.item_loaders import (
    ARMOR_PATH,
    POTIONS_PATH,
    THROWABLES_PATH,
    WANDS_PATH,
    WEAPONS_PATH,
)
from src.data.item_loader import load_item_registry
from src.data.macguffin_loader import MACGUFFINS_PATH, load_macguffin_registry
from src.data.names_loader import NAMES_PATH, load_names_registry, reset_names_registry
from src.data.npc_prefix_loader import (
    NPC_PREFIXES_PATH,
    load_npc_prefix_registry,
    reset_npc_prefix_registry_cache,
)
from src.data.rescue_gratitude_loader import (
    RESCUE_GRATITUDE_PATH,
    load_rescue_gratitude_registry,
    reset_rescue_gratitude_registry,
)
from src.spawn import reset_spawn_config_cache
from src.systems.floor_runes import reset_floor_rune_registry_cache
from src.systems.inventory import reset_item_registry_cache
from src.systems.macguffins import reset_macguffin_registry_cache

_T = TypeVar("_T")

_FINGERPRINT_FILES: tuple[str, ...] = (
    "entities.json",
    "depth_scaling.json",
    "dungeon_spawn.json",
    "floor_runes.json",
    "npc_prefixes.json",
    "weapons.json",
    "armor.json",
    "potions.json",
    "wands.json",
    "throwables.json",
    "macguffins.json",
    "names.json",
    "rescue_gratitude.json",
)


def data_fingerprint(data_dir: Path = DATA_DIR) -> str:
    """SHA-256 of stock data file contents (for comparison validity)."""
    digest = hashlib.sha256()
    for name in _FINGERPRINT_FILES:
        path = data_dir / name
        digest.update(name.encode("utf-8"))
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()


def _patch_stock_loader(
    module: Any,
    attr: str,
    stock_value: _T,
) -> None:
    """Route default-path loads to pre-parsed stock data."""
    original: Callable[..., _T] = getattr(module, attr)

    def _loader(path: Path | None = None, **kwargs: Any) -> _T:
        if path is None and kwargs.get("mods_root") is None:
            return stock_value
        return original(path, **kwargs)

    setattr(module, attr, _loader)


def install_stock_game_data() -> str:
    """Install stock ``data/`` caches (no enabled mods). Returns fingerprint."""
    reset_entity_registry_cache()
    reset_item_registry_cache()
    reset_names_registry()
    reset_rescue_gratitude_registry()
    reset_depth_scaling_cache()
    reset_npc_prefix_registry_cache()
    reset_floor_rune_registry_cache()
    reset_macguffin_registry_cache()
    reset_spawn_config_cache()

    entities = load_entity_registry(ENTITIES_PATH)
    import src.data.entity_loader as entity_loader_mod

    entity_loader_mod._default_registry = entities

    items = load_item_registry(
        weapons_path=WEAPONS_PATH,
        armor_path=ARMOR_PATH,
        potions_path=POTIONS_PATH,
        wands_path=WANDS_PATH,
        throwables_path=THROWABLES_PATH,
    )
    import src.systems.inventory as inventory_mod

    inventory_mod._ITEM_REGISTRY = items

    names = load_names_registry(NAMES_PATH)
    import src.data.names_loader as names_mod

    names_mod._names_registry = names

    gratitude = load_rescue_gratitude_registry(RESCUE_GRATITUDE_PATH)
    import src.data.rescue_gratitude_loader as gratitude_mod

    gratitude_mod._rescue_gratitude_registry = gratitude

    stock_depth = load_depth_scaling_config(path=DEPTH_SCALING_PATH)
    import src.data.depth_scaling_loader as depth_mod

    _patch_stock_loader(depth_mod, "load_depth_scaling_config", stock_depth)
    reset_depth_scaling_cache()

    stock_spawn = load_dungeon_spawn_config(path=DUNGEON_SPAWN_PATH)
    import src.data.dungeon_spawn_loader as spawn_mod

    _patch_stock_loader(spawn_mod, "load_dungeon_spawn_config", stock_spawn)
    reset_spawn_config_cache()

    stock_runes = load_floor_rune_registry(path=FLOOR_RUNES_PATH)
    import src.data.floor_rune_loader as rune_mod

    _patch_stock_loader(rune_mod, "load_floor_rune_registry", stock_runes)
    reset_floor_rune_registry_cache()

    stock_macguffins = load_macguffin_registry(path=MACGUFFINS_PATH)
    import src.data.macguffin_loader as mac_mod

    _patch_stock_loader(mac_mod, "load_macguffin_registry", stock_macguffins)
    reset_macguffin_registry_cache()

    stock_prefixes = load_npc_prefix_registry(path=NPC_PREFIXES_PATH)
    import src.data.npc_prefix_loader as prefix_mod

    _patch_stock_loader(prefix_mod, "load_npc_prefix_registry", stock_prefixes)
    reset_npc_prefix_registry_cache()

    return data_fingerprint()