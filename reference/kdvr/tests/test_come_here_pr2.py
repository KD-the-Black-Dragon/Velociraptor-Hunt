"""PR2: Come here! good AI approach, tag-clear, frustration, lose-track."""

from __future__ import annotations

import random

from src.components import AIState, Engulfed, Position
from src.engine import GameEngine
from src.spawn import spawn_entity_by_id
from src.systems.ai import _frustration_blockers_to_pos, _give_up_chase, pick_good_chase
from src.systems.come_here import clear_all_come_here
from src.systems.fov import update_fov
from src.systems.vore import is_adjacent
from tests.map_test_helpers import isolate_other_ais


def _knight_near_player(engine: GameEngine, dx: int = 2, dy: int = 0):
    player = engine.player
    assert player is not None
    pos = player.components[Position]
    knight = spawn_entity_by_id(engine.world, "knight", pos.x + dx, pos.y + dy)
    update_fov(engine.game_map, pos.x, pos.y)
    return knight


def test_come_here_prefers_player_over_visible_evil() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.new_game(seed=21)
    player = engine.player
    assert player is not None
    ppos = player.components[Position]
    knight = spawn_entity_by_id(engine.world, "knight", ppos.x + 3, ppos.y)
    # Evil near knight but NOT between knight and player (off the approach axis).
    wolf = spawn_entity_by_id(engine.world, "wolf", ppos.x + 3, ppos.y + 2)
    update_fov(engine.game_map, ppos.x, ppos.y)
    knight.components[AIState].come_here = True

    # Confirm setup: wolf is not a frustration blocker toward the player.
    assert not _frustration_blockers_to_pos(
        knight.components[Position],
        ppos,
        [wolf],
    )

    target, pos_target, mode = pick_good_chase(
        knight,
        engine.world,
        engine.game_map,
        player,
        random.Random(0),
    )
    assert mode == "follow"
    assert target is player
    assert pos_target is None


def test_adjacency_clears_come_here() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.new_game(seed=22)
    player = engine.player
    assert player is not None
    ppos = player.components[Position]
    knight = spawn_entity_by_id(engine.world, "knight", ppos.x + 1, ppos.y)
    update_fov(engine.game_map, ppos.x, ppos.y)
    state = knight.components[AIState]
    state.come_here = True
    assert is_adjacent(knight.components[Position], ppos)

    pick_good_chase(
        knight,
        engine.world,
        engine.game_map,
        player,
        random.Random(0),
    )
    assert state.come_here is False


def test_frustration_blockers_evil_between_ally_and_player() -> None:
    origin = Position(0, 0)
    player_pos = Position(4, 0)
    # Wolf at (2,0) is strictly between origin and player on the line.
    class _E:
        def __init__(self, x: int, y: int) -> None:
            self.components = {Position: Position(x, y)}

    wolf = _E(2, 0)
    side = _E(0, 3)  # off to the side; not closer to both origin and primary
    blockers = _frustration_blockers_to_pos(origin, player_pos, [wolf, side])  # type: ignore[list-item]
    assert wolf in blockers
    assert side not in blockers


def test_come_here_attacks_blocking_evil() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.new_game(seed=23)
    player = engine.player
    assert player is not None
    ppos = player.components[Position]
    # Knight -- wolf -- player in a row when geometry allows.
    # Place knight at player+3, wolf at player+2 (between).
    knight = spawn_entity_by_id(engine.world, "knight", ppos.x + 3, ppos.y)
    wolf = spawn_entity_by_id(engine.world, "wolf", ppos.x + 2, ppos.y)
    update_fov(engine.game_map, ppos.x, ppos.y)
    knight.components[AIState].come_here = True

    # Ensure LOS knight→player and frustration geometry.
    origin = knight.components[Position]
    player_pos = ppos
    assert _frustration_blockers_to_pos(
        origin, player_pos, [wolf]
    ), "test setup: wolf should block path to player"

    target, _, mode = pick_good_chase(
        knight,
        engine.world,
        engine.game_map,
        player,
        random.Random(0),
    )
    assert mode == "attack"
    assert target is wolf


def test_give_up_chase_clears_come_here() -> None:
    state = AIState(come_here=True, last_known_player=Position(1, 1))
    _give_up_chase(state)
    assert state.come_here is False
    assert state.last_known_player is None


def test_clear_all_come_here() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.new_game(seed=24)
    knight = _knight_near_player(engine, dx=2)
    knight.components[AIState].come_here = True
    clear_all_come_here(engine.world)
    assert knight.components[AIState].come_here is False


def test_come_here_without_los_or_memory_drops_order() -> None:
    engine = GameEngine()
    isolate_other_ais(engine)
    engine.new_game(seed=25)
    player = engine.player
    assert player is not None
    ppos = player.components[Position]
    knight = spawn_entity_by_id(engine.world, "knight", ppos.x + 20, ppos.y)
    update_fov(engine.game_map, ppos.x, ppos.y)
    state = knight.components[AIState]
    state.come_here = True
    state.last_known_player = None

    pick_good_chase(
        knight,
        engine.world,
        engine.game_map,
        player,
        random.Random(0),
    )
    assert state.come_here is False
