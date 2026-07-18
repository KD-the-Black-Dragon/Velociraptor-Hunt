"""Stock roster structure: expanded ids present; spider removed; rat id."""

from __future__ import annotations

from src.data.entity_loader import load_entity_registry, reset_entity_registry_cache


EXPECTED_CORE = {
    "slime",
    "tarantula",
    "fox_archer",
    "gnoll_mercenary",
    "roc",
    "owl_mage",
    "wyvern",
    "drake",
    "gryphon",
    "dragon",
    "rat",
    "bat",
    "wolf",
    "knight",
}


def test_stock_roster_loads_core_ids() -> None:
    reset_entity_registry_cache()
    reg = load_entity_registry()
    ids = {e.id for e in reg.entities}
    assert EXPECTED_CORE <= ids
    assert "cave_rat" not in ids
    assert "giant_spider" not in ids


def test_fox_archer_ranged_stronger_than_melee() -> None:
    reset_entity_registry_cache()
    fox = load_entity_registry().get("fox_archer")
    assert fox is not None
    assert fox.ranged_min_damage > fox.min_damage
    assert fox.ranged_max_damage > fox.max_damage


def test_gnoll_has_short_range() -> None:
    """Gnoll is a short-range generalist — ranged kit present (values may tune)."""
    reset_entity_registry_cache()
    gnoll = load_entity_registry().get("gnoll_mercenary")
    assert gnoll is not None
    assert "Range3" in gnoll.abilities
    assert gnoll.ranged_max_damage > 0


def test_early_rat_and_deep_dragon_present() -> None:
    """Sanity: rat exists as early vermin id; dragon exists as deep threat id.

    Does not pin live min/max depth numbers (balance-pass may retune).
    """
    reset_entity_registry_cache()
    reg = load_entity_registry()
    rat = reg.get("rat")
    dragon = reg.get("dragon")
    assert rat is not None and dragon is not None
    assert rat.spawn.weight > 0
    assert dragon.spawn.weight > 0


def test_rabbit_weight_zero_no_floor_spawn() -> None:
    reset_entity_registry_cache()
    rabbit = load_entity_registry().get("rabbit")
    assert rabbit is not None
    assert rabbit.spawn.weight == 0
