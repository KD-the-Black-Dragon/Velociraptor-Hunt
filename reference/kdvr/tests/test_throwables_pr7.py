"""PR7: stock throwable catalog, fox archer Range5, help bindings."""

from __future__ import annotations

from src.data.entity_loader import load_entity_registry, reset_entity_registry_cache
from src.data.item_loader import load_item_registry
from src.ui.help_overlay import HELP_LINES

CATALOG_IDS = (
    "rock",
    "brick",
    "dart",
    "throwing_knife",
    "throwing_axe",
    "shuriken",
    "javelin",
    "chakram",
    "ceramic_pot",
)


def test_throwable_catalog_loads_nine_entries() -> None:
    registry = load_item_registry()
    assert len(registry.throwables) == 9
    assert tuple(item.id for item in registry.throwables) == CATALOG_IDS


def test_rock_fg_is_light_brown() -> None:
    rock = load_item_registry().get_throwable("rock")
    assert rock.fg == (190, 150, 90)


def test_fox_archer_has_range5() -> None:
    reset_entity_registry_cache()
    fox = load_entity_registry().get("fox_archer")
    assert fox is not None
    assert "Range5" in fox.abilities


def test_help_lists_throw_bindings() -> None:
    text = "\n".join(HELP_LINES)
    assert "f - throw best throwable" in text
    assert "F - pick throwable to throw" in text