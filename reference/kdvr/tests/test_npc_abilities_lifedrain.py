"""PR12: Lifedrain heal on damage dealt."""

from __future__ import annotations

import random
from unittest.mock import patch

from src.components import Fighter, Position
from src.engine import GameEngine
from src.systems.abilities import has_lifedrain
from src.systems.combat import perform_npc_smite_attack, try_action
from src.systems.fov import update_fov
from tests.map_test_helpers import (
    ARENA_X,
    ARENA_Y,
    carve_horizontal_line,
    isolate_other_ais,
    spawn_wolf_with_abilities,
)


def _lifedrain_wolf(engine: GameEngine):
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, ["Lifedrain"])
    isolate_other_ais(engine, keep=(wolf,))
    return wolf


def _log_text(engine: GameEngine) -> str:
    return " ".join(engine.message_log.lines())


def test_lifedrain_ability_still_implemented() -> None:
    from src.data.abilities import filter_known_abilities
    from src.data.warnings import LoadWarnings

    assert filter_known_abilities("wolf", ["Lifedrain"], LoadWarnings()) == (
        "Lifedrain",
    )


def test_bump_lifedrain_heals_attacker_and_logs() -> None:
    engine = GameEngine()
    wolf = _lifedrain_wolf(engine)
    fighter = wolf.components[Fighter]
    fighter.max_hp = 20
    fighter.hp = 10
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 3)
    player.components[Position] = Position(ARENA_X + 1, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    engine.message_log = type(engine.message_log)()

    with patch("src.systems.combat.resolve_attack", return_value=(True, 4)):
        try_action(engine.world, engine.game_map, wolf, (1, 0), engine.message_log)

    assert wolf.components[Fighter].hp == 14
    text = _log_text(engine)
    assert "hits you for 4 damage" in text
    assert "appears healthier" in text


def test_lifedrain_no_log_when_already_at_max_hp() -> None:
    engine = GameEngine()
    wolf = _lifedrain_wolf(engine)
    fighter = wolf.components[Fighter]
    fighter.hp = fighter.max_hp
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 3)
    player.components[Position] = Position(ARENA_X + 1, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)
    engine.message_log = type(engine.message_log)()

    with patch("src.systems.combat.resolve_attack", return_value=(True, 4)):
        try_action(engine.world, engine.game_map, wolf, (1, 0), engine.message_log)

    assert wolf.components[Fighter].hp == fighter.max_hp
    assert "appears healthier" not in _log_text(engine)


def test_ranged_lifedrain_heals_attacker() -> None:
    engine = GameEngine()
    wolf = spawn_wolf_with_abilities(
        engine.world, ARENA_X, ARENA_Y, ["Smite2", "Lifedrain"]
    )
    isolate_other_ais(engine, keep=(wolf,))
    fighter = wolf.components[Fighter]
    fighter.max_hp = 20
    fighter.hp = 8
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

    assert wolf.components[Fighter].hp == 11
    assert "appears healthier" in _log_text(engine)


def test_without_lifedrain_no_heal_on_hit() -> None:
    engine = GameEngine()
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, [])
    assert not has_lifedrain(wolf)
    wolf.components[Fighter].hp = 10
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 3)
    player.components[Position] = Position(ARENA_X + 1, ARENA_Y)
    update_fov(engine.game_map, ARENA_X, ARENA_Y)

    with patch("src.systems.combat.resolve_attack", return_value=(True, 4)):
        try_action(engine.world, engine.game_map, wolf, (1, 0), engine.message_log)

    assert wolf.components[Fighter].hp == 10
    assert "appears healthier" not in _log_text(engine)