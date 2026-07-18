"""PR11: Knockback on successful melee and ranged damage."""

from __future__ import annotations

import random
from unittest.mock import patch

from src.components import Alignment, Position
from src.engine import GameEngine
from src.map_gen import Tile
from src.systems.abilities import has_knockback
from src.systems.combat import perform_npc_smite_attack, try_action
from src.systems.fov import update_fov
from tests.map_test_helpers import (
    ARENA_X,
    ARENA_Y,
    carve_floor_tile,
    carve_horizontal_line,
    isolate_other_ais,
    spawn_wolf_with_abilities,
)


def _knockback_wolf(engine: GameEngine):
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, ["Knockback"])
    isolate_other_ais(engine, keep=(wolf,))
    return wolf


def _log_text(engine: GameEngine) -> str:
    return " ".join(engine.message_log.lines())


def test_knockback_ability_still_implemented() -> None:
    from src.data.abilities import filter_known_abilities
    from src.data.warnings import LoadWarnings

    assert filter_known_abilities("wolf", ["Knockback"], LoadWarnings()) == (
        "Knockback",
    )


def test_bump_knockback_pushes_player_and_logs() -> None:
    engine = GameEngine()
    wolf = _knockback_wolf(engine)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 3)
    player.components[Position] = Position(ARENA_X + 1, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    engine.message_log = type(engine.message_log)()

    with patch("src.systems.combat.resolve_attack", return_value=(True, 4)):
        try_action(engine.world, engine.game_map, wolf, (1, 0), engine.message_log)

    assert player.components[Position] == Position(ARENA_X + 2, ARENA_Y)
    text = _log_text(engine)
    assert "hits you for 4 damage" in text
    assert "You are knocked back!" in text


def test_bump_knockback_no_log_when_push_blocked() -> None:
    engine = GameEngine()
    wolf = _knockback_wolf(engine)
    player = engine.player
    assert player is not None
    carve_floor_tile(engine, ARENA_X, ARENA_Y)
    carve_floor_tile(engine, ARENA_X + 1, ARENA_Y)
    engine.game_map.tiles[ARENA_Y, ARENA_X + 2] = Tile.WALL
    player.components[Position] = Position(ARENA_X + 1, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    engine.message_log = type(engine.message_log)()
    start_pos = player.components[Position]

    with patch("src.systems.combat.resolve_attack", return_value=(True, 2)):
        try_action(engine.world, engine.game_map, wolf, (1, 0), engine.message_log)

    assert player.components[Position] == start_pos
    assert "knocked back" not in _log_text(engine)


def test_bump_knockback_blocked_by_deep_water() -> None:
    engine = GameEngine()
    wolf = _knockback_wolf(engine)
    player = engine.player
    assert player is not None
    carve_floor_tile(engine, ARENA_X, ARENA_Y)
    carve_floor_tile(engine, ARENA_X + 1, ARENA_Y)
    engine.game_map.tiles[ARENA_Y, ARENA_X + 2] = Tile.DEEP_WATER
    player.components[Position] = Position(ARENA_X + 1, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    engine.message_log = type(engine.message_log)()

    with patch("src.systems.combat.resolve_attack", return_value=(True, 2)):
        try_action(engine.world, engine.game_map, wolf, (1, 0), engine.message_log)

    assert player.components[Position] == Position(ARENA_X + 1, ARENA_Y)
    assert "knocked back" not in _log_text(engine)


def test_ranged_knockback_pushes_player() -> None:
    engine = GameEngine()
    wolf = spawn_wolf_with_abilities(
        engine.world, ARENA_X, ARENA_Y, ["Smite2", "Knockback"]
    )
    isolate_other_ais(engine, keep=(wolf,))
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 4)
    player.components[Position] = Position(ARENA_X + 2, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    engine.message_log = type(engine.message_log)()

    with patch("src.systems.combat.resolve_attack", return_value=(True, 3)):
        perform_npc_smite_attack(
            wolf,
            player,
            engine.message_log,
            world=engine.world,
            game_map=engine.game_map,
            rng=random.Random(0),
        )

    assert player.components[Position] == Position(ARENA_X + 3, ARENA_Y)
    text = _log_text(engine)
    assert "smites you for 3 damage" in text
    assert "You are knocked back!" in text


def test_without_knockback_ability_no_push() -> None:
    engine = GameEngine()
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, [])
    assert not has_knockback(wolf)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 3)
    player.components[Position] = Position(ARENA_X + 1, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)

    with patch("src.systems.combat.resolve_attack", return_value=(True, 2)):
        try_action(engine.world, engine.game_map, wolf, (1, 0), engine.message_log)

    assert player.components[Position] == Position(ARENA_X + 1, ARENA_Y)