"""PR10: Fast double action per world phase."""

from __future__ import annotations

import random
from unittest.mock import patch

import pytest

from src.components import AbilityState, Fighter, Position, Stunned
from src.engine import GameEngine
from src.systems.abilities import ActionStepKind, compute_action_plan, has_fast
from src.systems.ai import _sorted_monsters, run_monster_turns
from src.systems.combat import try_action as real_try_action
from src.systems.fov import update_fov
from src.systems.vore import VoreModalSegment
from tests.map_test_helpers import (
    ARENA_X,
    ARENA_Y,
    carve_horizontal_line,
    isolate_other_ais,
    spawn_wolf_with_abilities,
)


def _fast_wolf(engine: GameEngine):
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, ["Fast"])
    isolate_other_ais(engine, keep=(wolf,))
    return wolf


def test_fast_ability_still_implemented() -> None:
    from src.data.abilities import filter_known_abilities
    from src.data.warnings import LoadWarnings

    assert filter_known_abilities("wolf", ["Fast"], LoadWarnings()) == ("Fast",)


def test_compute_action_plan_fast_shape() -> None:
    engine = GameEngine()
    wolf = _fast_wolf(engine)
    plan = compute_action_plan(wolf, 0)
    assert [step.kind for step in plan.steps] == [
        ActionStepKind.MOVE_OR_BUMP,
        ActionStepKind.MOVE_OR_BUMP,
    ]


def test_compute_action_plan_fast_plus_erratic_shape() -> None:
    engine = GameEngine()
    wolf = spawn_wolf_with_abilities(
        engine.world, ARENA_X, ARENA_Y, ["Fast", "Erratic"]
    )
    plan = compute_action_plan(wolf, 0)
    assert [step.kind for step in plan.steps] == [
        ActionStepKind.MOVE,
        ActionStepKind.ATTACK,
        ActionStepKind.MOVE,
        ActionStepKind.MOVE,
        ActionStepKind.ATTACK,
        ActionStepKind.MOVE,
    ]


@pytest.mark.parametrize("turn_count", [1, 3])
def test_compute_action_plan_fast_plus_slow_odd_is_skip(turn_count: int) -> None:
    engine = GameEngine()
    wolf = spawn_wolf_with_abilities(
        engine.world, ARENA_X, ARENA_Y, ["Fast", "Slow"]
    )
    plan = compute_action_plan(wolf, turn_count)
    assert [step.kind for step in plan.steps] == [ActionStepKind.SKIP]


def test_compute_action_plan_fast_plus_slow_even_is_double_bump() -> None:
    engine = GameEngine()
    wolf = spawn_wolf_with_abilities(
        engine.world, ARENA_X, ARENA_Y, ["Fast", "Slow"]
    )
    plan = compute_action_plan(wolf, 0)
    assert [step.kind for step in plan.steps] == [
        ActionStepKind.MOVE_OR_BUMP,
        ActionStepKind.MOVE_OR_BUMP,
    ]


def test_fast_wolf_two_moves_at_range() -> None:
    engine = GameEngine()
    wolf = _fast_wolf(engine)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X - 2, ARENA_Y, 8)
    player.components[Position] = Position(ARENA_X + 4, ARENA_Y)
    update_fov(engine.game_map, ARENA_X + 4, ARENA_Y)
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
            rng=random.Random(3),
            player_turn_count=0,
        )
    assert len(wolf_calls) == 2


def test_fast_modal_on_first_step_aborts_second() -> None:
    engine = GameEngine()
    wolf = _fast_wolf(engine)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 3)
    player.components[Position] = Position(ARENA_X + 1, ARENA_Y)
    player.components[Fighter].hp = 0
    player.tags.add(Stunned)
    update_fov(engine.game_map, ARENA_X + 1, ARENA_Y)
    pipeline_calls = 0

    def counting_pipeline(*args, **kwargs):
        nonlocal pipeline_calls
        pipeline_calls += 1
        if pipeline_calls == 1:
            return "open_modal"
        raise AssertionError("second Fast step should not run after modal abort")

    with patch(
        "src.systems.ai.visit._execute_intent_pipeline",
        side_effect=counting_pipeline,
    ):
        opened = run_monster_turns(
            engine.world,
            engine.game_map,
            player,
            engine.message_log,
            rng=random.Random(0),
            modal=engine.vore_modal,
            player_turn_count=0,
        )
    assert opened
    assert pipeline_calls == 1
    assert wolf.components[AbilityState].plan_step_index == 0


