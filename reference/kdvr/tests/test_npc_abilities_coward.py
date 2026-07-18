"""PR6: Coward flee below 50% HP."""

from __future__ import annotations

import random

from src.components import Abilities, Alignment, Fighter, Position
from src.data.ability_parser import parse_abilities
from src.engine import GameEngine
from src.systems.abilities import coward_flee_direction, coward_should_flee, has_coward
from src.systems.ai import run_monster_turns, spawn_test_npc
from src.systems.fov import update_fov
from tests.map_test_helpers import (
    ARENA_X,
    ARENA_Y,
    carve_horizontal_line,
    isolate_other_ais,
    spawn_wolf_with_abilities,
)


def _chebyshev(a: Position, b: Position) -> int:
    return max(abs(a.x - b.x), abs(a.y - b.y))


def _attach_abilities(entity, tokens: list[str]) -> None:
    parsed = parse_abilities(tokens)
    entity.components[Abilities] = Abilities(parsed=parsed)


def _coward_wolf(engine: GameEngine, *, hp: int, max_hp: int = 24):
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, ["Coward"])
    wolf.components[Fighter].max_hp = max_hp
    wolf.components[Fighter].hp = hp
    isolate_other_ais(engine, keep=(wolf,))
    return wolf


def test_coward_should_flee_strictly_below_half() -> None:
    engine = GameEngine()
    wolf = _coward_wolf(engine, hp=11, max_hp=24)
    assert has_coward(wolf)
    assert coward_should_flee(wolf)
    wolf.components[Fighter].hp = 12
    assert not coward_should_flee(wolf)


def test_coward_knight_below_half_flees_visible_wolf() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 5)
    wolf = spawn_test_npc(
        engine.world,
        x=ARENA_X + 1,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
        hp=24,
    )
    wolf.components[Fighter].max_hp = 24
    knight = spawn_test_npc(
        engine.world,
        x=ARENA_X + 2,
        y=ARENA_Y,
        species="knight",
        alignment=Alignment.GOOD,
        hp=4,
    )
    knight.components[Fighter].max_hp = 10
    _attach_abilities(knight, ["Coward"])
    player = engine.player
    assert player is not None
    player.components[Position] = Position(ARENA_X, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    knight_pos_before = knight.components[Position]
    wolf_pos = wolf.components[Position]
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(0),
    )
    assert knight.components[Position] != knight_pos_before
    assert _chebyshev(knight.components[Position], wolf_pos) > _chebyshev(
        knight_pos_before, wolf_pos
    )


def test_coward_wolf_below_half_flees_player() -> None:
    engine = GameEngine()
    wolf = _coward_wolf(engine, hp=10, max_hp=24)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X - 2, ARENA_Y, 8)
    player.components[Position] = Position(ARENA_X + 3, ARENA_Y)
    update_fov(engine.game_map, ARENA_X + 3, ARENA_Y)
    wolf_pos_before = wolf.components[Position]
    player_pos = player.components[Position]
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(1),
    )
    assert wolf.components[Position] != wolf_pos_before
    assert _chebyshev(wolf.components[Position], player_pos) > _chebyshev(
        wolf_pos_before, player_pos
    )


def test_coward_neutral_full_hp_skips_flee_direction() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 8)
    wolf = spawn_test_npc(
        engine.world,
        x=ARENA_X + 2,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    rabbit = spawn_test_npc(
        engine.world,
        x=ARENA_X + 4,
        y=ARENA_Y,
        species="rabbit",
        alignment=Alignment.NEUTRAL,
        hp=8,
    )
    rabbit.components[Fighter].max_hp = 8
    _attach_abilities(rabbit, ["Coward"])
    player = engine.player
    assert player is not None
    player.components[Position] = Position(ARENA_X + 7, ARENA_Y)
    update_fov(engine.game_map, ARENA_X + 4, ARENA_Y)
    assert has_coward(rabbit)
    assert not coward_should_flee(rabbit)
    assert (
        coward_flee_direction(
            rabbit,
            engine.world,
            engine.game_map,
            player,
            random.Random(0),
            alignment=Alignment.NEUTRAL,
            blocked_tiles=frozenset(),
        )
        is None
    )