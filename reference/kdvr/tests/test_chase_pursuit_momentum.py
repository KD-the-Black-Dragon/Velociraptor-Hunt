"""PR9: blind chase momentum and frustration give-up for good/evil NPCs."""

from __future__ import annotations

import random

from src.components import AI, AIState, Alignment, Position
from src.engine import GameEngine
from src.map_gen import Tile
from src.systems.ai import (
    CHASE_FRUSTRATION_MAX,
    CHASE_MOMENTUM_TURNS_MAX,
    _choose_momentum_direction,
    _complete_pursuit_step,
    _get_ai_state,
    _on_quarry_memory_reached,
    _pick_pursuit_direction,
    _record_memory_pursuit_blocked,
    _reset_chase_pursuit,
    _start_chase_momentum,
    pick_evil_chase,
    run_monster_turns,
    spawn_test_npc,
)
from src.systems.fov import update_fov

from tests.map_test_helpers import (
    ARENA_X,
    ARENA_Y,
    carve_floor_rect,
    carve_floor_tile,
    first_wolf,
    isolate_other_ais,
)


def test_momentum_starts_when_memory_reached_without_los() -> None:
    state = AIState(chase_momentum_direction=(1, 0))
    rng = random.Random(3)
    _on_quarry_memory_reached(
        state,
        rng,
        consumed_quarry=True,
        quarry_visible=False,
        alignment=Alignment.EVIL,
    )
    assert 3 <= state.chase_momentum_turns_left <= CHASE_MOMENTUM_TURNS_MAX
    assert state.chase_frustration_limit == 0


def test_momentum_direction_uses_preferred_step_when_legal() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    wolf = first_wolf(engine)
    carve_floor_tile(engine, ARENA_X, ARENA_Y)
    carve_floor_tile(engine, ARENA_X + 1, ARENA_Y)
    wolf.components[Position] = Position(ARENA_X, ARENA_Y)
    state = _get_ai_state(wolf)
    state.chase_momentum_direction = (1, 0)
    direction = _choose_momentum_direction(
        engine.world,
        engine.game_map,
        wolf,
        wolf.components[Position],
        state,
        blocked_tiles=frozenset(),
    )
    assert direction == (1, 0)


def test_momentum_direction_never_backtracks() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    wolf = first_wolf(engine)
    carve_floor_tile(engine, ARENA_X, ARENA_Y)
    carve_floor_tile(engine, ARENA_X, ARENA_Y - 1)
    engine.game_map.tiles[ARENA_Y, ARENA_X + 1] = Tile.WALL
    wolf.components[Position] = Position(ARENA_X, ARENA_Y)
    state = _get_ai_state(wolf)
    state.chase_momentum_direction = (1, 0)
    direction = _choose_momentum_direction(
        engine.world,
        engine.game_map,
        wolf,
        wolf.components[Position],
        state,
        blocked_tiles=frozenset(),
    )
    assert direction is not None
    assert direction != (-1, 0)


def test_memory_frustration_gives_up_and_clears_memory() -> None:
    state = AIState(
        last_known_primary=Position(9, 9),
        chase_frustration_limit=2,
        chase_frustration=1,
    )
    assert _record_memory_pursuit_blocked(state)
    assert state.last_known_primary is None
    assert state.chase_momentum_turns_left == 0


def test_memory_blocked_step_increments_frustration_not_blind_timer() -> None:
    state = AIState(chase_frustration_limit=CHASE_FRUSTRATION_MAX)
    _complete_pursuit_step(state, (1, 0), phase="memory", moved=False)
    assert state.chase_frustration == 1
    assert state.last_known_primary is None or state.chase_frustration < CHASE_FRUSTRATION_MAX


def test_memory_progress_resets_frustration() -> None:
    state = AIState(chase_frustration_limit=10, chase_frustration=4)
    origin = Position(ARENA_X, ARENA_Y)
    target = Position(ARENA_X + 5, ARENA_Y)
    _complete_pursuit_step(
        state,
        (1, 0),
        phase="memory",
        moved=True,
        origin=origin,
        current_pos=Position(ARENA_X + 1, ARENA_Y),
        memory_target=target,
    )
    assert state.chase_frustration == 0
    assert state.chase_momentum_direction == (1, 0)


def test_memory_sidestep_without_progress_counts_as_blocked() -> None:
    state = AIState(chase_frustration_limit=CHASE_FRUSTRATION_MAX, chase_frustration=0)
    origin = Position(ARENA_X + 2, ARENA_Y)
    target = Position(ARENA_X + 5, ARENA_Y)
    _complete_pursuit_step(
        state,
        (0, 1),
        phase="memory",
        moved=True,
        origin=origin,
        current_pos=Position(ARENA_X + 2, ARENA_Y + 1),
        memory_target=target,
    )
    assert state.chase_frustration == 1