def test_fast_miss_resume_skips_opener_no_second_step_replay() -> None:
    engine = GameEngine()
    wolf = _fast_wolf(engine)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 5)
    player.components[Position] = Position(ARENA_X + 1, ARENA_Y)
    player.components[Fighter].hp = 0
    player.tags.add(Stunned)
    runner = spawn_wolf_with_abilities(
        engine.world, ARENA_X + 3, ARENA_Y, ["Fast"]
    )
    update_fov(engine.game_map, ARENA_X + 1, ARENA_Y)
    monsters = _sorted_monsters(engine.world)
    opener_index = monsters.index(wolf)
    runner_index = monsters.index(runner)
    assert opener_index < runner_index

    acted: list[object] = []

    def counting_try_action(world, game_map, actor, direction, message_log, **kwargs):
        acted.append(actor)
        return real_try_action(
            world, game_map, actor, direction, message_log, **kwargs
        )

    with patch("src.systems.ai.visit.try_action", side_effect=counting_try_action), patch("src.systems.ai.movement.try_action", side_effect=counting_try_action):
        with patch("src.systems.vore.resolve_vore_hit", return_value=False):
            engine._consume_player_turn()
            assert engine.vore_modal.active
            assert engine.vore_modal.resume_monster_index == opener_index
            engine.vore_modal.segment = VoreModalSegment.NONE
            engine.vore_modal.resume_monster_index = opener_index + 1
            run_monster_turns(
                engine.world,
                engine.game_map,
                player,
                engine.message_log,
                rng=engine.rng,
                modal=engine.vore_modal,
                player_turn_count=engine.player_turn_count,
            )

    assert wolf not in acted
    assert runner in acted


def test_fast_after_miss_next_turn_runs_both_steps_from_zero() -> None:
    engine = GameEngine()
    wolf = _fast_wolf(engine)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X - 2, ARENA_Y, 8)
    player.components[Position] = Position(ARENA_X + 4, ARENA_Y)
    update_fov(engine.game_map, ARENA_X + 4, ARENA_Y)

    with patch("src.systems.vore.resolve_vore_hit", return_value=False):
        carve_horizontal_line(engine, ARENA_X, ARENA_Y, 3)
        player.components[Position] = Position(ARENA_X + 1, ARENA_Y)
        player.components[Fighter].hp = 0
        player.tags.add(Stunned)
        update_fov(engine.game_map, ARENA_X + 1, ARENA_Y)
        engine._consume_player_turn()
        while engine.vore_modal.active:
            engine.vore_modal.segment = VoreModalSegment.NONE
            engine.vore_modal.reset()

    wolf.components[Position] = Position(ARENA_X, ARENA_Y)
    player.components[Position] = Position(ARENA_X + 4, ARENA_Y)
    player.components[Fighter].hp = 10
    player.tags.discard(Stunned)
    update_fov(engine.game_map, ARENA_X + 4, ARENA_Y)
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
            rng=random.Random(4),
            player_turn_count=engine.player_turn_count,
        )

    assert len(wolf_calls) == 2
    assert wolf.components[AbilityState].plan_step_index == 0


def test_non_fast_wolf_single_step_plan() -> None:
    engine = GameEngine()
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, [])
    assert not has_fast(wolf)
    plan = compute_action_plan(wolf, 0)
    assert len(plan.steps) == 1
    assert plan.steps[0].kind == ActionStepKind.MOVE_OR_BUMP