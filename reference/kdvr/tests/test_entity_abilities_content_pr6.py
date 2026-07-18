"""Stock species ability assignments (baseline balance-pass)."""

from __future__ import annotations

from src.components import MobilityType
from src.data.entity_loader import load_entity_registry, reset_entity_registry_cache


def _entity(entity_id: str):
    reset_entity_registry_cache()
    entity = load_entity_registry().get(entity_id)
    assert entity is not None
    return entity


def test_baseline_abilities_by_species() -> None:
    expected = {
        "rat": set(),
        "bat": {"Erratic", "Lifedrain"},
        "slime": {"Slow"},
        "wolf": set(),
        "shark": set(),
        "tarantula": {"NoChase"},
        "fox_archer": {"Range5", "NoChase"},
        "kobold": {"Hands", "Coward", "NoChase"},
        "gnoll_mercenary": {"Range3", "Hands"},
        "tunnel_slug": {"Slow"},
        "roc": set(),
        "owl_mage": {"Smite5", "NoChase"},
        "wyvern": {"Knockback"},
        "drake": {"Knockback"},
        "gryphon": {"Knockback"},
        "dragon": {"Range5"},
        "knight": set(),
        "rabbit": set(),
    }
    for eid, abilities in expected.items():
        assert set(_entity(eid).abilities) == abilities, eid


def test_stationary_tunnel_slug() -> None:
    assert _entity("tunnel_slug").mobility is MobilityType.STATIONARY


def test_wolf_ground_no_abilities() -> None:
    wolf = _entity("wolf")
    assert wolf.mobility is MobilityType.GROUND
    assert wolf.abilities == ()