def test_momentum_exhaustion_gives_up() -> None:
    state = AIState(
        last_known_primary=Position(4, 4),
        chase_momentum_turns_left=1,
    )
    _complete_pursuit_step(state, (1, 0), phase="momentum", moved=True)
    assert state.last_known_primary is None
    _reset_chase_pursuit(state)


def test_pick_pursuit_prefers_momentum_over_memory_target() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    wolf = first_wolf(engine)
    player = engine.player
    assert player is not None
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X + 4, ARENA_Y)
    wolf.components[Position] = Position(ARENA_X, ARENA_Y)
    player.components[Position] = Position(1, 1)
    state = _get_ai_state(wolf)
    state.last_known_primary = Position(ARENA_X + 4, ARENA_Y)
    state.chase_momentum_direction = (1, 0)
    state.chase_momentum_turns_left = 2
    direction, phase = _pick_pursuit_direction(
        wolf,
        engine.world,
        engine.game_map,
        player,
        random.Random(0),
        state,
        wolf.components[Position],
        alignment=Alignment.EVIL,
        blocked_tiles=frozenset(),
        player_engulfed=False,
        entity_target=None,
        pos_target=state.last_known_primary,
        chase_mode="attack",
    )
    assert phase == "momentum"
    assert direction == (1, 0)


def test_memory_pursuit_sets_frustration_limit_not_immediate_give_up() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    wolf = first_wolf(engine)
    player = engine.player
    assert player is not None
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X + 8, ARENA_Y)
    wolf.components[Position] = Position(ARENA_X, ARENA_Y)
    player.components[Position] = Position(1, 1)
    state = _get_ai_state(wolf)
    memory = Position(ARENA_X + 8, ARENA_Y)
    state.last_known_primary = memory
    _, phase = _pick_pursuit_direction(
        wolf,
        engine.world,
        engine.game_map,
        player,
        random.Random(4),
        state,
        wolf.components[Position],
        alignment=Alignment.EVIL,
        blocked_tiles=frozenset(),
        player_engulfed=False,
        entity_target=None,
        pos_target=memory,
        chase_mode="attack",
    )
    assert phase == "memory"
    assert state.chase_frustration_limit >= 8
    assert state.last_known_primary == memory


def test_corner_pursuit_continues_past_memory_tile() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    wolf = first_wolf(engine)
    player = engine.player
    assert player is not None
    player.components[Position] = Position(1, 1)

    base_x = ARENA_X
    base_y = ARENA_Y
    carve_floor_rect(engine, base_x, base_y, base_x + 3, base_y)
    carve_floor_rect(engine, base_x + 3, base_y + 1, base_x + 3, base_y + 3)
    knight_pos = Position(base_x + 3, base_y + 3)
    carve_floor_tile(engine, knight_pos.x, knight_pos.y)
    game_map = engine.game_map
    for x in range(base_x + 4, base_x + 6):
        if game_map.in_bounds(x, base_y):
            game_map.tiles[base_y, x] = Tile.WALL

    knight = spawn_test_npc(
        engine.world,
        x=knight_pos.x,
        y=knight_pos.y,
        species="knight",
        alignment=Alignment.GOOD,
        hp=5,
    )
    knight.components[Position] = Position(70, 40)
    wolf.components[Position] = Position(base_x, base_y)

    # Sparse floor so D4 distant throttle is off (player is far; memory chase must run).
    for entity in list(engine.world.Q.all_of(components=[AI, Position])):
        if entity is player or entity is wolf or entity is knight:
            continue
        entity.clear()

    state = _get_ai_state(wolf)
    state.last_known_primary = knight_pos
    state.chase_momentum_direction = (1, 0)
    _start_chase_momentum(state, random.Random(1))
    update_fov(game_map, base_x, base_y)

    start = wolf.components[Position]
    run_monster_turns(
        engine.world,
        game_map,
        player,
        engine.message_log,
        rng=random.Random(2),
    )
    assert wolf.components[Position] != start


def test_evil_still_targets_last_known_primary_while_pathing() -> None:
    engine = GameEngine()
    player = engine.player
    assert player is not None
    wolf = first_wolf(engine)
    isolate_other_ais(engine, keep=(wolf,))
    carve_floor_rect(engine, ARENA_X, ARENA_Y, ARENA_X + 6, ARENA_Y)
    wolf.components[Position] = Position(ARENA_X, ARENA_Y)
    player.components[Position] = Position(1, 1)
    memory = Position(ARENA_X + 6, ARENA_Y)
    state = _get_ai_state(wolf)
    state.last_known_primary = memory
    state.chase_frustration = 3
    state.chase_frustration_limit = CHASE_FRUSTRATION_MAX
    entity, pos, _ = pick_evil_chase(
        wolf,
        engine.world,
        engine.game_map,
        player,
        random.Random(0),
    )
    assert entity is None
    assert pos == memory