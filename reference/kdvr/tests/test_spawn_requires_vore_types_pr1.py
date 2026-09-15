"""PR1: spawn.requires_vore_types parse + eligibility gate (pinned fixtures only)."""

from __future__ import annotations

import random

import pytest
from tcod.ecs import Registry

from src.components import Alignment, SpeciesId
from src.constants import VoreContentPreferences
from src.data.entity_loader import EntityLoadError, parse_entity_registry
from src.data.entity_registry import SpawnConfig
from src.map_gen import GameMap, Tile
from src.spawn import (
    _eligible_definitions,
    meets_vore_type_requirements,
    spawn_floor_population,
    spawn_from_definition,
)
from tests.spawn_test_helpers import (
    expected_spawn_count,
    fixture_entity_definition,
    fixture_entity_registry,
    fixed_spawn_config,
)
from tests.test_npc_data_pr1 import _minimal_entity


def _prefs(*enabled: str) -> VoreContentPreferences:
    return VoreContentPreferences(enabled=frozenset(enabled))


def _open_map() -> GameMap:
    game_map = GameMap(40, 40)
    game_map.tiles[:, :] = Tile.FLOOR
    game_map.enter_xy = (20, 20)
    return game_map


def _spawn_payload(**spawn_extra: object) -> dict[str, object]:
    spawn: dict[str, object] = {
        "weight": 1,
        "min_depth": 1,
        "max_depth": 10,
        "terrain": "land",
    }
    spawn.update(spawn_extra)
    return _minimal_entity(id="gated", spawn=spawn)


# --- Parse matrix ---


def test_parse_omitted_requires_vore_types_is_empty() -> None:
    registry = parse_entity_registry(
        {"schema_version": 1, "entities": [_minimal_entity()]}
    )
    assert registry.get("test_creature").spawn.requires_vore_types == frozenset()


def test_parse_null_and_empty_array_are_empty() -> None:
    for value in (None, []):
        registry = parse_entity_registry(
            {"schema_version": 1, "entities": [_spawn_payload(requires_vore_types=value)]}
        )
        assert registry.get("gated").spawn.requires_vore_types == frozenset()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (["OV"], frozenset({"OV"})),
        (["CV"], frozenset({"CV"})),
        (["AV"], frozenset({"AV"})),
        (["OV", "CV"], frozenset({"OV", "CV"})),
        (["OV", "CV", "AV"], frozenset({"OV", "CV", "AV"})),
        (["OV", "OV", "bogus", 3, None], frozenset({"OV"})),
        (["nope", "also_no"], frozenset()),
    ],
)
def test_parse_requires_vore_types_matrix(
    raw: list[object], expected: frozenset[str]
) -> None:
    registry = parse_entity_registry(
        {"schema_version": 1, "entities": [_spawn_payload(requires_vore_types=raw)]}
    )
    assert registry.get("gated").spawn.requires_vore_types == expected


def test_parse_requires_vore_types_bad_type_errors() -> None:
    with pytest.raises(EntityLoadError, match="requires_vore_types"):
        parse_entity_registry(
            {
                "schema_version": 1,
                "entities": [_spawn_payload(requires_vore_types="CV")],
            }
        )


# --- meets_vore_type_requirements ---


@pytest.mark.parametrize(
    ("required", "enabled", "ok"),
    [
        (frozenset(), frozenset({"OV"}), True),
        (frozenset({"CV"}), frozenset({"CV"}), True),
        (frozenset({"CV"}), frozenset({"OV"}), False),
        (frozenset({"OV", "CV"}), frozenset({"OV", "CV"}), True),
        # OR: partial prefs still eligible when any listed type is enabled
        (frozenset({"OV", "CV"}), frozenset({"OV"}), True),
        (frozenset({"OV", "CV"}), frozenset({"CV"}), True),
        (frozenset({"OV", "CV"}), frozenset({"AV"}), False),
        (frozenset({"OV", "CV", "AV"}), frozenset({"OV", "CV", "AV"}), True),
        (frozenset({"OV", "CV", "AV"}), frozenset({"OV"}), True),
        (frozenset({"OV", "CV", "AV"}), frozenset({"OV", "CV"}), True),
        (frozenset({"CV", "AV"}), frozenset({"OV"}), False),
        (frozenset({"CV", "AV"}), frozenset({"CV"}), True),
    ],
)
def test_meets_vore_type_requirements_truth_table(
    required: frozenset[str], enabled: frozenset[str], ok: bool
) -> None:
    definition = fixture_entity_definition(requires_vore_types=required)
    assert meets_vore_type_requirements(definition, _prefs(*enabled)) is ok


