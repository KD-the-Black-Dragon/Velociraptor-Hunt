"""Priority-ordered sim policy (PR2–PR4 navigation, survival, loot)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

from src.components import Position, Stunned
from src.engine_input import try_descend
from src.sim.inventory_policy import (
    note_visible_upgrade_spawns,
    pickup_and_equip_at_player_tile,
    try_lethal_risk_consumable,
    try_stunned_recovery,
)
from src.sim.navigation import (
    explore_frontier_tiles,
    first_step_toward,
    flee_goal_maximizing_distance,
    nearest_goal,
    player_walk_distances,
    stair_positions_reachable,
)
from src.sim.perception import (
    SHARK_THREAT_RADIUS,
    adjacent_evil_entities,
    aquatic_evils_within_radius,
    rune_quota_met,
    visible_floor_rune_positions,
    visible_loot_at_tile,
    visible_loot_positions,
    visible_non_aquatic_evils,
)
from src.sim.threat import (
    lethal_risk_active,
    rest_imperfection_skips,
    should_attempt_rest,
    update_bail_for_survival,
)
from src.systems.combat import try_action
from src.systems.floor_runes import try_activate_floor_rune


if TYPE_CHECKING:
    from src.engine import GameEngine
    from src.sim.snapshots import FloorTrackingState


class SimActionKind(Enum):
    WAIT = auto()
    MOVE = auto()
    ATTACK = auto()
    DESCEND = auto()
    REST = auto()
    CONSUME = auto()


@dataclass(frozen=True)
class SimAction:
    kind: SimActionKind
    direction: tuple[int, int] = (0, 0)


class SimPolicy:
    """Imperfect but reasonable policy for balance simulation."""

    def decide(self, engine: GameEngine, *, tracking: FloorTrackingState) -> SimAction:
        player = engine.player
        if player is None:
            return SimAction(SimActionKind.WAIT)

        pos = player.components.get(Position)
        if pos is None:
            return SimAction(SimActionKind.WAIT)

        visit = tracking.visit
        _note_stunned_event(player, visit)

        if Stunned in player.tags:
            return SimAction(SimActionKind.CONSUME)

        origin = (pos.x, pos.y)
        distances = player_walk_distances(engine.game_map, origin)

        update_bail_for_survival(engine, visit)
        if visit is not None and visit.bail_for_survival:
            stair_action = _move_toward_stairs(engine, origin, distances)
            if stair_action is not None:
                return stair_action

        if should_attempt_rest(engine) and not rest_imperfection_skips(engine):
            return SimAction(SimActionKind.REST)

        if lethal_risk_active(engine):
            return SimAction(SimActionKind.CONSUME)

        note_visible_upgrade_spawns(engine, visit)

        if visible_loot_at_tile(engine, origin[0], origin[1]):
            return SimAction(SimActionKind.WAIT)

        loot_positions = visible_loot_positions(engine)
        if loot_positions:
            goal = nearest_goal(origin, loot_positions, distances, engine.rng)
            if goal is not None:
                goal_distances = player_walk_distances(engine.game_map, goal)
                direction = first_step_toward(origin, goal, goal_distances)
                if direction is not None:
                    return SimAction(SimActionKind.MOVE, direction)

        rune_positions = visible_floor_rune_positions(engine)
        if rune_positions and not rune_quota_met(engine, visit):
            if origin in rune_positions:
                return SimAction(SimActionKind.WAIT)
            goal = nearest_goal(origin, rune_positions, distances, engine.rng)
            if goal is not None:
                goal_distances = player_walk_distances(engine.game_map, goal)
                direction = first_step_toward(origin, goal, goal_distances)
                if direction is not None:
                    return SimAction(SimActionKind.MOVE, direction)

        adjacent_attack = adjacent_evil_entities(engine, aquatic=False)
        if adjacent_attack:
            target = engine.rng.choice(adjacent_attack)
            tpos = target.components[Position]
            direction = _direction_to_adjacent(origin, (tpos.x, tpos.y))
            if direction is not None:
                return SimAction(SimActionKind.ATTACK, direction)

        aquatic_threats = aquatic_evils_within_radius(engine, SHARK_THREAT_RADIUS)
        if aquatic_threats:
            threat_positions = [
                (entity.components[Position].x, entity.components[Position].y)
                for entity in aquatic_threats
            ]
            flee_goal = flee_goal_maximizing_distance(
                origin,
                threat_positions,
                distances,
                engine.rng,
            )
            if flee_goal is not None:
                flee_distances = player_walk_distances(engine.game_map, flee_goal)
                direction = first_step_toward(origin, flee_goal, flee_distances)
                if direction is not None:
                    return SimAction(SimActionKind.MOVE, direction)

        if visit is not None and rune_quota_met(engine, visit):
            if engine._player_on_stairs():
                return SimAction(SimActionKind.DESCEND)
            stair_action = _move_toward_stairs(engine, origin, distances)
            if stair_action is not None:
                return stair_action

        frontier = explore_frontier_tiles(engine.game_map)
        goal = nearest_goal(origin, frontier, distances, engine.rng)
        if goal is not None:
            goal_distances = player_walk_distances(engine.game_map, goal)
            direction = first_step_toward(origin, goal, goal_distances)
            if direction is not None:
                return SimAction(SimActionKind.MOVE, direction)

        return SimAction(SimActionKind.WAIT)

    def execute(
        self,
        engine: GameEngine,
        action: SimAction,
        *,
        tracking: FloorTrackingState,
    ) -> None:
        player = engine.player
        if player is None:
            return

        visit = tracking.visit

        if action.kind is SimActionKind.DESCEND:
            if try_descend(engine):
                engine._consume_player_turn()
            return

        if action.kind is SimActionKind.REST:
            if engine.begin_rest():
                return
            engine._consume_player_turn()
            return

        if action.kind is SimActionKind.CONSUME:
            if Stunned in player.tags:
                try_stunned_recovery(engine, visit=visit)
            else:
                try_lethal_risk_consumable(engine, visit=visit)
            engine._consume_player_turn()
            return

        if action.kind in (SimActionKind.MOVE, SimActionKind.ATTACK):
            moved = try_action(
                engine.world,
                engine.game_map,
                player,
                action.direction,
                engine.message_log,
                rng=engine.rng,
                skip_turn_entities=engine.skipped_this_phase,
                run_stats=engine.run_stats,
            )
            if moved:
                pos = player.components.get(Position)
                if pos is not None:
                    pickup_and_equip_at_player_tile(engine, visit=visit)
                    try_activate_floor_rune(
                        engine.world,
                        player,
                        pos.x,
                        pos.y,
                        engine.message_log,
                        screen_flash=engine.screen_flash,
                        run_stats=engine.run_stats,
                        rune_pieces_multiplier=engine.difficulty_profile().rune_pieces_multiplier,
                    )
            engine._consume_player_turn()
            return

        pos = player.components.get(Position)
        if pos is not None:
            pickup_and_equip_at_player_tile(engine, visit=visit)
            try_activate_floor_rune(
                engine.world,
                player,
                pos.x,
                pos.y,
                engine.message_log,
                screen_flash=engine.screen_flash,
                run_stats=engine.run_stats,
                rune_pieces_multiplier=engine.difficulty_profile().rune_pieces_multiplier,
            )
        engine._consume_player_turn()


def execute_policy_turn(engine: GameEngine, *, tracking: FloorTrackingState) -> None:
    policy = SimPolicy()
    action = policy.decide(engine, tracking=tracking)
    policy.execute(engine, action, tracking=tracking)


def _move_toward_stairs(
    engine: GameEngine,
    origin: tuple[int, int],
    distances: dict[tuple[int, int], int],
) -> SimAction | None:
    if engine._player_on_stairs():
        return SimAction(SimActionKind.DESCEND)
    stair_goals = stair_positions_reachable(engine.game_map, distances)
    goal = nearest_goal(origin, stair_goals, distances, engine.rng)
    if goal is None:
        return None
    goal_distances = player_walk_distances(engine.game_map, goal)
    direction = first_step_toward(origin, goal, goal_distances)
    if direction is None:
        return None
    return SimAction(SimActionKind.MOVE, direction)


def _note_stunned_event(player, visit) -> None:
    if visit is None:
        return
    stunned = Stunned in player.tags
    if stunned and not visit._stunned_last_turn:
        visit.stunned_events += 1
    visit._stunned_last_turn = stunned


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