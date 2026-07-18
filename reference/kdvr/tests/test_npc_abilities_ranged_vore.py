"""PR5: RangedVoreN — vore at Chebyshev distance [2, N] with pull-on-hit."""

from __future__ import annotations

import random
from unittest.mock import patch

import pytest

from src.components import Alignment, Engulfed, Fighter, Position, Predator, Stunned
from src.data.ability_parser import RangedVoreAbility, collapse_ranged_vore_tokens, parse_ability_token
from src.data.abilities import DOCUMENTED_ABILITIES, filter_known_abilities
from src.data.warnings import LoadWarnings
from src.engine import GameEngine
from src.systems.abilities import (
    has_ranged_vore_ability,
    max_ranged_vore_range,
    try_path_engagement,
)
from src.systems.ai import run_monster_turns, spawn_test_npc
from src.systems.fov import update_fov
from src.systems.vore import (
    ranged_vore_npc_prey,
    should_attempt_ranged_vore,
    should_attempt_vore,
    try_resolve_npc_ranged_vore,
    try_open_ranged_vore_modal,
    vore_decision_chance,
)
from tests.map_test_helpers import (
    ARENA_X,
    ARENA_Y,
    carve_horizontal_line,
    isolate_other_ais,
    spawn_wolf_with_abilities,
)


def _wolf_with_ranged_vore(engine: GameEngine, distance: int):
    isolate_other_ais(engine)
    return spawn_wolf_with_abilities(
        engine.world,
        ARENA_X,
        ARENA_Y,
        [f"RangedVore{distance}"],
    )


@pytest.mark.parametrize("distance", [2, 3, 5, 9])
def test_parse_ranged_vore_token(distance: int) -> None:
    token = f"RangedVore{distance}"
    assert parse_ability_token(token) == RangedVoreAbility(distance=distance)
    assert token in DOCUMENTED_ABILITIES


def test_parse_ranged_vore_rejects_invalid_tokens() -> None:
    assert parse_ability_token("RangedVore1") is None
    assert parse_ability_token("RangedVore10") is None


def test_collapse_ranged_vore_tokens_keeps_max() -> None:
    assert collapse_ranged_vore_tokens(["RangedVore2", "RangedVore5", "Coward"]) == (
        "Coward",
        "RangedVore5",
    )


@pytest.mark.parametrize("distance", [2, 3])
def test_filter_known_abilities_keeps_ranged_vore(distance: int) -> None:
    token = f"RangedVore{distance}"
    kept = filter_known_abilities("wolf", [token], LoadWarnings())
    assert kept == (token,)


@pytest.mark.parametrize("distance", [2, 4])
def test_spawned_wolf_max_ranged_vore_range_matches_token(distance: int) -> None:
    engine = GameEngine()
    wolf = _wolf_with_ranged_vore(engine, distance)
    assert max_ranged_vore_range(wolf) == distance
    assert has_ranged_vore_ability(wolf)


def test_ranged_vore_requires_distance_band() -> None:
    engine = GameEngine()
    wolf = _wolf_with_ranged_vore(engine, 3)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 5)
    player.components[Fighter].hp = 8
    player.components[Fighter].max_hp = 20
    wolf.components[Position] = Position(ARENA_X, ARENA_Y)
    player.components[Position] = Position(ARENA_X + 1, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    rng = random.Random(0)
    with patch.object(rng, "random", return_value=0.0):
        assert should_attempt_vore(wolf, player, engine.game_map, rng) is True
        assert should_attempt_ranged_vore(
            wolf, player, engine.game_map, rng, max_n=3
        ) is False
    player.components[Position] = Position(ARENA_X + 3, ARENA_Y)
    with patch.object(rng, "random", return_value=0.0):
        assert should_attempt_ranged_vore(
            wolf, player, engine.game_map, rng, max_n=3
        ) is True


def test_ranged_vore_npc_prey_lists_in_range_only() -> None:
    engine = GameEngine()
    wolf = _wolf_with_ranged_vore(engine, 3)
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 6)
    knight_near = spawn_test_npc(
        engine.world,
        x=ARENA_X + 1,
        y=ARENA_Y,
        species="knight",
        alignment=Alignment.GOOD,
        hp=10,
    )
    knight_near.components[Fighter].max_hp = 24
    knight_far = spawn_test_npc(
        engine.world,
        x=ARENA_X + 3,
        y=ARENA_Y,
        species="knight",
        alignment=Alignment.GOOD,
        hp=10,
    )
    knight_far.components[Fighter].max_hp = 24
    knight_out = spawn_test_npc(
        engine.world,
        x=ARENA_X + 5,
        y=ARENA_Y,
        species="knight",
        alignment=Alignment.GOOD,
        hp=10,
    )
    knight_out.components[Fighter].max_hp = 24
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    prey = ranged_vore_npc_prey(wolf, engine.world, engine.game_map, 3)
    assert knight_near not in prey
    assert knight_far in prey
    assert knight_out not in prey


def test_ranged_vore_can_target_stunned_prey_at_range() -> None:
    engine = GameEngine()
    wolf = _wolf_with_ranged_vore(engine, 3)
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 5)
    knight = spawn_test_npc(
        engine.world,
        x=ARENA_X + 2,
        y=ARENA_Y,
        species="knight",
        alignment=Alignment.GOOD,
        hp=0,
    )
    knight.tags.add(Stunned)
    knight.components[Fighter].max_hp = 24
    player = engine.player
    assert player is not None
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    assert knight in ranged_vore_npc_prey(wolf, engine.world, engine.game_map, 3)
    with patch("src.systems.vore.resolve_vore_hit", return_value=False):
        assert try_resolve_npc_ranged_vore(
            wolf,
            engine.world,
            engine.game_map,
            engine.message_log,
            random.Random(0),
        )


