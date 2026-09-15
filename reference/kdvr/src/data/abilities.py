from __future__ import annotations

from collections.abc import Iterable

from src.data.ability_parser import (
    ParsedAbility,
    RangeAbility,
    RangedVoreAbility,
    SmiteAbility,
    SummonAbility,
    FixedAbility,
    collapse_range_tokens,
    collapse_ranged_vore_tokens,
    collapse_smite_tokens,
    parse_ability_token,
    parse_abilities,
)
from src.data.warnings import LoadWarnings

DOCUMENTED_ABILITIES: frozenset[str] = frozenset(
    {f"Smite{n}" for n in range(2, 10)}
    | {f"Range{n}" for n in range(2, 10)}
    | {f"RangedVore{n}" for n in range(2, 10)}
    | {
        "Fast",
        "Slow",
        "Erratic",
        "Coward",
        "Supercoward",
        "Knockback",
        "Lifedrain",
        "PreferVore",
        "Wander",
        "NoChase",
        "Hands",
    }
)

IMPLEMENTED_KINDS: frozenset[type[ParsedAbility]] = frozenset(
    {SmiteAbility, RangeAbility, RangedVoreAbility, SummonAbility}
)

IMPLEMENTED_FIXED_IDS: frozenset[str] = frozenset(
    {
        "Coward",
        "Supercoward",
        "Erratic",
        "Slow",
        "Fast",
        "Knockback",
        "Lifedrain",
        "PreferVore",
        "Wander",
        "NoChase",
        "Hands",
    }
)


def _collapse_ability_tokens(abilities: list[str]) -> tuple[str, ...]:
    smite_collapsed = collapse_smite_tokens(abilities)
    range_collapsed = collapse_range_tokens(list(smite_collapsed))
    return collapse_ranged_vore_tokens(list(range_collapsed))


def filter_known_abilities(
    entity_id: str,
    abilities: Iterable[str],
    warnings: LoadWarnings,
) -> tuple[str, ...]:
    """Parse tokens, collapse SmiteN/RangeN duplicates, keep implemented kinds only."""
    raw_list = list(abilities)
    collapsed = _collapse_ability_tokens(raw_list)
    if len(collapsed) < len(raw_list):
        warnings.warn_once(
            f"ability:token-collapse:{entity_id}",
            f"Duplicate SmiteN, RangeN, or RangedVoreN tokens on '{entity_id}' collapsed to max range",
        )

    kept: list[str] = []
    for ability in collapsed:
        parsed = parse_ability_token(ability)
        if parsed is None:
            if ability in DOCUMENTED_ABILITIES or _SUMMON_PREFIX(ability):
                warnings.warn_unimplemented_ability(ability, entity_id)
            else:
                warnings.warn_unknown_ability(ability, entity_id)
            continue
        if isinstance(parsed, FixedAbility):
            if parsed.ability_id not in IMPLEMENTED_FIXED_IDS:
                warnings.warn_unimplemented_ability(ability, entity_id)
                continue
        elif type(parsed) not in IMPLEMENTED_KINDS:
            warnings.warn_unimplemented_ability(ability, entity_id)
            continue
        kept.append(ability)
    return tuple(kept)


def _SUMMON_PREFIX(ability: str) -> bool:
    return ability.startswith("Summon")