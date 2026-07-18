from __future__ import annotations

import re
from collections.abc import Iterable
from typing import TypeAlias

import attrs

_SMITE_RE = re.compile(r"^Smite([2-9])$")
_RANGE_RE = re.compile(r"^Range([2-9])$")
_RANGED_VORE_RE = re.compile(r"^RangedVore([2-9])$")
_SUMMON_RE = re.compile(r"^Summon(\d+)\s+(\S+)$")

ABILITY_FAMILY_TOKENS: frozenset[str] = frozenset({"RangeN", "SmiteN", "RangedVoreN"})

FIXED_ABILITY_IDS: frozenset[str] = frozenset(
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


@attrs.define(frozen=True)
class SmiteAbility:
    distance: int


@attrs.define(frozen=True)
class RangeAbility:
    distance: int


@attrs.define(frozen=True)
class RangedVoreAbility:
    distance: int


@attrs.define(frozen=True)
class SummonAbility:
    count: int
    entity_id: str


@attrs.define(frozen=True)
class FixedAbility:
    ability_id: str


ParsedAbility: TypeAlias = (
    SmiteAbility | RangeAbility | RangedVoreAbility | SummonAbility | FixedAbility
)


def parse_ability_token(raw: str) -> ParsedAbility | None:
    smite_match = _SMITE_RE.match(raw)
    if smite_match is not None:
        return SmiteAbility(distance=int(smite_match.group(1)))

    range_match = _RANGE_RE.match(raw)
    if range_match is not None:
        return RangeAbility(distance=int(range_match.group(1)))

    ranged_vore_match = _RANGED_VORE_RE.match(raw)
    if ranged_vore_match is not None:
        return RangedVoreAbility(distance=int(ranged_vore_match.group(1)))

    summon_match = _SUMMON_RE.match(raw)
    if summon_match is not None:
        return SummonAbility(count=int(summon_match.group(1)), entity_id=summon_match.group(2))

    if raw in FIXED_ABILITY_IDS:
        return FixedAbility(ability_id=raw)

    return None


def collapse_smite_tokens(abilities: list[str]) -> tuple[str, ...]:
    """Collapse duplicate SmiteN tokens to a single token with max N."""
    max_distance: int | None = None
    kept: list[str] = []
    for ability in abilities:
        match = _SMITE_RE.match(ability)
        if match is not None:
            distance = int(match.group(1))
            max_distance = distance if max_distance is None else max(max_distance, distance)
            continue
        kept.append(ability)
    if max_distance is not None:
        kept.append(f"Smite{max_distance}")
    return tuple(kept)


def collapse_range_tokens(abilities: list[str]) -> tuple[str, ...]:
    """Collapse duplicate RangeN tokens to a single token with max N."""
    max_distance: int | None = None
    kept: list[str] = []
    for ability in abilities:
        match = _RANGE_RE.match(ability)
        if match is not None:
            distance = int(match.group(1))
            max_distance = distance if max_distance is None else max(max_distance, distance)
            continue
        kept.append(ability)
    if max_distance is not None:
        kept.append(f"Range{max_distance}")
    return tuple(kept)


def collapse_ranged_vore_tokens(abilities: list[str]) -> tuple[str, ...]:
    """Collapse duplicate RangedVoreN tokens to a single token with max N."""
    max_distance: int | None = None
    kept: list[str] = []
    for ability in abilities:
        match = _RANGED_VORE_RE.match(ability)
        if match is not None:
            distance = int(match.group(1))
            max_distance = distance if max_distance is None else max(max_distance, distance)
            continue
        kept.append(ability)
    if max_distance is not None:
        kept.append(f"RangedVore{max_distance}")
    return tuple(kept)


def parse_abilities(raw: Iterable[str]) -> tuple[ParsedAbility, ...]:
    parsed: list[ParsedAbility] = []
    for token in raw:
        ability = parse_ability_token(token)
        if ability is not None:
            parsed.append(ability)
    return tuple(parsed)


def collapse_ability_tokens(abilities: Iterable[str]) -> tuple[str, ...]:
    """Collapse SmiteN, RangeN, and RangedVoreN families to max N."""
    smite_collapsed = collapse_smite_tokens(list(abilities))
    range_collapsed = collapse_range_tokens(list(smite_collapsed))
    return collapse_ranged_vore_tokens(list(range_collapsed))


def collapse_and_parse_abilities(abilities: Iterable[str]) -> tuple[ParsedAbility, ...]:
    return parse_abilities(collapse_ability_tokens(abilities))


def entity_has_ability_family(abilities: Iterable[str], family: str) -> bool:
    """True when ``family`` is RangeN/SmiteN/RangedVoreN or an exact fixed ability id."""
    if family == "RangeN":
        return any(_RANGE_RE.match(token) for token in abilities)
    if family == "SmiteN":
        return any(_SMITE_RE.match(token) for token in abilities)
    if family == "RangedVoreN":
        return any(_RANGED_VORE_RE.match(token) for token in abilities)
    if family in FIXED_ABILITY_IDS:
        return family in abilities
    return False


def ability_kind(ability: ParsedAbility) -> type[ParsedAbility]:
    return type(ability)