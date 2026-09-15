from __future__ import annotations

import random

import attrs

from src.data.entity_loader import load_entity_registry
from src.data.entity_registry import EntityRegistry, VoreNarrativeVariant

_index: NarrativeIndex | None = None


@attrs.define(frozen=True)
class NarrativeIndex:
    """Runtime lookup for entity vore variants and digestion lines keyed by entity id."""

    vore_variants: dict[tuple[str, str], tuple[VoreNarrativeVariant, ...]]
    digestion_complete: dict[tuple[str, str], tuple[str, ...]]
    digestion_player_modal: dict[tuple[str, str], tuple[tuple[str, ...], ...]]
    npc_vore_hit: dict[tuple[str, str], tuple[str, ...]]
    npc_vore_miss: dict[tuple[str, str], tuple[str, ...]]
    offscreen_vore: dict[tuple[str, str], tuple[str, ...]]
    offscreen_digest: dict[tuple[str, str], tuple[str, ...]]
    engulfed_flavor: dict[tuple[str, str], tuple[str, ...]]

    @classmethod
    def from_registry(cls, registry: EntityRegistry) -> NarrativeIndex:
        vore: dict[tuple[str, str], tuple[VoreNarrativeVariant, ...]] = {}
        complete: dict[tuple[str, str], tuple[str, ...]] = {}
        player_modal: dict[tuple[str, str], tuple[tuple[str, ...], ...]] = {}
        npc_vore_hit: dict[tuple[str, str], tuple[str, ...]] = {}
        npc_vore_miss: dict[tuple[str, str], tuple[str, ...]] = {}
        offscreen_vore: dict[tuple[str, str], tuple[str, ...]] = {}
        offscreen_digest: dict[tuple[str, str], tuple[str, ...]] = {}
        engulfed_flavor: dict[tuple[str, str], tuple[str, ...]] = {}

        for entity in registry.entities:
            if entity.vore_narratives:
                for narrative_type, variants in entity.vore_narratives.items():
                    vore[(entity.id, narrative_type)] = variants
            if entity.digestion_complete:
                for narrative_type, lines in entity.digestion_complete.items():
                    complete[(entity.id, narrative_type)] = lines
            if entity.digestion_player_modal:
                for narrative_type, variants in entity.digestion_player_modal.items():
                    player_modal[(entity.id, narrative_type)] = variants
            if entity.npc_vore_hit:
                for narrative_type, lines in entity.npc_vore_hit.items():
                    npc_vore_hit[(entity.id, narrative_type)] = lines
            if entity.npc_vore_miss:
                for narrative_type, lines in entity.npc_vore_miss.items():
                    npc_vore_miss[(entity.id, narrative_type)] = lines
            if entity.offscreen_vore:
                for narrative_type, lines in entity.offscreen_vore.items():
                    offscreen_vore[(entity.id, narrative_type)] = lines
            if entity.offscreen_digest:
                for narrative_type, lines in entity.offscreen_digest.items():
                    offscreen_digest[(entity.id, narrative_type)] = lines
            if entity.engulfed_flavor:
                for narrative_type, lines in entity.engulfed_flavor.items():
                    engulfed_flavor[(entity.id, narrative_type)] = lines

        return cls(
            vore_variants=vore,
            digestion_complete=complete,
            digestion_player_modal=player_modal,
            npc_vore_hit=npc_vore_hit,
            npc_vore_miss=npc_vore_miss,
            offscreen_vore=offscreen_vore,
            offscreen_digest=offscreen_digest,
            engulfed_flavor=engulfed_flavor,
        )

    def pick_vore_variant(
        self,
        entity_id: str,
        narrative_type: str,
        rng: random.Random,
    ) -> VoreNarrativeVariant | None:
        variants = self.vore_variants.get((entity_id, narrative_type))
        if not variants:
            return None
        return rng.choice(variants)

    def narrative_phases(
        self,
        entity_id: str,
        narrative_type: str,
        segment: str,
        *,
        variant_index: int = 0,
    ) -> tuple[str, ...]:
        """First variant's phases for segment (deterministic; modals use pick_vore_variant)."""
        variants = self.vore_variants.get((entity_id, narrative_type))
        if not variants:
            return ()
        index = min(max(variant_index, 0), len(variants) - 1)
        variant = variants[index]
        if segment == "attempt":
            return variant.attempt
        if segment == "success":
            return variant.success
        return ()

    def digestion_complete_lines(
        self,
        entity_id: str,
        narrative_type: str,
    ) -> tuple[str, ...]:
        return self.digestion_complete.get((entity_id, narrative_type), ())

    def pick_digestion_player_modal_phases(
        self,
        entity_id: str,
        narrative_type: str,
        rng: random.Random,
    ) -> tuple[str, ...]:
        variants = self.digestion_player_modal.get((entity_id, narrative_type))
        if not variants:
            return ()
        return rng.choice(variants)

    def npc_vore_hit_lines(
        self,
        entity_id: str,
        narrative_type: str,
    ) -> tuple[str, ...]:
        return self.npc_vore_hit.get((entity_id, narrative_type), ())

    def npc_vore_miss_lines(
        self,
        entity_id: str,
        narrative_type: str,
    ) -> tuple[str, ...]:
        return self.npc_vore_miss.get((entity_id, narrative_type), ())

    def pick_offscreen_vore_line(
        self,
        entity_id: str,
        narrative_type: str,
        rng: random.Random,
    ) -> str | None:
        lines = self.offscreen_vore.get((entity_id, narrative_type))
        if not lines:
            return None
        return rng.choice(lines)

    def pick_offscreen_digest_line(
        self,
        entity_id: str,
        narrative_type: str,
        rng: random.Random,
    ) -> str | None:
        lines = self.offscreen_digest.get((entity_id, narrative_type))
        if not lines:
            return None
        return rng.choice(lines)

    def engulfed_flavor_lines(
        self,
        entity_id: str,
        narrative_type: str,
    ) -> tuple[str, ...]:
        return self.engulfed_flavor.get((entity_id, narrative_type), ())

    def pick_engulfed_flavor_line(
        self,
        entity_id: str,
        narrative_type: str,
        rng: random.Random,
    ) -> str | None:
        lines = self.engulfed_flavor_lines(entity_id, narrative_type)
        if not lines:
            return None
        return rng.choice(lines)


def get_narrative_index() -> NarrativeIndex:
    global _index
    if _index is None:
        _index = NarrativeIndex.from_registry(load_entity_registry())
    return _index


def reset_narrative_index() -> None:
    """Clear cached index (tests or hot-reload)."""
    global _index
    _index = None