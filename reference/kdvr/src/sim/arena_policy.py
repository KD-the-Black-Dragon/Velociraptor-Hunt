"""Minimal bump-or-move-right policy for 1v1 arena headless runs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

from src.components import Position, Stunned
from src.sim.navigation import (
    first_step_toward,
    manhattan,
    player_walk_distances,
)
from src.sim.perception import visible_evil_entities
from src.systems.combat import try_action

if TYPE_CHECKING:
    from src.engine import GameEngine


class ArenaActionKind(Enum):
    WAIT = auto()
    MOVE = auto()
    ATTACK = auto()


@dataclass(frozen=True)
class ArenaAction:
    kind: ArenaActionKind
    direction: tuple[int, int] = (0, 0)


class ArenaPolicy:
    """Bump nearest visible Evil, else move right. No consumables."""

    def decide(self, engine: GameEngine) -> ArenaAction:
        player = engine.player
        if player is None:
            return ArenaAction(ArenaActionKind.WAIT)

        if Stunned in player.tags:
            return ArenaAction(ArenaActionKind.WAIT)

        pos = player.components.get(Position)
        if pos is None:
            return ArenaAction(ArenaActionKind.WAIT)

        origin = (pos.x, pos.y)
        evils = visible_evil_entities(engine)
        if evils:
            target = min(
                evils,
                key=lambda entity: manhattan(
                    origin,
                    (
                        entity.components[Position].x,
                        entity.components[Position].y,
                    ),
                ),
            )
            target_pos = target.components[Position]
            target_xy = (target_pos.x, target_pos.y)
            if (
                abs(target_pos.x - pos.x) <= 1
                and abs(target_pos.y - pos.y) <= 1
                and target_xy != origin
            ):
                direction = _direction_to_adjacent(origin, target_xy)
                if direction is not None:
                    return ArenaAction(ArenaActionKind.ATTACK, direction)
            goal_distances = player_walk_distances(engine.game_map, target_xy)
            direction = first_step_toward(origin, target_xy, goal_distances)
            if direction is not None:
                return ArenaAction(ArenaActionKind.MOVE, direction)

        return ArenaAction(ArenaActionKind.MOVE, (1, 0))

    def execute(self, engine: GameEngine, action: ArenaAction) -> None:
        player = engine.player
        if player is None:
            return

        if action.kind is ArenaActionKind.WAIT:
            engine._consume_player_turn()
            return

        if action.kind in (ArenaActionKind.MOVE, ArenaActionKind.ATTACK):
            try_action(
                engine.world,
                engine.game_map,
                player,
                action.direction,
                engine.message_log,
                rng=engine.rng,
                skip_turn_entities=engine.skipped_this_phase,
                run_stats=engine.run_stats,
            )
            engine._consume_player_turn()


def _direction_to_adjacent(
    origin: tuple[int, int],
    target: tuple[int, int],
) -> tuple[int, int] | None:
    ox, oy = origin
    tx, ty = target
    dx = max(-1, min(1, tx - ox))
    dy = max(-1, min(1, ty - oy))
    if dx == 0 and dy == 0:
        return None
    return (dx, dy)


def execute_arena_policy_turn(engine: GameEngine) -> None:
    policy = ArenaPolicy()
    action = policy.decide(engine)
    policy.execute(engine, action)