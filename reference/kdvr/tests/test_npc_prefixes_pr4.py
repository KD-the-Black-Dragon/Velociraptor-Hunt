"""PR4: NPC prefix system (Elite) — name, stats, floor-only roll, soft-drop."""

from __future__ import annotations

import random

from tcod.ecs import Registry

from src.components import (
    Alignment,
    DigestionStats,
    DisplayName,
    Fighter,
    NpcPrefix,
    SpeciesId,
)
from src.data.depth_scaling_config import (
    DepthScalingConfig,
    DifficultyProfile,
    PrefixSpawnConfig,
)
from src.data.entity_registry import EntityDefinition, SpawnConfig
from src.data.npc_prefix_loader import parse_npc_prefix_registry
from src.data.npc_prefix_registry import (
    NpcPrefixDefinition,
    NpcPrefixRegistry,
    PrefixStatBonuses,
)
from src.components import MobilityType
from src.save.sanitize import sanitize_loaded_world
from src.spawn import (
    apply_prefix_definition,
    spawn_entity_by_id,
    spawn_from_definition,
    try_roll_prefix,
)


def _wolfish(
    *,
    alignment: Alignment = Alignment.EVIL,
    max_hp: int = 10,
    ac: int = 1,
    dig: int | None = 3,
) -> EntityDefinition:
    return EntityDefinition(
        id="wolf",
        display_name="wolf",
        glyph="w",
        fg=(100, 100, 100),
        alignment=alignment,
        mobility=MobilityType.GROUND,
        max_hp=max_hp,
        evade=0,
        ac=ac,
        accuracy=0.5,
        min_damage=2,
        max_damage=3,
        ranged_accuracy=0.0,
        ranged_min_damage=0,
        ranged_max_damage=0,
        spawn=SpawnConfig(weight=1, min_depth=1, max_depth=1000),
        digestion_damage_per_tick=dig,
        digest_time=6 if dig is not None else None,
    )


def _elite_prefix() -> NpcPrefixDefinition:
    return NpcPrefixDefinition(
        id="elite",
        display_prefix="Elite ",
        apply_to_alignments=frozenset({Alignment.EVIL}),
        min_depth=1,
        max_depth=1000,
        weight=1,
        stat_bonuses=PrefixStatBonuses(
            max_hp=4,
            ac=1,
            accuracy=0.05,
            min_damage=1,
            max_damage=1,
            digestion_damage_per_tick=1,
        ),
    )


def _scaling_with_chance(chance: int) -> DepthScalingConfig:
    profile = DifficultyProfile(
        id="test",
        display_name="Test",
        apply_to_alignments=frozenset({Alignment.EVIL}),
        stats={},
        prefix_spawn=PrefixSpawnConfig(
            base_chance_pct=chance,
            chance_pct_per_depth_step=0,
            max_chance_pct=100,
            start_depth=1,
        ),
    )
    return DepthScalingConfig(
        schema_version=1,
        default_difficulty_id="test",
        difficulties={"test": profile},
    )


class TestLoader:
    def test_stock_elite_loads(self) -> None:
        from src.data.npc_prefix_loader import (
            load_npc_prefix_registry,
            reset_npc_prefix_registry_cache,
        )

        reset_npc_prefix_registry_cache()
        reg = load_npc_prefix_registry()
        elite = reg.get("elite")
        assert elite.display_prefix == "Elite "
        assert Alignment.EVIL in elite.apply_to_alignments
        # Stock elite max_hp was scaled with the global HP +50% pass (4 → 6).
        assert elite.stat_bonuses.max_hp == 6


class TestApplyPrefix:
    def test_elite_wolf_name_and_stats(self) -> None:
        world = Registry()
        entity = spawn_from_definition(world, _wolfish(), 1, 1, floor_depth=1)
        base_hp = entity.components[Fighter].max_hp
        base_ac = entity.components[Fighter].ac
        base_dig = entity.components[DigestionStats].damage_per_tick
        apply_prefix_definition(entity, _wolfish(), _elite_prefix())
        assert entity.components[DisplayName].name == "Elite wolf"
        assert entity.components[NpcPrefix].prefix_id == "elite"
        assert entity.components[Fighter].max_hp == base_hp + 4
        assert entity.components[Fighter].ac == base_ac + 1
        assert entity.components[Fighter].min_damage == 3
        assert entity.components[DigestionStats].damage_per_tick == base_dig + 1
        # Ranged stayed 0
        assert entity.components[Fighter].ranged_min_damage == 0

    def test_good_not_in_elite_pool(self) -> None:
        reg = NpcPrefixRegistry(schema_version=1, prefixes=(_elite_prefix(),))
        assert reg.eligible(alignment=Alignment.GOOD, floor_depth=5) == ()
        assert len(reg.eligible(alignment=Alignment.EVIL, floor_depth=5)) == 1


