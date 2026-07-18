"""PR1 engineering-maintainability: spawn-at-depth / difficulty test helpers."""

from __future__ import annotations

from tcod.ecs import Registry

from src.components import Alignment, Fighter, SpeciesId
from src.engine import GameEngine
from tests.spawn_test_helpers import (
    fighter_of,
    fixture_depth_scaling_config,
    fixture_difficulty_profile,
    fixture_entity_definition,
    fixture_entity_registry,
    fixture_stat_schedule,
    position_of,
    set_engine_depth,
    spawn_fixture_at,
    spawn_species_at,
    spawn_species_on_engine,
    species_id_of,
)


class TestFixtureDepthBake:
    def test_spawn_fixture_at_bakes_pinned_max_hp(self) -> None:
        """depth 5, start 1 → steps 4; per_floor 1 → +4 HP (pinned, not stock)."""
        world = Registry()
        scaling = fixture_depth_scaling_config(
            fixture_difficulty_profile(
                stats={"max_hp": fixture_stat_schedule(per_floor=1)},
            )
        )
        entity = spawn_fixture_at(
            world,
            fixture_entity_definition(max_hp=10, ac=1),
            3,
            4,
            floor_depth=5,
            difficulty_id="test",
            depth_scaling=scaling,
        )
        fighter = fighter_of(entity)
        assert fighter.max_hp == 14
        assert fighter.hp == 14
        assert position_of(entity).x == 3
        assert position_of(entity).y == 4

    def test_good_alignment_not_scaled_when_profile_evil_only(self) -> None:
        world = Registry()
        scaling = fixture_depth_scaling_config(
            fixture_difficulty_profile(
                stats={"ac": fixture_stat_schedule(per_floor=5)},
            )
        )
        entity = spawn_fixture_at(
            world,
            fixture_entity_definition(
                alignment=Alignment.GOOD,
                ac=2,
                digestion_damage_per_tick=None,
                digest_time=None,
            ),
            0,
            0,
            floor_depth=20,
            difficulty_id="test",
            depth_scaling=scaling,
        )
        assert fighter_of(entity).ac == 2

    def test_spawn_species_at_uses_fixture_registry(self) -> None:
        world = Registry()
        definition = fixture_entity_definition(
            entity_id="depth_critter",
            max_hp=8,
            ac=0,
        )
        registry = fixture_entity_registry(definition)
        scaling = fixture_depth_scaling_config(
            fixture_difficulty_profile(
                stats={
                    "ac": fixture_stat_schedule(
                        per_floor=0,
                        every_n_floors=4,
                        bank_amount=1,
                    ),
                },
            )
        )
        # depth 5 → steps 4 → floor(4/4)*1 = +1 ac
        entity = spawn_species_at(
            world,
            "depth_critter",
            1,
            2,
            floor_depth=5,
            difficulty_id="test",
            depth_scaling=scaling,
            registry=registry,
        )
        assert species_id_of(entity) == "depth_critter"
        assert fighter_of(entity).ac == 1
        assert fighter_of(entity).max_hp == 8


class TestEngineHelpers:
    def test_set_engine_depth(self) -> None:
        engine = GameEngine(skip_new_game=True)
        set_engine_depth(engine, floor_depth=12, difficulty_id="normal")
        assert engine.floor_depth == 12
        assert engine.difficulty_id == "normal"

    def test_spawn_species_on_engine_defaults_to_engine_context(self) -> None:
        engine = GameEngine()
        set_engine_depth(engine, floor_depth=7, difficulty_id="normal")
        definition = fixture_entity_definition(entity_id="on_engine", max_hp=10)
        registry = fixture_entity_registry(definition)
        scaling = fixture_depth_scaling_config(
            fixture_difficulty_profile(
                stats={"max_hp": fixture_stat_schedule(per_floor=1)},
            )
        )
        # steps = 7-1 = 6 → max_hp 16
        entity = spawn_species_on_engine(
            engine,
            "on_engine",
            40,
            22,
            depth_scaling=scaling,
            registry=registry,
            carve=True,
        )
        assert entity.components[SpeciesId].id == "on_engine"
        assert entity.components[Fighter].max_hp == 16
        pos = position_of(entity)
        assert pos.x == 40
        assert pos.y == 22
