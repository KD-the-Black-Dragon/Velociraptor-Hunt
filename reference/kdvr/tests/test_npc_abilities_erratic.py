"""PR8: Erratic move-attack-move pattern."""

from __future__ import annotations

import random
from unittest.mock import patch

import pytest

from src.components import AIState, AbilityState, Alignment, Fighter, Position, Stunned
from src.engine import GameEngine
from src.systems.abilities import (
    ActionStepKind,
    compute_action_plan,
    erratic_pursuit_suppressed,
    has_erratic,
)
from src.systems.ai import run_monster_turns
from src.systems.ai.movement import _choose_erratic_random_direction
from src.systems.combat import try_action as real_try_action
from src.systems.fov import update_fov
from tests.map_test_helpers import (
    ARENA_X,
    ARENA_Y,
    carve_floor_rect,
    carve_horizontal_line,
    isolate_other_ais,
    spawn_wolf_with_abilities,
)


def _chebyshev(a: Position, b: Position) -> int:
    return max(abs(a.x - b.x), abs(a.y - b.y))


def _erratic_wolf(engine: GameEngine):
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, ["Erratic"])
    isolate_other_ais(engine, keep=(wolf,))
    return wolf


def test_erratic_ability_still_implemented() -> None:
    from src.data.abilities import filter_known_abilities
    from src.data.warnings import LoadWarnings

    assert filter_known_abilities("wolf", ["Erratic"], LoadWarnings()) == (
        "Erratic",
    )


def test_compute_action_plan_erratic_shape() -> None:
    engine = GameEngine()
    wolf = _erratic_wolf(engine)
    plan = compute_action_plan(wolf, 0)
    assert [step.kind for step in plan.steps] == [
        ActionStepKind.MOVE,
        ActionStepKind.ATTACK,
        ActionStepKind.MOVE,
    ]


def test_erratic_at_range_one_pursuit_and_one_random_move() -> None:
    """Distant target: pursuit MOVE + ATTACK no-op + random MOVE (not a second chase)."""
    engine = GameEngine()
    wolf = _erratic_wolf(engine)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X - 2, ARENA_Y, 8)
    player.components[Position] = Position(ARENA_X + 4, ARENA_Y)
    update_fov(engine.game_map, ARENA_X + 4, ARENA_Y)
    wolf_pos_before = wolf.components[Position]
    wolf_calls: list[tuple[int, int] | None] = []

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
            rng=random.Random(5),
        )
    # Erratic: intentional pursuit always tries to move; random step may stay (no try_action).
    assert len(wolf_calls) >= 1
    assert wolf_calls[0] is not None
    dx, dy = wolf_calls[0]
    after_pursuit = Position(wolf_pos_before.x + dx, wolf_pos_before.y + dy)
    assert _chebyshev(after_pursuit, player.components[Position]) < _chebyshev(
        wolf_pos_before, player.components[Position]
    )
    if len(wolf_calls) == 2:
        # Second action is random wander, not a second chase toward the player.
        d2 = wolf_calls[1]
        assert d2 is not None
        after_random = Position(after_pursuit.x + d2[0], after_pursuit.y + d2[1])
        # May or may not get closer; must not reverse onto pre-pursuit tile.
        assert after_random != wolf_pos_before
    else:
        assert len(wolf_calls) == 1


def test_erratic_attack_no_op_when_not_adjacent() -> None:
    engine = GameEngine()
    wolf = _erratic_wolf(engine)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 6)
    player.components[Position] = Position(ARENA_X + 3, ARENA_Y)
    update_fov(engine.game_map, ARENA_X + 3, ARENA_Y)
    engine.message_log = type(engine.message_log)()
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=random.Random(1),
    )
    text = " ".join(engine.message_log.lines())
    assert "shoots" not in text


def test_erratic_final_step_uses_random_wander() -> None:
    engine = GameEngine()
    wolf = _erratic_wolf(engine)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X - 2, ARENA_Y, 8)
    player.components[Position] = Position(ARENA_X + 4, ARENA_Y)
    update_fov(engine.game_map, ARENA_X + 4, ARENA_Y)
    wander_calls = 0

    def track_wander(world, game_map, monster, *args, **kwargs):
        nonlocal wander_calls
        if monster is wolf:
            wander_calls += 1
        return (1, 0)

    with (
        patch(
            "src.systems.ai.visit._choose_erratic_random_direction",
            side_effect=track_wander,
        ),
        patch(
            "src.systems.ai.movement._choose_erratic_random_direction",
            side_effect=track_wander,
        ),
    ):
        run_monster_turns(
            engine.world,
            engine.game_map,
            player,
            engine.message_log,
            rng=random.Random(5),
        )
    assert wander_calls == 1