class TestRollPrefix:
    def test_zero_chance_never_applies(self) -> None:
        world = Registry()
        entity = spawn_from_definition(world, _wolfish(), 1, 1)
        scaling = _scaling_with_chance(0)
        result = try_roll_prefix(
            entity,
            _wolfish(),
            floor_depth=10,
            difficulty_id="test",
            depth_scaling=scaling,
            rng=random.Random(0),
            prefix_registry=NpcPrefixRegistry(
                schema_version=1, prefixes=(_elite_prefix(),)
            ),
        )
        assert result is None
        assert NpcPrefix not in entity.components

    def test_hundred_chance_always_applies(self) -> None:
        world = Registry()
        entity = spawn_from_definition(world, _wolfish(), 1, 1)
        scaling = _scaling_with_chance(100)
        result = try_roll_prefix(
            entity,
            _wolfish(),
            floor_depth=1,
            difficulty_id="test",
            depth_scaling=scaling,
            rng=random.Random(0),
            prefix_registry=NpcPrefixRegistry(
                schema_version=1, prefixes=(_elite_prefix(),)
            ),
        )
        assert result is not None
        assert entity.components[DisplayName].name == "Elite wolf"

    def test_floor_spawn_can_roll(self) -> None:
        world = Registry()
        scaling = _scaling_with_chance(100)
        entity = spawn_from_definition(
            world,
            _wolfish(),
            1,
            1,
            floor_depth=1,
            difficulty_id="test",
            depth_scaling=scaling,
            roll_prefix=True,
            rng=random.Random(1),
            prefix_registry=NpcPrefixRegistry(
                schema_version=1, prefixes=(_elite_prefix(),)
            ),
        )
        assert entity.components[DisplayName].name == "Elite wolf"

    def test_summon_path_no_roll(self) -> None:
        world = Registry()
        # spawn_entity_by_id defaults roll_prefix=False
        from src.data.entity_loader import load_entity_registry

        reg = load_entity_registry()
        scaling = _scaling_with_chance(100)
        entity = spawn_entity_by_id(
            world,
            "wolf",
            2,
            2,
            registry=reg,
            floor_depth=5,
            difficulty_id="test",
            depth_scaling=scaling,
        )
        assert NpcPrefix not in entity.components
        assert entity.components[DisplayName].name == "wolf"


class TestSoftDrop:
    def test_unknown_prefix_cleared(self) -> None:
        world = Registry()
        entity = spawn_from_definition(world, _wolfish(), 1, 1)
        entity.components[NpcPrefix] = NpcPrefix(
            prefix_id="vanished_title",
            display_prefix="Vanished ",
        )
        entity.components[DisplayName] = DisplayName(name="Vanished wolf")
        report = sanitize_loaded_world(world)
        assert "vanished_title" in report.dropped_prefix_ids
        assert NpcPrefix not in entity.components
        assert entity.components[DisplayName].name == "wolf"


class TestPrefixSpawnParse:
    def test_parse_prefix_spawn_on_difficulty(self) -> None:
        from src.data.depth_scaling_loader import parse_depth_scaling_config

        raw = {
            "schema_version": 1,
            "default_difficulty_id": "hard",
            "difficulties": {
                "hard": {
                    "display_name": "Hard",
                    "apply_to_alignments": ["evil"],
                    "stats": {},
                    "prefix_spawn": {
                        "base_chance_pct": 5,
                        "chance_pct_per_depth_step": 2,
                        "max_chance_pct": 25,
                        "start_depth": 3,
                    },
                }
            },
        }
        cfg = parse_depth_scaling_config(raw)
        ps = cfg.profile_for("hard").prefix_spawn
        assert ps.base_chance_pct == 5
        # depth 3 → steps 0 → 5; depth 5 → steps 2 → 9
        assert ps.chance_at_depth(3) == 5
        assert ps.chance_at_depth(5) == 9