def test_ranged_vore_pulls_prey_on_hit() -> None:
    engine = GameEngine()
    wolf = _wolf_with_ranged_vore(engine, 3)
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 5)
    knight = spawn_test_npc(
        engine.world,
        x=ARENA_X + 2,
        y=ARENA_Y,
        species="knight",
        alignment=Alignment.GOOD,
        hp=10,
    )
    knight.components[Fighter].max_hp = 24
    wolf_pos = wolf.components[Position]
    update_fov(engine.game_map, wolf_pos.x, wolf_pos.y)
    rng = random.Random(0)
    with patch.object(rng, "random", return_value=0.0):
        with patch("src.systems.vore.resolve_vore_hit", return_value=True):
            assert try_resolve_npc_ranged_vore(
                wolf,
                engine.world,
                engine.game_map,
                engine.message_log,
                rng,
            )
    assert Engulfed in knight.tags
    assert wolf.components.get(Predator) is not None
    assert knight.components[Position] == wolf_pos


def test_ranged_vore_miss_leaves_prey_position() -> None:
    engine = GameEngine()
    wolf = _wolf_with_ranged_vore(engine, 3)
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 5)
    knight = spawn_test_npc(
        engine.world,
        x=ARENA_X + 2,
        y=ARENA_Y,
        species="knight",
        alignment=Alignment.GOOD,
        hp=10,
    )
    knight.components[Fighter].max_hp = 24
    start = Position(ARENA_X + 2, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    rng = random.Random(0)
    with patch.object(rng, "random", return_value=0.0):
        with patch("src.systems.vore.resolve_vore_hit", return_value=False):
            assert try_resolve_npc_ranged_vore(
                wolf,
                engine.world,
                engine.game_map,
                engine.message_log,
                rng,
            )
    assert knight.components[Position] == start
    assert Engulfed not in knight.tags


def test_prefer_vore_skips_ranged_decision_roll() -> None:
    engine = GameEngine()
    wolf = spawn_wolf_with_abilities(
        engine.world,
        ARENA_X,
        ARENA_Y,
        ["RangedVore3", "PreferVore"],
    )
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 5)
    player.components[Fighter].hp = 8
    player.components[Fighter].max_hp = 20
    assert vore_decision_chance(0.4) < 1.0
    player.components[Position] = Position(ARENA_X + 3, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    rng = random.Random(0)
    with patch.object(rng, "random", return_value=0.99):
        assert should_attempt_ranged_vore(
            wolf, player, engine.game_map, rng, max_n=3
        ) is True


def test_open_ranged_vore_modal_at_distance() -> None:
    from src.systems.vore import VoreModalState

    engine = GameEngine()
    wolf = _wolf_with_ranged_vore(engine, 3)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 5)
    player.components[Fighter].hp = 8
    player.components[Fighter].max_hp = 20
    player.components[Position] = Position(ARENA_X + 3, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    modal = VoreModalState()
    rng = random.Random(0)
    with patch.object(rng, "random", return_value=0.0):
        assert try_open_ranged_vore_modal(
            wolf,
            player,
            engine.game_map,
            modal,
            [],
            0,
            rng,
        )
    assert modal.active


def test_dual_tongue_path_when_prey_above_vore_threshold() -> None:
    engine = GameEngine()
    wolf = spawn_wolf_with_abilities(
        engine.world,
        ARENA_X,
        ARENA_Y,
        ["Range3", "RangedVore3"],
    )
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 5)
    player.components[Fighter].hp = 14
    player.components[Fighter].max_hp = 20
    player.components[Position] = Position(ARENA_X + 3, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    assert try_path_engagement(
        wolf,
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        random.Random(42),
        alignment=Alignment.EVIL,
        entity_target=player,
    )


def test_save_codec_encodes_ranged_vore_ability() -> None:
    from src.components import Abilities
    from src.data.ability_parser import parse_abilities
    from src.save.codec import assign_entity_ids, encode_entity_record, restore_entities
    from tcod.ecs import Registry

    world = Registry()
    wolf = spawn_wolf_with_abilities(world, ARENA_X, ARENA_Y, ["Range3", "RangedVore3"])
    assert wolf.components[Abilities].parsed == parse_abilities(["Range3", "RangedVore3"])
    id_map = assign_entity_ids([wolf])
    record = encode_entity_record(wolf, id_map[wolf], id_map)
    assert record["components"]["Abilities"]["tokens"] == ["Range3", "RangedVore3"]

    restored_world = Registry()
    restore_entities(restored_world, [record])
    restored = restored_world[id_map[wolf]]
    assert restored.components[Abilities].parsed == parse_abilities(["Range3", "RangedVore3"])


def test_dual_tongue_ranged_vore_before_path_when_weakened() -> None:
    engine = GameEngine()
    wolf = spawn_wolf_with_abilities(
        engine.world,
        ARENA_X,
        ARENA_Y,
        ["Range3", "RangedVore3"],
    )
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 5)
    player.components[Fighter].hp = 8
    player.components[Fighter].max_hp = 20
    player.components[Position] = Position(ARENA_X + 3, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    from src.systems.vore import VoreModalState

    modal = VoreModalState()
    rng = random.Random(0)
    with patch.object(rng, "random", return_value=0.0):
        with patch("src.systems.vore.resolve_vore_hit", return_value=False):
            run_monster_turns(
                engine.world,
                engine.game_map,
                player,
                engine.message_log,
                rng=rng,
                modal=modal,
            )
    assert modal.active