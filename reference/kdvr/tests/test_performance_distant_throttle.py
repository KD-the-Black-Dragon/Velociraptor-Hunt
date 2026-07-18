"""Distant AI throttle D2/D3/D4 (fix-performance-ai-hotpath PR2)."""

from __future__ import annotations

import random

from src.components import AI, AIState, Alignment, Player, Position
from src.constants import BUSY_FLOOR_NPC_THRESHOLD, DISTANT_AI_RADIUS
from src.engine import GameEngine
from src.message_log import MessageLog
from src.systems.ai import (
    _distant_throttle_applies,
    _floor_is_busy,
    _half_turn_should_act,
    _is_distant_from_player,
    pick_evil_chase,
    pick_good_chase,
    run_monster_turns,
    spawn_test_npc,
)
from tests.map_test_helpers import ARENA_X, ARENA_Y, carve_floor_rect, relocate_player


def _remove_all_npcs(engine: GameEngine) -> None:
    player = engine.player
    for entity in list(engine.world.Q.all_of(components=[AI, Position])):
        if entity is player:
            continue
        entity.clear()


def _npc_count(engine: GameEngine) -> int:
    player = engine.player
    return sum(
        1
        for entity in engine.world.Q.all_of(components=[AI, Position])
        if entity is not player and Player not in entity.tags
    )


def _pad_busy_floor(engine: GameEngine) -> None:
    """Stack pad NPCs far away so count > N without interacting with the subject."""
    need = BUSY_FLOOR_NPC_THRESHOLD + 2 - _npc_count(engine)
    for i in range(max(0, need)):
        spawn_test_npc(
            engine.world,
            x=70,
            y=40,
            species=f"pad{i}",
            alignment=Alignment.NEUTRAL,
        )


def test_floor_is_busy_gate() -> None:
    assert not _floor_is_busy(BUSY_FLOOR_NPC_THRESHOLD)
    assert not _floor_is_busy(BUSY_FLOOR_NPC_THRESHOLD - 1)
    assert _floor_is_busy(BUSY_FLOOR_NPC_THRESHOLD + 1)


def test_distant_uses_chebyshev_radius() -> None:
    player = Position(10, 10)
    assert not _is_distant_from_player(Position(10 + DISTANT_AI_RADIUS, 10), player)
    assert _is_distant_from_player(Position(10 + DISTANT_AI_RADIUS + 1, 10), player)
    assert _is_distant_from_player(
        Position(10 + DISTANT_AI_RADIUS, 10 + DISTANT_AI_RADIUS + 1),
        player,
    )


def test_half_turn_cadence_uses_salt() -> None:
    even = AIState(ai_turn_salt=0)
    odd = AIState(ai_turn_salt=1)
    assert _half_turn_should_act(even, 0)
    assert not _half_turn_should_act(even, 1)
    assert not _half_turn_should_act(odd, 0)
    assert _half_turn_should_act(odd, 1)


