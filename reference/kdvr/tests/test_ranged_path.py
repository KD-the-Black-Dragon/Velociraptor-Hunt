"""Path-targeted ranged beam resolution and NPC path attacks."""

from __future__ import annotations

import random
from unittest.mock import patch

from src.components import Alignment, Fighter, Position, Stunned
from src.engine import GameEngine
from src.map_gen import Tile
from src.systems.combat import perform_npc_path_attack
from src.systems.fov import update_fov
from src.systems.ranged_path import PathShotStatus, resolve_path_shot
from src.systems.ai import spawn_test_npc
from tests.map_test_helpers import (
    ARENA_X,
    ARENA_Y,
    carve_floor_rect,
    carve_horizontal_line,
    isolate_other_ais,
    spawn_wolf_with_abilities,
)


def test_evil_shot_blocked_by_evil_on_path() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 5)
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, [])
    blocker = spawn_test_npc(
        engine.world,
        x=ARENA_X + 1,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    player = engine.player
    assert player is not None
    player.components[Position] = Position(ARENA_X + 3, ARENA_Y)
    result = resolve_path_shot(engine.world, engine.game_map, wolf, player)
    assert result.status is PathShotStatus.BLOCKED


def test_evil_shot_hits_player_with_clear_path() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 4)
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, [])
    player = engine.player
    assert player is not None
    player.components[Position] = Position(ARENA_X + 2, ARENA_Y)
    result = resolve_path_shot(engine.world, engine.game_map, wolf, player)
    assert result.status is PathShotStatus.HIT
    assert result.defender is player


def test_player_shot_blocked_by_good_on_path() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 5)
    player = engine.player
    assert player is not None
    player.components[Position] = Position(ARENA_X, ARENA_Y)
    knight = spawn_test_npc(
        engine.world,
        x=ARENA_X + 1,
        y=ARENA_Y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    evil = spawn_test_npc(
        engine.world,
        x=ARENA_X + 3,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    result = resolve_path_shot(engine.world, engine.game_map, player, evil)
    assert result.status is PathShotStatus.BLOCKED
    assert knight.components[Position].x == ARENA_X + 1


def test_player_beam_hits_first_evil_not_intended() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 5)
    player = engine.player
    assert player is not None
    player.components[Position] = Position(ARENA_X, ARENA_Y)
    front = spawn_test_npc(
        engine.world,
        x=ARENA_X + 1,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    rear = spawn_test_npc(
        engine.world,
        x=ARENA_X + 3,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    result = resolve_path_shot(engine.world, engine.game_map, player, rear)
    assert result.status is PathShotStatus.HIT
    assert result.defender is front


def test_wall_on_path_returns_no_line() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 4)
    game_map = engine.game_map
    game_map.tiles[ARENA_Y, ARENA_X + 1] = Tile.WALL
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, [])
    player = engine.player
    assert player is not None
    player.components[Position] = Position(ARENA_X + 3, ARENA_Y)
    result = resolve_path_shot(engine.world, game_map, wolf, player)
    assert result.status is PathShotStatus.NO_LINE


def test_stunned_prey_does_not_block_beam() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 5)
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, [])
    knight = spawn_test_npc(
        engine.world,
        x=ARENA_X + 1,
        y=ARENA_Y,
        species="knight",
        alignment=Alignment.GOOD,
        hp=0,
    )
    knight.tags.add(Stunned)
    player = engine.player
    assert player is not None
    player.components[Position] = Position(ARENA_X + 3, ARENA_Y)
    result = resolve_path_shot(engine.world, engine.game_map, wolf, player)
    assert result.status is PathShotStatus.HIT
    assert result.defender is player


def test_perform_npc_path_attack_uses_shoot_logs() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 4)
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, [])
    player = engine.player
    assert player is not None
    player.components[Position] = Position(ARENA_X + 2, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    engine.message_log = type(engine.message_log)()

    with patch("src.systems.combat.resolve_attack", return_value=(True, 4)):
        attempted = perform_npc_path_attack(
            wolf,
            player,
            engine.message_log,
            world=engine.world,
            game_map=engine.game_map,
            rng=random.Random(0),
        )

    assert attempted is True
    text = " ".join(engine.message_log.lines())
    assert "shoots you for 4 damage" in text
    assert "smites" not in text


def test_perform_npc_path_attack_returns_false_when_blocked() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 5)
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, [])
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
    engine.message_log = type(engine.message_log)()

    attempted = perform_npc_path_attack(
        wolf,
        player,
        engine.message_log,
        world=engine.world,
        game_map=engine.game_map,
        rng=random.Random(0),
    )

    assert attempted is False
    assert not engine.message_log.lines()


def test_good_archer_path_shot_hits_evil() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    carve_floor_rect(engine, ARENA_X, ARENA_Y - 1, ARENA_X + 4, ARENA_Y + 1)
    knight = spawn_test_npc(
        engine.world,
        x=ARENA_X,
        y=ARENA_Y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    evil = spawn_test_npc(
        engine.world,
        x=ARENA_X + 2,
        y=ARENA_Y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    result = resolve_path_shot(engine.world, engine.game_map, knight, evil)
    assert result.status is PathShotStatus.HIT
    assert result.defender is evil