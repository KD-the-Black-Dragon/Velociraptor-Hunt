from __future__ import annotations

import attrs

from src.components import Alignment, MobilityType
from src.log_categories import MessageCategory


@attrs.define(frozen=True)
class SpawnConfig:
    weight: float
    min_depth: int
    max_depth: int
    terrain: str = "land"
    # Capability set (OV/CV/AV); empty = unrestricted (missing / null / [] / junk-only).
    # Spawn: eligible when empty or intersects run prefs (OR).
    requires_vore_types: frozenset[str] = frozenset()


@attrs.define(frozen=True)
class VoreNarrativeVariant:
    """One full vore narrative option (attempt lines + success phase lines)."""

    attempt: tuple[str, ...]
    success: tuple[str, ...]


@attrs.define(frozen=True)
class EntityDefinition:
    id: str
    display_name: str
    glyph: str
    fg: tuple[int, int, int]
    alignment: Alignment
    mobility: MobilityType
    max_hp: int
    evade: float
    ac: int
    accuracy: float
    min_damage: int
    max_damage: int
    ranged_accuracy: float
    ranged_min_damage: int
    ranged_max_damage: int
    spawn: SpawnConfig
    examine: str | None = None
    proper_name: str | None = None
    spawn_requires_water: bool = False
    digestion_damage_per_tick: int | None = None
    digest_time: int | None = None
    experience_points: int | None = None
    vore_narratives: dict[str, tuple[VoreNarrativeVariant, ...]] | None = None
    digestion_complete: dict[str, tuple[str, ...]] | None = None
    digestion_player_modal: dict[str, tuple[tuple[str, ...], ...]] | None = None
    npc_vore_hit: dict[str, tuple[str, ...]] | None = None
    npc_vore_miss: dict[str, tuple[str, ...]] | None = None
    offscreen_vore: dict[str, tuple[str, ...]] | None = None
    offscreen_digest: dict[str, tuple[str, ...]] | None = None
    engulfed_flavor: dict[str, tuple[str, ...]] | None = None
    introduction: tuple[str, ...] | None = None
    introduction_log_category: MessageCategory | None = None
    abilities: tuple[str, ...] = ()
    # Content marker only — no combat rules. True = unfinished / stub narratives OK.
    placeholder: bool = False


@attrs.define(frozen=True)
class EntityRegistry:
    schema_version: int
    entities: tuple[EntityDefinition, ...]
    warnings: tuple[str, ...] = ()

    def by_id(self) -> dict[str, EntityDefinition]:
        return {entity.id: entity for entity in self.entities}

    def get(self, entity_id: str) -> EntityDefinition:
        return self.by_id()[entity_id]