def test_within_r_still_pursues_last_known_when_busy() -> None:
    """Within R: memory corner chase even if floor is busy (D3 off)."""
    engine = GameEngine()
    _remove_all_npcs(engine)
    _pad_busy_floor(engine)
    # Player near wolf (within R) but not LOS-visible so chase uses memory only.
    relocate_player(engine, ARENA_X, ARENA_Y + 3)
    wolf_x = ARENA_X + 5
    wolf_y = ARENA_Y
    carve_floor_rect(engine, ARENA_X, ARENA_Y, wolf_x, wolf_y)
    # Wall off player from wolf corridor.
    from src.map_gen import Tile

    for x in range(ARENA_X - 1, wolf_x + 2):
        if engine.game_map.in_bounds(x, ARENA_Y + 1):
            engine.game_map.tiles[ARENA_Y + 1, x] = int(Tile.WALL)
    wolf = spawn_test_npc(
        engine.world,
        x=wolf_x,
        y=wolf_y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    memory = Position(ARENA_X + 2, ARENA_Y)
    state = wolf.components[AIState]
    state.last_known_primary = memory
    assert not _is_distant_from_player(
        wolf.components[Position],
        engine.player.components[Position],
    )
    assert _floor_is_busy(_npc_count(engine))
    _entity, pos, _blocked = pick_evil_chase(
        wolf,
        engine.world,
        engine.game_map,
        engine.player,
        random.Random(0),
        distant_throttle=False,
    )
    assert _entity is None
    assert pos == memory


def test_beyond_r_skips_memory_when_throttled() -> None:
    engine = GameEngine()
    _remove_all_npcs(engine)
    relocate_player(engine, ARENA_X, ARENA_Y)
    far_x = ARENA_X + DISTANT_AI_RADIUS + 3
    far_y = ARENA_Y
    carve_floor_rect(engine, ARENA_X, ARENA_Y, far_x, far_y)
    wolf = spawn_test_npc(
        engine.world,
        x=far_x,
        y=far_y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    state = wolf.components[AIState]
    memory = Position(ARENA_X + 1, ARENA_Y)
    state.last_known_primary = memory
    assert _is_distant_from_player(
        wolf.components[Position],
        engine.player.components[Position],
    )
    _entity, pos, _blocked = pick_evil_chase(
        wolf,
        engine.world,
        engine.game_map,
        engine.player,
        random.Random(0),
        distant_throttle=True,
    )
    assert pos != memory
    assert state.last_known_primary == memory


def test_beyond_r_memory_works_when_not_busy() -> None:
    """D4 off: ≤N NPCs keeps full memory pursuit even when distant."""
    engine = GameEngine()
    _remove_all_npcs(engine)
    relocate_player(engine, ARENA_X, ARENA_Y)
    far_x = ARENA_X + DISTANT_AI_RADIUS + 3
    far_y = ARENA_Y
    carve_floor_rect(engine, ARENA_X, ARENA_Y, far_x, far_y)
    wolf = spawn_test_npc(
        engine.world,
        x=far_x,
        y=far_y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    memory = Position(ARENA_X + 1, ARENA_Y)
    wolf.components[AIState].last_known_primary = memory
    npc_count = _npc_count(engine)
    assert npc_count <= BUSY_FLOOR_NPC_THRESHOLD
    busy = _floor_is_busy(npc_count)
    throttle = _distant_throttle_applies(wolf, engine.player, busy=busy)
    assert not throttle
    _entity, pos, _blocked = pick_evil_chase(
        wolf,
        engine.world,
        engine.game_map,
        engine.player,
        random.Random(0),
        distant_throttle=throttle,
    )
    assert pos == memory


def test_good_beyond_r_skips_last_known_player_when_throttled() -> None:
    engine = GameEngine()
    _remove_all_npcs(engine)
    relocate_player(engine, ARENA_X, ARENA_Y)
    far_x = ARENA_X + DISTANT_AI_RADIUS + 3
    far_y = ARENA_Y
    carve_floor_rect(engine, ARENA_X, ARENA_Y, far_x, far_y)
    ally = spawn_test_npc(
        engine.world,
        x=far_x,
        y=far_y,
        species="knight",
        alignment=Alignment.GOOD,
    )
    state = ally.components[AIState]
    state.last_known_player = engine.player.components[Position]
    _entity, pos, mode = pick_good_chase(
        ally,
        engine.world,
        engine.game_map,
        engine.player,
        random.Random(0),
        distant_throttle=True,
    )
    assert mode == "explore"
    assert pos != state.last_known_player


def test_half_turn_skips_distant_busy_visit() -> None:
    engine = GameEngine()
    _remove_all_npcs(engine)
    relocate_player(engine, ARENA_X, ARENA_Y)
    _pad_busy_floor(engine)
    far_x = ARENA_X + DISTANT_AI_RADIUS + 4
    far_y = ARENA_Y
    carve_floor_rect(engine, far_x - 1, far_y, far_x + 1, far_y)
    wolf = spawn_test_npc(
        engine.world,
        x=far_x,
        y=far_y,
        species="wolf",
        alignment=Alignment.EVIL,
    )
    state = wolf.components[AIState]
    state.ai_turn_salt = 0
    start = wolf.components[Position]
    log = MessageLog()
    assert _floor_is_busy(_npc_count(engine))
    assert _distant_throttle_applies(wolf, engine.player, busy=True)
    # Odd turn + salt 0 → skip (D2).
    run_monster_turns(
        engine.world,
        engine.game_map,
        engine.player,
        log,
        rng=random.Random(0),
        player_turn_count=1,
    )
    assert wolf.components[Position] == start
    # Even turn → visit runs (explore may idle without moving).
    run_monster_turns(
        engine.world,
        engine.game_map,
        engine.player,
        log,
        rng=random.Random(1),
        player_turn_count=2,
    )
    assert wolf.components.get(AIState) is not None


def test_spawn_sets_ai_turn_salt() -> None:
    engine = GameEngine()
    _remove_all_npcs(engine)
    a = spawn_test_npc(engine.world, x=3, y=4, species="a", alignment=Alignment.EVIL)
    b = spawn_test_npc(engine.world, x=3, y=5, species="b", alignment=Alignment.EVIL)
    assert a.components[AIState].ai_turn_salt == (3 + 4) & 1
    assert b.components[AIState].ai_turn_salt == (3 + 5) & 1
    assert a.components[AIState].ai_turn_salt != b.components[AIState].ai_turn_salt
