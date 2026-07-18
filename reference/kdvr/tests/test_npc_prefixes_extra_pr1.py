"""PR1: NPC prefix requirements, ability grants, ranged_accuracy."""

from __future__ import annotations

import random

from tcod.ecs import Registry

from src.components import Abilities, DisplayName, Fighter, NpcPrefix
from src.components import MobilityType
from src.components import Alignment
from src.data.entity_registry import EntityDefinition, SpawnConfig
from src.data.npc_prefix_loader import parse_npc_prefix_registry
from src.data.npc_prefix_registry import (
    NpcPrefixDefinition,
    NpcPrefixRegistry,
    PrefixRequirements,
    PrefixStatBonuses,
)
from src.data.ability_parser import FixedAbility
from src.spawn import apply_prefix_definition, spawn_from_definition, try_roll_prefix
from tests.test_npc_prefixes_pr4 import _scaling_with_chance, _wolfish


def _has_fixed_ability(entity, ability_id: str) -> bool:
    abilities = entity.components.get(Abilities)
    if abilities is None:
        return False
    return any(
        isinstance(parsed, FixedAbility) and parsed.ability_id == ability_id
        for parsed in abilities.parsed
    )


def _ranged_wolf() -> EntityDefinition:
    return EntityDefinition(
        id="wolf",
        display_name="wolf",
        glyph="w",
        fg=(100, 100, 100),
        alignment=Alignment.EVIL,
        mobility=MobilityType.GROUND,
        max_hp=10,
        evade=0,
        ac=1,
        accuracy=0.5,
        min_damage=2,
        max_damage=3,
        ranged_accuracy=0.4,
        ranged_min_damage=1,
        ranged_max_damage=2,
        spawn=SpawnConfig(weight=1, min_depth=1, max_depth=1000),
        digestion_damage_per_tick=3,
        digest_time=6,
        abilities=("Range6",),
    )


def _melee_rat() -> EntityDefinition:
    return EntityDefinition(
        id="rat",
        display_name="rat",
        glyph="r",
        fg=(100, 100, 100),
        alignment=Alignment.EVIL,
        mobility=MobilityType.GROUND,
        max_hp=4,
        evade=0,
        ac=0,
        accuracy=0.4,
        min_damage=1,
        max_damage=2,
        ranged_accuracy=0.0,
        ranged_min_damage=0,
        ranged_max_damage=0,
        spawn=SpawnConfig(weight=1, min_depth=1, max_depth=1000),
        digestion_damage_per_tick=2,
        digest_time=6,
        abilities=(),
    )


def _smite_slime() -> EntityDefinition:
    return EntityDefinition(
        id="slime",
        display_name="slime",
        glyph="s",
        fg=(100, 100, 100),
        alignment=Alignment.EVIL,
        mobility=MobilityType.GROUND,
        max_hp=8,
        evade=0,
        ac=0,
        accuracy=0.5,
        min_damage=1,
        max_damage=2,
        ranged_accuracy=0.5,
        ranged_min_damage=2,
        ranged_max_damage=3,
        spawn=SpawnConfig(weight=1, min_depth=1, max_depth=1000),
        digestion_damage_per_tick=2,
        digest_time=6,
        abilities=("Smite3",),
    )


def _sniper_prefix() -> NpcPrefixDefinition:
    return NpcPrefixDefinition(
        id="sniper",
        display_prefix="Sniper ",
        apply_to_alignments=frozenset({Alignment.EVIL}),
        min_depth=1,
        max_depth=1000,
        weight=1,
        stat_bonuses=PrefixStatBonuses(ranged_accuracy=0.10),
        requirements=PrefixRequirements(ability_families=frozenset({"RangeN"})),
    )


def _brute_prefix() -> NpcPrefixDefinition:
    return NpcPrefixDefinition(
        id="brute",
        display_prefix="Brute ",
        apply_to_alignments=frozenset({Alignment.EVIL}),
        min_depth=1,
        max_depth=1000,
        weight=1,
        stat_bonuses=PrefixStatBonuses(
            min_damage=2,
            max_damage=2,
            accuracy=-0.10,
        ),
        grant_abilities=("Slow",),
    )


def _starving_prefix() -> NpcPrefixDefinition:
    return NpcPrefixDefinition(
        id="starving",
        display_prefix="Starving ",
        apply_to_alignments=frozenset({Alignment.EVIL}),
        min_depth=1,
        max_depth=1000,
        weight=1,
        stat_bonuses=PrefixStatBonuses(max_hp=-2),
        grant_abilities=("PreferVore",),
    )


