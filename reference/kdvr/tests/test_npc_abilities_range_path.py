"""RangeN (2–9) Path-targeted attack and engagement AI."""

from __future__ import annotations

import random

import pytest

from src.components import Alignment, Position, Stunned
from src.data.abilities import filter_known_abilities
from src.data.warnings import LoadWarnings
from src.engine import GameEngine
from src.systems.abilities import (
    max_path_range,
    pick_evil_path_target,
    try_path_engagement,
)
from src.systems.ai import run_monster_turns, spawn_test_npc
from src.systems.fov import update_fov
from tests.map_test_helpers import (
    ARENA_X,
    ARENA_Y,
    carve_horizontal_line,
    isolate_other_ais,
    spawn_wolf_with_abilities,
)


def _wolf_with_range(engine: GameEngine, distance: int):
    isolate_other_ais(engine)
    return spawn_wolf_with_abilities(
        engine.world,
        ARENA_X,
        ARENA_Y,
        [f"Range{distance}"],
    )


@pytest.mark.parametrize("distance", [2, 3, 4, 5])
def test_filter_known_abilities_keeps_range_tokens(distance: int) -> None:
    token = f"Range{distance}"
    kept = filter_known_abilities("wolf", [token], LoadWarnings())
    assert kept == (token,)


@pytest.mark.parametrize("distance", [2, 3, 5])
def test_spawned_wolf_max_path_range_matches_token(distance: int) -> None:
    engine = GameEngine()
    wolf = _wolf_with_range(engine, distance)
    assert max_path_range(wolf) == distance


@pytest.mark.parametrize("distance", [2, 3])
def test_wolf_shoots_player_at_max_range(distance: int) -> None:
    engine = GameEngine()
    wolf = _wolf_with_range(engine, distance)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, distance + 2)
    player.components[Position] = Position(ARENA_X + distance, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    engine.message_log = type(engine.message_log)()
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(42),
    )
    text = " ".join(entry.text for entry in engine.message_log.entries())
    assert "shoots you" in text
    assert "smites" not in text


def test_wolf_does_not_shoot_adjacent_player() -> None:
    engine = GameEngine()
    wolf = _wolf_with_range(engine, 2)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 3)
    wolf.components[Position] = Position(ARENA_X, ARENA_Y)
    player.components[Position] = Position(ARENA_X + 1, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    engine.message_log = type(engine.message_log)()
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(42),
    )
    text = " ".join(entry.text for entry in engine.message_log.entries())
    assert "shoots" not in text


def test_path_shot_blocked_by_evil_ally_skips_turn_damage() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 5)
    wolf = _wolf_with_range(engine, 3)
    spawn_test_npc(
        engine.world,
        x=ARENA_X + 1,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    player = engine.player
    assert player is not None
    player.components[Position] = Position(ARENA_X + 3, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    assert not try_path_engagement(
        wolf,
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        random.Random(0),
        alignment=Alignment.EVIL,
        entity_target=player,
    )


def test_pick_evil_path_target_requires_clear_beam() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 5)
    wolf = _wolf_with_range(engine, 3)
    spawn_test_npc(
        engine.world,
        x=ARENA_X + 1,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    player = engine.player
    assert player is not None
    player.components[Position] = Position(ARENA_X + 3, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    assert pick_evil_path_target(
        wolf,
        engine.world,
        engine.game_map,
        player,
        random.Random(0),
        max_n=3,
    ) is None


def test_no_path_shot_stunned_knight_in_range() -> None:
    engine = GameEngine()
    wolf = _wolf_with_range(engine, 2)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 4)
    knight = spawn_test_npc(
        engine.world,
        x=ARENA_X + 2,
        y=ARENA_Y,
        species="knight",
        alignment=Alignment.GOOD,
        hp=0,
    )
    knight.tags.add(Stunned)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    assert not try_path_engagement(
        wolf,
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        random.Random(0),
        alignment=Alignment.EVIL,
        entity_target=knight,
    )