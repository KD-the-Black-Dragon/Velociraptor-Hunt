"""PR0: ability token parser."""

from __future__ import annotations

from src.data.ability_parser import (
    RangeAbility,
    RangedVoreAbility,
    SmiteAbility,
    SummonAbility,
    collapse_range_tokens,
    collapse_ranged_vore_tokens,
    collapse_smite_tokens,
    parse_ability_token,
    parse_abilities,
)
from src.data.abilities import DOCUMENTED_ABILITIES, filter_known_abilities
from src.data.warnings import LoadWarnings


def test_parse_smite_tokens() -> None:
    assert parse_ability_token("Smite2") == SmiteAbility(distance=2)
    assert parse_ability_token("Smite9") == SmiteAbility(distance=9)
    assert parse_ability_token("Smite1") is None
    assert parse_ability_token("Smite10") is None
    assert parse_ability_token("Range2") == RangeAbility(distance=2)
    assert parse_ability_token("Range9") == RangeAbility(distance=9)


def test_range_tokens_implemented() -> None:
    assert "Range2" in DOCUMENTED_ABILITIES
    kept = filter_known_abilities("wolf", ["Range2"], LoadWarnings())
    assert kept == ("Range2",)


def test_collapse_range_tokens_keeps_max() -> None:
    assert collapse_range_tokens(["Range2", "Range5", "Coward"]) == (
        "Coward",
        "Range5",
    )


def test_parse_summon_token() -> None:
    parsed = parse_ability_token("Summon2 rabbit")
    assert isinstance(parsed, SummonAbility)
    assert parsed.count == 2
    assert parsed.entity_id == "rabbit"


def test_collapse_smite_tokens_keeps_max() -> None:
    assert collapse_smite_tokens(["Smite2", "Smite5", "Coward"]) == (
        "Coward",
        "Smite5",
    )


def test_parse_ranged_vore_token() -> None:
    assert parse_ability_token("RangedVore2") == RangedVoreAbility(distance=2)
    assert parse_ability_token("RangedVore9") == RangedVoreAbility(distance=9)


def test_collapse_ranged_vore_tokens_keeps_max() -> None:
    assert collapse_ranged_vore_tokens(["RangedVore2", "RangedVore5", "Coward"]) == (
        "Coward",
        "RangedVore5",
    )


def test_parse_abilities_round_trip() -> None:
    parsed = parse_abilities(["Smite2"])
    assert len(parsed) == 1
    assert parsed[0] == SmiteAbility(distance=2)