def test_meets_with_none_prefs_treats_all_enabled() -> None:
    definition = fixture_entity_definition(
        requires_vore_types=frozenset({"OV", "CV", "AV"})
    )
    assert meets_vore_type_requirements(definition, None) is True


# --- spawn_from_definition gate ---


def test_spawn_from_definition_returns_none_when_gated() -> None:
    world = Registry()
    definition = fixture_entity_definition(
        entity_id="cv_only",
        requires_vore_types=frozenset({"CV"}),
    )
    assert (
        spawn_from_definition(world, definition, 1, 1, vore_prefs=_prefs("OV"))
        is None
    )


def test_spawn_from_definition_succeeds_when_requirement_met() -> None:
    world = Registry()
    definition = fixture_entity_definition(
        entity_id="cv_only",
        requires_vore_types=frozenset({"CV"}),
    )
    entity = spawn_from_definition(
        world, definition, 1, 1, vore_prefs=_prefs("CV", "OV")
    )
    assert entity is not None
    assert entity.components[SpeciesId].id == "cv_only"


# --- Floor eligibility + density ---


def test_eligible_definitions_excludes_gated_species() -> None:
    gated = fixture_entity_definition(
        entity_id="cv_only",
        alignment=Alignment.EVIL,
        requires_vore_types=frozenset({"CV"}),
        spawn_weight=5,
    )
    open_def = fixture_entity_definition(
        entity_id="open",
        alignment=Alignment.EVIL,
        spawn_weight=5,
    )
    registry = fixture_entity_registry(gated, open_def)
    prefs_off = _prefs("OV")
    eligible = _eligible_definitions(
        registry,
        floor_depth=1,
        terrain="land",
        map_has_water=False,
        vore_prefs=prefs_off,
    )
    assert [d.id for d in eligible] == ["open"]

    prefs_on = _prefs("OV", "CV")
    eligible_on = _eligible_definitions(
        registry,
        floor_depth=1,
        terrain="land",
        map_has_water=False,
        vore_prefs=prefs_on,
    )
    assert {d.id for d in eligible_on} == {"cv_only", "open"}


def test_density_target_unchanged_when_gated_species_filtered() -> None:
    """Gated-out defs leave the pool; remaining species still fill density target."""
    gated = fixture_entity_definition(
        entity_id="cv_only",
        alignment=Alignment.EVIL,
        requires_vore_types=frozenset({"CV"}),
        spawn_weight=100,
    )
    filler = fixture_entity_definition(
        entity_id="filler",
        alignment=Alignment.EVIL,
        spawn_weight=1,
    )
    registry = fixture_entity_registry(gated, filler)
    game_map = _open_map()
    config = fixed_spawn_config(density_pct=0.2, density_variance=0.0)
    expected = expected_spawn_count(
        game_map, 20, 20, floor_depth=1, config=config, rng_seed=7
    )
    assert expected > 0

    spawned = spawn_floor_population(
        Registry(),
        game_map,
        player_x=20,
        player_y=20,
        floor_depth=1,
        rng=random.Random(7),
        registry=registry,
        spawn_config=config,
        vore_prefs=_prefs("OV"),  # CV off → cv_only ineligible
    )
    assert len(spawned) == expected
    assert all(e.components[SpeciesId].id == "filler" for e in spawned)


def test_spawn_config_default_requires_empty() -> None:
    cfg = SpawnConfig(weight=1, min_depth=1, max_depth=1)
    assert cfg.requires_vore_types == frozenset()
