"""PR2: spawn.requires_vore_types filters which types a predator may initiate."""

from __future__ import annotations

import random

from tcod.ecs import Registry

from src.components import SpeciesId, VoreNarratives
from src.constants import VoreContentPreferences
from src.systems.vore import (
    attemptable_narrative_types,
    capable_narrative_types,
    pick_attempt_narrative_type,
    species_vore_capability,
)
from tests.spawn_test_helpers import fixture_entity_definition, fixture_entity_registry


def _prefs(*enabled: str) -> VoreContentPreferences:
    return VoreContentPreferences(enabled=frozenset(enabled))


def _predator(
    *,
    entity_id: str = "cv_only",
    narrative_types: tuple[str, ...] = ("OV", "CV", "AV"),
) -> object:
    world = Registry()
    entity = world.new_entity()
    entity.components[SpeciesId] = SpeciesId(id=entity_id)
    entity.components[VoreNarratives] = VoreNarratives(types=narrative_types)
    return entity


def test_capable_narrative_types_empty_capability_is_passthrough() -> None:
    assert capable_narrative_types(("OV", "CV", "AV"), frozenset()) == ("OV", "CV", "AV")


def test_capable_narrative_types_intersects() -> None:
    assert capable_narrative_types(("OV", "CV", "AV"), frozenset({"CV", "AV"})) == (
        "CV",
        "AV",
    )


def test_species_vore_capability_missing_species_is_unrestricted() -> None:
    world = Registry()
    entity = world.new_entity()
    entity.components[VoreNarratives] = VoreNarratives(types=("OV", "CV", "AV"))
    assert species_vore_capability(entity) == frozenset()


def test_species_vore_capability_unknown_id_is_unrestricted() -> None:
    predator = _predator(entity_id="no_such_species")
    registry = fixture_entity_registry(fixture_entity_definition(entity_id="other"))
    assert species_vore_capability(predator, registry=registry) == frozenset()


def test_attemptable_respects_capability_and_prefs() -> None:
    predator = _predator(entity_id="cv_av")
    registry = fixture_entity_registry(
        fixture_entity_definition(
            entity_id="cv_av",
            requires_vore_types=frozenset({"CV", "AV"}),
        )
    )
    # All prefs on → only CV/AV
    assert set(
        attemptable_narrative_types(
            predator, _prefs("OV", "CV", "AV"), registry=registry
        )
    ) == {"CV", "AV"}
    # CV-only prefs → CV only
    assert attemptable_narrative_types(
        predator, _prefs("CV"), registry=registry
    ) == ["CV"]
    # OV-only prefs → empty (no attempt this PR)
    assert (
        attemptable_narrative_types(predator, _prefs("OV"), registry=registry) == []
    )


def test_attemptable_unrestricted_when_requires_empty() -> None:
    predator = _predator(entity_id="open")
    registry = fixture_entity_registry(
        fixture_entity_definition(entity_id="open", requires_vore_types=frozenset())
    )
    assert set(
        attemptable_narrative_types(
            predator, _prefs("OV", "CV", "AV"), registry=registry
        )
    ) == {"OV", "CV", "AV"}


def test_pick_attempt_never_selects_outside_capability() -> None:
    predator = _predator(entity_id="cv_only")
    registry = fixture_entity_registry(
        fixture_entity_definition(
            entity_id="cv_only",
            requires_vore_types=frozenset({"CV"}),
        )
    )
    rng = random.Random(0)
    prefs = _prefs("OV", "CV", "AV")
    for _ in range(50):
        picked = pick_attempt_narrative_type(
            predator, prefs, rng, registry=registry
        )
        assert picked == "CV"


def test_pick_attempt_returns_generic_when_pool_empty() -> None:
    from src.systems.vore_fallback import GENERIC_VORE_TYPE

    predator = _predator(entity_id="cv_only")
    registry = fixture_entity_registry(
        fixture_entity_definition(
            entity_id="cv_only",
            requires_vore_types=frozenset({"CV"}),
        )
    )
    assert (
        pick_attempt_narrative_type(
            predator, _prefs("OV"), random.Random(1), registry=registry
        )
        == GENERIC_VORE_TYPE
    )
