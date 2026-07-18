"""Spawn AI freeze (anti-swarm): distance timer, proximity, damage, one-shot."""

from __future__ import annotations

from tcod.ecs import Registry

from src.components import AI, AIState, Fighter, Player, Position
from src.data.depth_scaling_config import SpawnAiFreezeConfig
from src.systems.ai.common import (
    apply_spawn_ai_freeze_at_spawn,
    clear_spawn_ai_freeze,
    spawn_ai_freeze_blocks_action,
)


def _npc_at(world: Registry, x: int, y: int, *, remaining: int = 10) -> object:
    e = world[object()]
    e.components[Position] = Position(x, y)
    e.components[AI] = AI()
    e.components[AIState] = AIState(
        spawn_freeze_remaining=remaining,
        spawn_freeze_consumed=remaining <= 0,
    )
    e.components[Fighter] = Fighter(
        hp=10, max_hp=10, accuracy=1.0, evade=0, ac=0, min_damage=1, max_damage=1
    )
    return e


def _player_at(world: Registry, x: int, y: int) -> object:
    p = world[object()]
    p.tags.add(Player)
    p.components[Position] = Position(x, y)
    return p


def test_freeze_turns_scale_with_distance() -> None:
    cfg = SpawnAiFreezeConfig(
        enabled=True,
        turns_per_chebyshev=2,
        distance_offset=6,
        max_turns=48,
        proximity_unfreeze=8,
    )
    assert cfg.freeze_turns_for_chebyshev(6) == 0
    assert cfg.freeze_turns_for_chebyshev(10) == 8
    assert cfg.freeze_turns_for_chebyshev(100) == 48


def test_apply_at_spawn_arms_and_marks_near_as_consumed() -> None:
    world = Registry()
    e = _npc_at(world, 5, 5, remaining=0)
    cfg = SpawnAiFreezeConfig(
        enabled=True,
        turns_per_chebyshev=2,
        distance_offset=6,
        max_turns=48,
        proximity_unfreeze=8,
    )
    apply_spawn_ai_freeze_at_spawn(
        e, spawn_x=5, spawn_y=5, player_x=5, player_y=5, freeze_config=cfg
    )
    st = e.components[AIState]
    assert st.spawn_freeze_remaining == 0
    assert st.spawn_freeze_consumed is True

    apply_spawn_ai_freeze_at_spawn(
        e, spawn_x=20, spawn_y=5, player_x=5, player_y=5, freeze_config=cfg
    )
    st = e.components[AIState]
    # cheb 15 → (15-6)*2 = 18
    assert st.spawn_freeze_remaining == 18
    assert st.spawn_freeze_consumed is False


def test_timer_ticks_and_blocks_then_releases() -> None:
    world = Registry()
    player = _player_at(world, 0, 0)
    # far enough that proximity 8 does not clear
    npc = _npc_at(world, 20, 0, remaining=2)
    cfg = SpawnAiFreezeConfig(proximity_unfreeze=8)

    assert spawn_ai_freeze_blocks_action(npc, player, cfg) is True
    assert npc.components[AIState].spawn_freeze_remaining == 1
    assert spawn_ai_freeze_blocks_action(npc, player, cfg) is True
    assert npc.components[AIState].spawn_freeze_remaining == 0
    assert npc.components[AIState].spawn_freeze_consumed is True
    # fully released — never blocks again
    assert spawn_ai_freeze_blocks_action(npc, player, cfg) is False


def test_proximity_clears_and_allows_action() -> None:
    world = Registry()
    player = _player_at(world, 0, 0)
    npc = _npc_at(world, 5, 0, remaining=20)
    cfg = SpawnAiFreezeConfig(proximity_unfreeze=8)
    assert spawn_ai_freeze_blocks_action(npc, player, cfg) is False
    assert npc.components[AIState].spawn_freeze_consumed is True
    assert npc.components[AIState].spawn_freeze_remaining == 0


def test_damage_clears_freeze() -> None:
    world = Registry()
    npc = _npc_at(world, 30, 0, remaining=40)
    clear_spawn_ai_freeze(npc)
    assert npc.components[AIState].spawn_freeze_consumed is True
    assert npc.components[AIState].spawn_freeze_remaining == 0


def test_cannot_refreeze_after_consumed() -> None:
    world = Registry()
    player = _player_at(world, 0, 0)
    npc = _npc_at(world, 30, 0, remaining=5)
    clear_spawn_ai_freeze(npc)
    # even if remaining were set again by mistake, consumed wins
    npc.components[AIState].spawn_freeze_remaining = 99
    cfg = SpawnAiFreezeConfig()
    assert spawn_ai_freeze_blocks_action(npc, player, cfg) is False


def test_stock_depth_scaling_loads_freeze() -> None:
    from src.data.depth_scaling_loader import (
        default_depth_scaling_config,
        reset_depth_scaling_cache,
    )

    reset_depth_scaling_cache()
    cfg = default_depth_scaling_config()
    normal = cfg.profile_for("normal").spawn_ai_freeze
    assert normal.enabled is True
    assert normal.turns_per_chebyshev >= 1
    easier = cfg.profile_for("easier").spawn_ai_freeze
    hard = cfg.profile_for("hard").spawn_ai_freeze
    # Easier is more generous than hard (higher freeze budget)
    assert easier.max_turns >= hard.max_turns
    assert easier.turns_per_chebyshev >= hard.turns_per_chebyshev
    reset_depth_scaling_cache()
