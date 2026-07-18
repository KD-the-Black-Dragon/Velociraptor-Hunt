"""PR1: dual-int depth scaling bake (fixture-pinned; not stock balance numbers)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from tcod.ecs import Registry

from src.components import (
    Alignment,
    DigestionStats,
    Fighter,
    MobilityType,
)
from src.data.depth_scaling_config import (
    DepthScalingConfig,
    DifficultyProfile,
    StatSchedule,
    bonuses_for_spawn,
    dual_int_bonus,
    resolve_bonuses,
)
from src.data.depth_scaling_loader import (
    DepthScalingLoadError,
    parse_depth_scaling_config,
    reset_depth_scaling_cache,
)
from src.data.entity_registry import EntityDefinition, SpawnConfig
from src.spawn import spawn_entity_by_id, spawn_from_definition


def _schedule(**kwargs: int | float) -> StatSchedule:
    return StatSchedule(
        per_floor=int(kwargs.get("per_floor", 0)),
        every_n_floors=int(kwargs.get("every_n_floors", 0)),
        bank_amount=int(kwargs.get("bank_amount", 1)),
        start_depth=int(kwargs.get("start_depth", 1)),
        unit=float(kwargs.get("unit", 1.0)),
    )


def _profile(
    *,
    stats: dict[str, StatSchedule] | None = None,
    alignments: frozenset[Alignment] | None = None,
) -> DifficultyProfile:
    return DifficultyProfile(
        id="test",
        display_name="Test",
        apply_to_alignments=alignments or frozenset({Alignment.EVIL}),
        stats=stats or {},
    )


def _config(profile: DifficultyProfile) -> DepthScalingConfig:
    return DepthScalingConfig(
        schema_version=1,
        default_difficulty_id="test",
        difficulties={"test": profile},
    )


def _def(
    *,
    alignment: Alignment = Alignment.EVIL,
    max_hp: int = 10,
    ac: int = 1,
    evade: int = 0,
    accuracy: float = 0.5,
    min_damage: int = 2,
    max_damage: int = 3,
    ranged_accuracy: float = 0.0,
    ranged_min_damage: int = 0,
    ranged_max_damage: int = 0,
    dig_damage: int | None = 3,
    digest_time: int | None = 6,
) -> EntityDefinition:
    return EntityDefinition(
        id="fixture_critter",
        display_name="critter",
        glyph="c",
        fg=(100, 100, 100),
        alignment=alignment,
        mobility=MobilityType.GROUND,
        max_hp=max_hp,
        evade=evade,
        ac=ac,
        accuracy=accuracy,
        min_damage=min_damage,
        max_damage=max_damage,
        ranged_accuracy=ranged_accuracy,
        ranged_min_damage=ranged_min_damage,
        ranged_max_damage=ranged_max_damage,
        spawn=SpawnConfig(weight=1, min_depth=1, max_depth=1000),
        digestion_damage_per_tick=dig_damage,
        digest_time=digest_time,
    )


class TestDualIntMath:
    def test_floor1_zero_steps(self) -> None:
        s = _schedule(per_floor=1, every_n_floors=4, bank_amount=1, start_depth=1)
        assert dual_int_bonus(s, 1) == 0

    def test_average_1_25_at_four_steps(self) -> None:
        s = _schedule(per_floor=1, every_n_floors=4, bank_amount=1, start_depth=1)
        # depth 5 → steps 4 → 4*1 + floor(4/4)*1 = 5
        assert dual_int_bonus(s, 5) == 5

    def test_pure_bank_every_four(self) -> None:
        s = _schedule(per_floor=0, every_n_floors=4, bank_amount=1, start_depth=1)
        assert dual_int_bonus(s, 4) == 0
        assert dual_int_bonus(s, 5) == 1
        assert dual_int_bonus(s, 9) == 2

    def test_every_n_zero_disables_bank(self) -> None:
        s = _schedule(per_floor=2, every_n_floors=0, bank_amount=99, start_depth=1)
        assert dual_int_bonus(s, 5) == 8  # 2 * 4 steps


class TestResolveAndAlignment:
    def test_accuracy_unit(self) -> None:
        profile = _profile(
            stats={
                "accuracy": _schedule(
                    per_floor=0, every_n_floors=1, bank_amount=1, start_depth=1, unit=0.01
                )
            }
        )
        # depth 3 → steps 2 → 2 * 0.01
        bonuses = resolve_bonuses(profile, 3)
        assert bonuses.accuracy == pytest.approx(0.02)

    def test_evil_only_gate(self) -> None:
        profile = _profile(
            stats={"ac": _schedule(per_floor=1, every_n_floors=0, start_depth=1)},
            alignments=frozenset({Alignment.EVIL}),
        )
        config = _config(profile)
        evil = bonuses_for_spawn(
            config, floor_depth=3, alignment=Alignment.EVIL, difficulty_id="test"
        )
        good = bonuses_for_spawn(
            config, floor_depth=3, alignment=Alignment.GOOD, difficulty_id="test"
        )
        neutral = bonuses_for_spawn(
            config, floor_depth=3, alignment=Alignment.NEUTRAL, difficulty_id="test"
        )
        assert evil.ac == 2
        assert good.ac == 0
        assert neutral.ac == 0


class TestSpawnBake:
    def test_ac_and_hp_bake(self) -> None:
        world = Registry()
        profile = _profile(
            stats={
                "ac": _schedule(per_floor=0, every_n_floors=4, bank_amount=1),
                "max_hp": _schedule(per_floor=1, every_n_floors=0),
            }
        )
        config = _config(profile)
        entity = spawn_from_definition(
            world,
            _def(max_hp=10, ac=1),
            1,
            1,
            floor_depth=5,
            difficulty_id="test",
            depth_scaling=config,
        )
        fighter = entity.components[Fighter]
        # steps=4: ac +1, max_hp +4
        assert fighter.ac == 2
        assert fighter.max_hp == 14
        assert fighter.hp == 14

    def test_good_unaffected(self) -> None:
        world = Registry()
        profile = _profile(
            stats={"ac": _schedule(per_floor=5, every_n_floors=0)},
        )
        config = _config(profile)
        entity = spawn_from_definition(
            world,
            _def(alignment=Alignment.GOOD, ac=2, dig_damage=None, digest_time=None),
            1,
            1,
            floor_depth=10,
            difficulty_id="test",
            depth_scaling=config,
        )
        assert entity.components[Fighter].ac == 2

    def test_digestion_damage_scales_not_digest_time(self) -> None:
        world = Registry()
        profile = _profile(
            stats={
                "digestion_damage_per_tick": _schedule(
                    per_floor=0, every_n_floors=2, bank_amount=1
                )
            }
        )
        config = _config(profile)
        entity = spawn_from_definition(
            world,
            _def(dig_damage=3, digest_time=6),
            1,
            1,
            floor_depth=5,  # steps 4 → bank floor(4/2)=2
            difficulty_id="test",
            depth_scaling=config,
        )
        dig = entity.components[DigestionStats]
        assert dig.damage_per_tick == 5
        assert dig.digest_time == 6

    def test_ranged_gate_stock_zero_stays_zero(self) -> None:
        world = Registry()
        profile = _profile(
            stats={
                "min_damage": _schedule(per_floor=1, every_n_floors=0),
                "max_damage": _schedule(per_floor=1, every_n_floors=0),
                "accuracy": _schedule(
                    per_floor=0, every_n_floors=1, bank_amount=1, unit=0.1
                ),
            }
        )
        config = _config(profile)
        entity = spawn_from_definition(
            world,
            _def(
                min_damage=2,
                max_damage=3,
                ranged_min_damage=0,
                ranged_max_damage=0,
                ranged_accuracy=0.0,
            ),
            1,
            1,
            floor_depth=4,  # steps 3
            difficulty_id="test",
            depth_scaling=config,
        )
        fighter = entity.components[Fighter]
        assert fighter.min_damage == 5
        assert fighter.max_damage == 6
        assert fighter.ranged_min_damage == 0
        assert fighter.ranged_max_damage == 0
        assert fighter.ranged_accuracy == 0.0

    def test_ranged_scales_when_base_positive(self) -> None:
        world = Registry()
        profile = _profile(
            stats={
                "min_damage": _schedule(per_floor=1, every_n_floors=0),
                "max_damage": _schedule(per_floor=1, every_n_floors=0),
            }
        )
        config = _config(profile)
        entity = spawn_from_definition(
            world,
            _def(
                min_damage=2,
                max_damage=3,
                ranged_min_damage=1,
                ranged_max_damage=2,
                ranged_accuracy=0.4,
            ),
            1,
            1,
            floor_depth=3,  # steps 2
            difficulty_id="test",
            depth_scaling=config,
        )
        fighter = entity.components[Fighter]
        assert fighter.ranged_min_damage == 3
        assert fighter.ranged_max_damage == 4

    def test_separable_min_max_damage(self) -> None:
        world = Registry()
        profile = _profile(
            stats={
                "min_damage": _schedule(per_floor=0, every_n_floors=0),
                "max_damage": _schedule(per_floor=1, every_n_floors=0),
            }
        )
        config = _config(profile)
        entity = spawn_from_definition(
            world,
            _def(min_damage=2, max_damage=3),
            1,
            1,
            floor_depth=4,
            difficulty_id="test",
            depth_scaling=config,
        )
        fighter = entity.components[Fighter]
        assert fighter.min_damage == 2
        assert fighter.max_damage == 6  # 3 + 3 steps

    def test_spawn_entity_by_id_forwards_depth(self) -> None:
        # Use stock wolf via real registry is ok if we inject depth_scaling that
        # only affects ac with fixture config — still pins math not stock wolf AC.
        world = Registry()
        profile = _profile(
            stats={"ac": _schedule(per_floor=1, every_n_floors=0, start_depth=1)}
        )
        config = _config(profile)
        from src.data.entity_loader import load_entity_registry

        reg = load_entity_registry()
        wolf = spawn_entity_by_id(
            world,
            "wolf",
            2,
            2,
            registry=reg,
            floor_depth=4,
            difficulty_id="test",
            depth_scaling=config,
        )
        base_ac = reg.get("wolf").ac
        assert wolf.components[Fighter].ac == base_ac + 3


class TestLoader:
    def test_parse_stock_like_zero(self) -> None:
        raw = {
            "schema_version": 1,
            "default_difficulty_id": "normal",
            "difficulties": {
                "normal": {
                    "display_name": "Normal",
                    "apply_to_alignments": ["evil"],
                    "stats": {},
                }
            },
        }
        config = parse_depth_scaling_config(raw)
        assert config.default_difficulty_id == "normal"
        bonuses = bonuses_for_spawn(
            config, floor_depth=99, alignment=Alignment.EVIL, difficulty_id="normal"
        )
        assert bonuses == bonuses_for_spawn(
            config, floor_depth=1, alignment=Alignment.EVIL
        )
        assert bonuses.ac == 0
        assert bonuses.max_hp == 0

    def test_unknown_stat_rejected(self) -> None:
        raw = {
            "schema_version": 1,
            "default_difficulty_id": "normal",
            "difficulties": {
                "normal": {
                    "display_name": "Normal",
                    "apply_to_alignments": ["evil"],
                    "stats": {"digest_time": {"per_floor": 1}},
                }
            },
        }
        with pytest.raises(DepthScalingLoadError, match="unknown stat"):
            parse_depth_scaling_config(raw)

    def test_shipped_file_loads(self) -> None:
        reset_depth_scaling_cache()
        from src.data.depth_scaling_loader import load_depth_scaling_config

        config = load_depth_scaling_config()
        assert set(config.difficulties) >= {"easier", "normal", "hard", "nightmare"}
        assert config.default_difficulty_id == "normal"
        # Floor 1: zero depth steps (protect opener) — not live deep-floor numbers
        b = bonuses_for_spawn(
            config, floor_depth=1, alignment=Alignment.EVIL, difficulty_id="nightmare"
        )
        assert b.ac == 0
        assert b.max_hp == 0
        assert b.digestion_damage_per_tick == 0
        # Good never scales on stock apply_to_alignments
        good = bonuses_for_spawn(
            config, floor_depth=20, alignment=Alignment.GOOD, difficulty_id="nightmare"
        )
        assert good.ac == 0

    def test_roundtrip_fixture_file(self, tmp_path: Path) -> None:
        path = tmp_path / "depth_scaling.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "default_difficulty_id": "hard",
                    "difficulties": {
                        "hard": {
                            "display_name": "Hard",
                            "apply_to_alignments": ["evil"],
                            "stats": {
                                "ac": {
                                    "per_floor": 0,
                                    "every_n_floors": 4,
                                    "bank_amount": 1,
                                    "start_depth": 1,
                                }
                            },
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        from src.data.depth_scaling_loader import load_depth_scaling_config

        config = load_depth_scaling_config(path)
        b = bonuses_for_spawn(
            config, floor_depth=5, alignment=Alignment.EVIL, difficulty_id="hard"
        )
        assert b.ac == 1
