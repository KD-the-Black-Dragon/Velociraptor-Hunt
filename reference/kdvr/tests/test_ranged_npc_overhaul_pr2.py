"""PR2: RangedMagazine spawn, spend, reload, save."""

from __future__ import annotations

import random

from src.components import (
    Abilities,
    AbilityState,
    Alignment,
    Fighter,
    Position,
    RangedMagazine,
)
from src.data.ability_parser import parse_abilities
from src.data.depth_scaling_loader import default_depth_scaling_config, reset_depth_scaling_cache
from src.engine import GameEngine
from src.spawn import spawn_from_definition
from src.systems.abilities import try_path_engagement, try_smite_engagement
from src.systems.fov import update_fov
from src.systems.ranged_magazine import (
    can_spend_ranged_shot,
    ensure_ranged_magazine,
    spend_ranged_shot,
    try_ranged_reload,
)
from src.systems.vore import try_resolve_npc_ranged_vore
from tests.entity_test_helpers import fixture_wolf_payload, parse_entity_registry
from tests.map_test_helpers import (
    ARENA_X,
    ARENA_Y,
    carve_horizontal_line,
    isolate_other_ais,
    spawn_wolf_with_abilities,
)


def test_spawn_attaches_full_magazine_from_difficulty() -> None:
    reset_depth_scaling_cache()
    engine = GameEngine(difficulty_id="nightmare")
    isolate_other_ais(engine)
    registry = parse_entity_registry(
        {
            "schema_version": 1,
            "entities": [
                fixture_wolf_payload(
                    id="shot_fox",
                    abilities=["Range5"],
                    ranged_min_damage=3,
                    ranged_max_damage=3,
                    ranged_accuracy=5.0,
                )
            ],
        }
    )
    fox = spawn_from_definition(
        engine.world,
        registry.by_id()["shot_fox"],
        ARENA_X,
        ARENA_Y,
        difficulty_id="nightmare",
    )
    mag = fox.components[RangedMagazine]
    assert mag.maximum == 3  # evil nightmare
    assert mag.current == 3


def test_good_spawn_uses_good_ranged_shots() -> None:
    reset_depth_scaling_cache()
    engine = GameEngine(difficulty_id="normal")
    isolate_other_ais(engine)
    registry = parse_entity_registry(
        {
            "schema_version": 1,
            "entities": [
                fixture_wolf_payload(
                    id="shot_ally",
                    alignment="good",
                    abilities=["Smite5"],
                    ranged_min_damage=3,
                    ranged_max_damage=3,
                    ranged_accuracy=5.0,
                    digestion_damage_per_tick=None,
                    digest_time=None,
                    vore_narratives={},
                )
            ],
        }
    )
    # good entities may need cleaned payload — use spawn_test style if load fails
    definition = registry.by_id()["shot_ally"]
    ally = spawn_from_definition(
        engine.world,
        definition,
        ARENA_X,
        ARENA_Y,
        difficulty_id="normal",
    )
    mag = ally.components[RangedMagazine]
    assert mag.maximum == 2
    assert mag.current == 2


def test_cannot_shoot_at_zero_shots() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, ["Smite5"])
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 6)
    player.components[Position] = Position(ARENA_X + 3, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    mag = wolf.components[RangedMagazine]
    mag.current = 0
    assert not can_spend_ranged_shot(wolf)
    fired = try_smite_engagement(
        wolf,
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        random.Random(0),
        alignment=Alignment.EVIL,
        entity_target=player,
    )
    assert fired is False
    assert mag.current == 0


def test_smite_spend_decrements_magazine() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, ["Smite5"])
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 6)
    player.components[Position] = Position(ARENA_X + 3, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    mag = wolf.components[RangedMagazine]
    assert mag.current == 2
    fired = try_smite_engagement(
        wolf,
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        random.Random(0),
        alignment=Alignment.EVIL,
        entity_target=player,
    )
    assert fired is True
    assert mag.current == 1


def test_reload_caps_at_maximum() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, ["Range3"])
    mag = wolf.components[RangedMagazine]
    mag.current = 0
    assert try_ranged_reload(wolf) is True
    assert mag.current == 1
    assert try_ranged_reload(wolf) is True
    assert mag.current == 2
    assert try_ranged_reload(wolf) is False
    assert mag.current == 2


def test_ranged_vore_does_not_spend_shot() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    wolf = spawn_wolf_with_abilities(
        engine.world, ARENA_X, ARENA_Y, ["Range3", "RangedVore3", "PreferVore"]
    )
    from src.systems.ai import spawn_test_npc

    prey = spawn_test_npc(
        engine.world,
        x=ARENA_X + 2,
        y=ARENA_Y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
        hp=1,
    )
    prey.components[Fighter].hp = 1
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 5)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    mag = wolf.components[RangedMagazine]
    before = mag.current
    # PreferVore + low HP should attempt; may or may not hit
    try_resolve_npc_ranged_vore(
        wolf,
        engine.world,
        engine.game_map,
        engine.message_log,
        random.Random(0),
    )
    assert mag.current == before


def test_magazine_save_round_trip() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, ["Smite5"])
    wolf.components[RangedMagazine].current = 1
    snapshot = engine.build_run_snapshot()
    restored = GameEngine.from_run_snapshot(snapshot)
    found = None
    for entity in restored.world.Q.all_of(components=[RangedMagazine]):
        found = entity
        break
    assert found is not None
    mag = found.components[RangedMagazine]
    assert mag.current == 1
    assert mag.maximum == 2


def test_missing_magazine_on_load_soft_fills() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, ["Smite5"])
    snapshot = engine.build_run_snapshot()
    # Strip magazine from encoded entity to simulate old save
    for record in snapshot["entities"]:
        comps = record.get("components", {})
        if "RangedMagazine" in comps and "Abilities" in comps:
            del comps["RangedMagazine"]
    restored = GameEngine.from_run_snapshot(snapshot)
    found = None
    for entity in restored.world.Q.all_of(components=[RangedMagazine, Abilities]):
        tokens = [
            type(p).__name__ for p in entity.components[Abilities].parsed
        ]
        if any("Smite" in t or t == "SmiteAbility" for t in tokens):
            found = entity
            break
    assert found is not None
    mag = found.components[RangedMagazine]
    assert mag.current == mag.maximum == 2
