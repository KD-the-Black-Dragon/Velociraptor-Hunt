"""PR2: stock NPC prefix content — structure and grants, not balance numbers."""

from __future__ import annotations

from src.data.npc_prefix_loader import (
    load_npc_prefix_registry,
    parse_npc_prefix_registry,
    reset_npc_prefix_registry_cache,
)

STOCK_PREFIX_IDS = frozenset(
    {
        "elite",
        "brute",
        "berserk",
        "veteran",
        "starving",
        "sniper",
        "bloated",
    }
)


def test_stock_catalog_has_all_prefix_ids() -> None:
    reset_npc_prefix_registry_cache()
    reg = load_npc_prefix_registry()
    assert STOCK_PREFIX_IDS <= set(reg.by_id())
    for prefix_id in STOCK_PREFIX_IDS:
        prefix = reg.get(prefix_id)
        assert prefix.weight > 0
        assert prefix.display_prefix.endswith(" ")


def test_stock_sniper_requires_range_n() -> None:
    reset_npc_prefix_registry_cache()
    sniper = load_npc_prefix_registry().get("sniper")
    assert sniper.requirements.ability_families == frozenset({"RangeN"})
    assert sniper.grant_abilities == ()


def test_stock_brute_and_bloated_grant_slow() -> None:
    reset_npc_prefix_registry_cache()
    reg = load_npc_prefix_registry()
    assert reg.get("brute").grant_abilities == ("Slow",)
    assert reg.get("bloated").grant_abilities == ("Slow",)


def test_stock_starving_grants_prefer_vore() -> None:
    reset_npc_prefix_registry_cache()
    assert load_npc_prefix_registry().get("starving").grant_abilities == (
        "PreferVore",
    )


def test_fixture_prefix_rows_parse() -> None:
    """Pinned minimal JSON — mechanics only, not live balance tuning."""
    raw = {
        "schema_version": 1,
        "prefixes": [
            {
                "id": "brute",
                "display_prefix": "Brute ",
                "apply_to_alignments": ["evil"],
                "min_depth": 1,
                "max_depth": 10,
                "weight": 1,
                "grant_abilities": ["Slow"],
                "stat_bonuses": {"min_damage": 1},
            },
            {
                "id": "sniper",
                "display_prefix": "Sniper ",
                "apply_to_alignments": ["evil"],
                "min_depth": 1,
                "max_depth": 10,
                "weight": 1,
                "requirements": {"ability_families": ["RangeN"]},
                "stat_bonuses": {"ranged_accuracy": 0.05},
            },
        ],
    }
    reg = parse_npc_prefix_registry(raw)
    assert reg.get("brute").grant_abilities == ("Slow",)
    assert reg.get("sniper").requirements.ability_families == frozenset({"RangeN"})