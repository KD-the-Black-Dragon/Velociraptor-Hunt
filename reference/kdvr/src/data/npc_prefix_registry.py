"""NPC name-prefix definitions (Elite and future modifiers)."""

from __future__ import annotations

import attrs

from src.components import Alignment
from src.data.ability_parser import entity_has_ability_family
from src.data.entity_registry import EntityDefinition


@attrs.define(frozen=True)
class PrefixStatBonuses:
    max_hp: int = 0
    ac: int = 0
    evade: float = 0.0
    accuracy: float = 0.0
    ranged_accuracy: float = 0.0
    min_damage: int = 0
    max_damage: int = 0
    digestion_damage_per_tick: int = 0


@attrs.define(frozen=True)
class PrefixRequirements:
    """Entity-aware gates; empty ``ability_families`` imposes no ability requirement."""

    ability_families: frozenset[str] = frozenset()

    def matches(self, definition: EntityDefinition) -> bool:
        if not self.ability_families:
            return True
        return any(
            entity_has_ability_family(definition.abilities, family)
            for family in self.ability_families
        )


@attrs.define(frozen=True)
class NpcPrefixDefinition:
    id: str
    display_prefix: str
    apply_to_alignments: frozenset[Alignment]
    min_depth: int
    max_depth: int
    weight: int
    stat_bonuses: PrefixStatBonuses
    grant_abilities: tuple[str, ...] = ()
    requirements: PrefixRequirements = attrs.field(factory=PrefixRequirements)


@attrs.define(frozen=True)
class NpcPrefixRegistry:
    schema_version: int
    prefixes: tuple[NpcPrefixDefinition, ...]

    def by_id(self) -> dict[str, NpcPrefixDefinition]:
        return {prefix.id: prefix for prefix in self.prefixes}

    def get(self, prefix_id: str) -> NpcPrefixDefinition:
        return self.by_id()[prefix_id]

    def eligible(
        self,
        *,
        alignment: Alignment,
        floor_depth: int,
    ) -> tuple[NpcPrefixDefinition, ...]:
        return tuple(
            prefix
            for prefix in self.prefixes
            if alignment in prefix.apply_to_alignments
            and prefix.min_depth <= floor_depth <= prefix.max_depth
            and prefix.weight > 0
        )

    def eligible_for_entity(
        self,
        *,
        alignment: Alignment,
        floor_depth: int,
        definition: EntityDefinition,
    ) -> tuple[NpcPrefixDefinition, ...]:
        return tuple(
            prefix
            for prefix in self.eligible(alignment=alignment, floor_depth=floor_depth)
            if prefix.requirements.matches(definition)
        )