def test_erratic_explore_takes_intentional_first_move(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exploring erratics must use intentional first MOVE (no explore idle skip)."""
    engine = GameEngine()
    wolf = _erratic_wolf(engine)
    player = engine.player
    assert player is not None
    # Player far away / no LOS to chase — force explore.
    player.components[Position] = Position(1, 1)
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X + 6, ARENA_Y)
    state = wolf.components[AIState]
    state.explore_goal = Position(ARENA_X + 6, ARENA_Y)
    state.last_known_primary = None
    # If idle were allowed, this would often skip the first step.
    monkeypatch.setattr("src.systems.ai.explore.EXPLORE_IDLE_CHANCE", 1.0)

    before = wolf.components[Position]
    wolf_calls: list[tuple[int, int] | None] = []

    def counting_try_action(world, game_map, actor, direction, message_log, **kwargs):
        if actor is wolf:
            wolf_calls.append(direction)
        return real_try_action(
            world, game_map, actor, direction, message_log, **kwargs
        )

    with patch("src.systems.ai.visit.try_action", side_effect=counting_try_action), patch(
        "src.systems.ai.movement.try_action", side_effect=counting_try_action
    ):
        run_monster_turns(
            engine.world,
            engine.game_map,
            player,
            engine.message_log,
            rng=random.Random(0),
        )

    # Intentional explore step must fire despite EXPLORE_IDLE_CHANCE=1.0
    assert len(wolf_calls) >= 1
    assert wolf_calls[0] is not None
    after_first = Position(before.x + wolf_calls[0][0], before.y + wolf_calls[0][1])
    assert after_first.x > before.x


def test_erratic_random_cannot_reverse_intentional_move() -> None:
    engine = GameEngine()
    wolf = _erratic_wolf(engine)
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X + 2, ARENA_Y)
    origin = Position(ARENA_X + 1, ARENA_Y)
    wolf.components[Position] = origin
    left_from = Position(ARENA_X, ARENA_Y)

    # Force many samples: reverse west to left_from must never appear.
    for seed in range(80):
        d = _choose_erratic_random_direction(
            engine.world,
            engine.game_map,
            wolf,
            origin,
            random.Random(seed),
            forbid_return_to=left_from,
        )
        assert d is not None
        if d != (0, 0):
            dest = origin + d
            assert dest != left_from


def test_erratic_random_includes_stay_option() -> None:
    engine = GameEngine()
    wolf = _erratic_wolf(engine)
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X + 2, ARENA_Y)
    wolf.components[Position] = Position(ARENA_X + 1, ARENA_Y)
    saw_stay = False
    for seed in range(100):
        d = _choose_erratic_random_direction(
            engine.world,
            engine.game_map,
            wolf,
            wolf.components[Position],
            random.Random(seed),
        )
        if d == (0, 0):
            saw_stay = True
            break
    assert saw_stay


def test_erratic_skips_pursuit_when_adjacent_opens_vore_modal() -> None:
    engine = GameEngine()
    wolf = _erratic_wolf(engine)
    player = engine.player
    assert player is not None
    carve_horizontal_line(engine, ARENA_X, ARENA_Y, 3)
    player.components[Position] = Position(ARENA_X + 1, ARENA_Y)
    player.components[Fighter].hp = 0
    player.tags.add(Stunned)
    update_fov(engine.game_map, ARENA_X + 1, ARENA_Y)
    assert erratic_pursuit_suppressed(
        wolf,
        engine.world,
        engine.game_map,
        player,
        alignment=Alignment.EVIL,
        player_engulfed=False,
    )
    wolf_calls: list[object] = []

    def counting_try_action(*args, **kwargs):
        actor = args[2]
        if actor is wolf:
            wolf_calls.append(actor)
        return real_try_action(*args, **kwargs)

    with patch("src.systems.ai.visit.try_action", side_effect=counting_try_action), patch("src.systems.ai.movement.try_action", side_effect=counting_try_action):
        opened = run_monster_turns(
            engine.world,
            engine.game_map,
            player,
            engine.message_log,
            rng=random.Random(0),
            modal=engine.vore_modal,
        )
    assert opened
    assert len(wolf_calls) == 0
    assert wolf.components[AbilityState].plan_step_index == 0


def test_non_erratic_wolf_single_step_plan() -> None:
    engine = GameEngine()
    wolf = spawn_wolf_with_abilities(engine.world, ARENA_X, ARENA_Y, [])
    assert not has_erratic(wolf)
    plan = compute_action_plan(wolf, 0)
    assert len(plan.steps) == 1
    assert plan.steps[0].kind == ActionStepKind.MOVE_OR_BUMP