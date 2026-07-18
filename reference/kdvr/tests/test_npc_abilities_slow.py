"""PR9: Slow skip every other turn."""

from __future__ import annotations

import random
from unittest.mock import patch

import pytest

from src.components import Position
from src.engine import GameEngine
from src.systems.abilities import ActionStepKind, compute_action_plan, has_slow
from src.systems.ai import run_monster_turns
from src.systems.combat import try_action as real_try_action
from src.systems.fov import update_fov
from tests.map_test_helpers import (
    ARENA_X,
    ARENA_Y,
    carve_horizontal_line,
    isolate_other_ais,
    spawn_wolf_with_abilities,
)


def _slow_wolf(engine: GameEngine):
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, ["Slow"])
    isolate_other_ais(engine, keep=(wolf,))
    return wolf


def test_slow_ability_still_implemented() -> None:
    from src.data.abilities import filter_known_abilities
    from src.data.warnings import LoadWarnings

    assert filter_known_abilities("wolf", ["Slow"], LoadWarnings()) == ("Slow",)


@pytest.mark.parametrize(
    ("turn_count", "should_act"),
    [
        (0, True),
        (1, False),
        (2, True),
        (3, False),
    ],
)
def test_compute_action_plan_slow_parity(turn_count: int, should_act: bool) -> None:
    engine = GameEngine()
    wolf = _slow_wolf(engine)
    plan = compute_action_plan(wolf, turn_count)
    if should_act:
        assert [step.kind for step in plan.steps] == [ActionStepKind.MOVE_OR_BUMP]
    else:
        assert [step.kind for step in plan.steps] == [ActionStepKind.SKIP]


@pytest.mark.parametrize(
    ("turn_count", "should_act"),
    [
        (0, True),
        (1, False),
        (2, True),
        (3, False),
    ],
)
def test_slow_wolf_visit_parity(
    turn_count: int,
    should_act: bool,
) -> None:
    engine = GameEngine()
    wolf = _slow_wolf(engine)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X - 2, ARENA_Y, 8)
    player.components[Position] = Position(ARENA_X + 4, ARENA_Y)
    update_fov(engine.game_map, ARENA_X + 4, ARENA_Y)
    start_pos = wolf.components[Position]
    wolf_calls: list[object] = []

    def counting_try_action(world, game_map, actor, direction, message_log, **kwargs):
        if actor is wolf:
            wolf_calls.append(direction)
        return real_try_action(
            world, game_map, actor, direction, message_log, **kwargs
        )

    with patch("src.systems.ai.visit.try_action", side_effect=counting_try_action), patch("src.systems.ai.movement.try_action", side_effect=counting_try_action):
        run_monster_turns(
            engine.world,
            engine.game_map,
            player,
            engine.message_log,
            rng=random.Random(turn_count),
            player_turn_count=turn_count,
        )

    if should_act:
        assert len(wolf_calls) >= 1
        assert wolf.components[Position] != start_pos
    else:
        assert len(wolf_calls) == 0
        assert wolf.components[Position] == start_pos


def test_non_slow_wolf_single_step_plan() -> None:
    engine = GameEngine()
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, [])
    assert not has_slow(wolf)
    plan = compute_action_plan(wolf, 1)
    assert len(plan.steps) == 1
    assert plan.steps[0].kind == ActionStepKind.MOVE_OR_BUMP