class TestLoaderExtensions:
    def test_parse_requirements_grant_and_ranged_accuracy(self) -> None:
        raw = {
            "schema_version": 1,
            "prefixes": [
                {
                    "id": "sniper",
                    "display_prefix": "Sniper ",
                    "apply_to_alignments": ["evil"],
                    "min_depth": 1,
                    "max_depth": 100,
                    "weight": 2,
                    "stat_bonuses": {"ranged_accuracy": 0.1},
                    "requirements": {"ability_families": ["RangeN"]},
                },
                {
                    "id": "brute",
                    "display_prefix": "Brute ",
                    "apply_to_alignments": ["evil"],
                    "min_depth": 1,
                    "max_depth": 100,
                    "weight": 1,
                    "grant_abilities": ["Slow"],
                },
            ],
        }
        reg = parse_npc_prefix_registry(raw)
        sniper = reg.get("sniper")
        assert sniper.stat_bonuses.ranged_accuracy == 0.1
        assert sniper.requirements.ability_families == frozenset({"RangeN"})
        assert reg.get("brute").grant_abilities == ("Slow",)


class TestEntityFilter:
    def test_sniper_eligible_for_range_not_smite_or_melee(self) -> None:
        reg = NpcPrefixRegistry(schema_version=1, prefixes=(_sniper_prefix(),))
        assert reg.eligible_for_entity(
            alignment=Alignment.EVIL,
            floor_depth=5,
            definition=_ranged_wolf(),
        ) == (_sniper_prefix(),)
        assert reg.eligible_for_entity(
            alignment=Alignment.EVIL,
            floor_depth=5,
            definition=_melee_rat(),
        ) == ()
        assert reg.eligible_for_entity(
            alignment=Alignment.EVIL,
            floor_depth=5,
            definition=_smite_slime(),
        ) == ()


class TestRollFilter:
    def test_no_prefix_when_only_sniper_and_melee_host(self) -> None:
        world = Registry()
        entity = spawn_from_definition(world, _melee_rat(), 1, 1)
        scaling = _scaling_with_chance(100)
        result = try_roll_prefix(
            entity,
            _melee_rat(),
            floor_depth=5,
            difficulty_id="test",
            depth_scaling=scaling,
            rng=random.Random(0),
            prefix_registry=NpcPrefixRegistry(
                schema_version=1, prefixes=(_sniper_prefix(),)
            ),
        )
        assert result is None
        assert NpcPrefix not in entity.components
        assert entity.components[DisplayName].name == "rat"

    def test_sniper_applies_to_range_host(self) -> None:
        world = Registry()
        entity = spawn_from_definition(world, _ranged_wolf(), 1, 1)
        scaling = _scaling_with_chance(100)
        result = try_roll_prefix(
            entity,
            _ranged_wolf(),
            floor_depth=5,
            difficulty_id="test",
            depth_scaling=scaling,
            rng=random.Random(0),
            prefix_registry=NpcPrefixRegistry(
                schema_version=1, prefixes=(_sniper_prefix(),)
            ),
        )
        assert result is not None
        assert result.id == "sniper"
        assert entity.components[DisplayName].name == "Sniper wolf"


class TestAbilityGrants:
    def test_brute_grants_slow(self) -> None:
        world = Registry()
        entity = spawn_from_definition(world, _wolfish(), 1, 1)
        apply_prefix_definition(entity, _wolfish(), _brute_prefix())
        assert _has_fixed_ability(entity, "Slow")
        assert entity.components[DisplayName].name == "Brute wolf"

    def test_starving_grants_prefer_vore(self) -> None:
        world = Registry()
        entity = spawn_from_definition(world, _wolfish(), 1, 1)
        apply_prefix_definition(entity, _wolfish(), _starving_prefix())
        assert _has_fixed_ability(entity, "PreferVore")


class TestRangedAccuracy:
    def test_sniper_buffs_ranged_only(self) -> None:
        world = Registry()
        entity = spawn_from_definition(world, _ranged_wolf(), 1, 1)
        base_melee_acc = entity.components[Fighter].accuracy
        base_ranged_acc = entity.components[Fighter].ranged_accuracy
        apply_prefix_definition(entity, _ranged_wolf(), _sniper_prefix())
        fighter = entity.components[Fighter]
        assert fighter.accuracy == base_melee_acc
        assert fighter.ranged_accuracy == base_ranged_acc + 0.10