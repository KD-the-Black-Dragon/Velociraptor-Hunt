"""Invalidate and reload cached game data after mod enable/order changes."""

from __future__ import annotations

from pathlib import Path

def reload_game_data_caches() -> None:
    """Drop in-memory registries so the next load re-reads core + mods."""
    from src.data.entity_loader import reset_entity_registry_cache
    from src.data.names_loader import reset_names_registry
    from src.data.rescue_gratitude_loader import reset_rescue_gratitude_registry
    from src.systems.inventory import reset_item_registry_cache

    reset_entity_registry_cache()
    reset_item_registry_cache()
    reset_names_registry()
    reset_rescue_gratitude_registry()


def reload_all_game_data(
    *,
    mods_root: Path | None = None,
    report: bool = True,
) -> None:
    """Clear caches and reload all moddable JSON domains (one error report)."""
    from src.mods.pipeline import load_all_layered

    reload_game_data_caches()
    load_all_layered(mods_root=mods_root, report=report)
