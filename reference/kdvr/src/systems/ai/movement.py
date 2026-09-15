"""AI movement: flee/wander, step resolution, door-spite wait (PR10/PR11)."""
from __future__ import annotations

import random

from tcod.ecs import Entity, Registry

from src import messages
from src.debug_log import debug_print
from src.components import (
    AIState,
    Alignment,
    Position,
)
from src.map_gen import GameMap
from src.message_log import MessageLog
from src.systems.combat import actor_can_melee_damage, _fighter_at, try_action
from src.systems.movement import MOVEMENT_DIRECTIONS, can_move_to, is_stationary
from src.systems.naming import entity_log_name
from src.systems.abilities import (
    coward_should_flee,
    has_coward,
    has_hands,
    has_supercoward,
    has_wander,
)
from src.systems.ai.common import (
    _cancel_door_spite,
    _chebyshev,
    _has_los,
    _visible_evils,
)
from src.systems.ai.explore import (
    ExploreBfsCache,
    _blocked_tiles_for_explore,
    _choose_explore_direction,
    _complete_explore_step,
    _ensure_explore_goal,
)
from src.systems.ai.targeting import (
    pick_evil_chase,
    pick_good_chase,
)
from src.systems.ai.chase import (
    ChaseStepPhase,
    _complete_pursuit_step,
    _resolve_chase_direction,
)


def _choose_flee_direction(
    world: Registry,
    game_map: GameMap,
    monster: Entity,
    origin: Position,
    threat: Position,
    rng: random.Random,
    *,
    blocked_tiles: frozenset[Position] = frozenset(),
) -> tuple[int, int] | None:
    """Pick a legal step that maximizes Chebyshev distance from the threat."""
    if is_stationary(monster):
        return None
    candidates: list[tuple[int, tuple[int, int]]] = []
    for direction in MOVEMENT_DIRECTIONS:
        if not can_move_to(
            world,
            game_map,
            monster,
            origin,
            direction,
            blocked_tiles=blocked_tiles,
        ):
            continue
        dest = origin + direction
        candidates.append((_chebyshev(dest, threat), direction))
    if not candidates:
        return None
    best_distance = max(distance for distance, _ in candidates)
    best = [direction for distance, direction in candidates if distance == best_distance]
    return rng.choice(best)


def _choose_wander_direction(
    world: Registry,
    game_map: GameMap,
    monster: Entity,
    origin: Position,
    rng: random.Random,
    *,
    blocked_tiles: frozenset[Position] = frozenset(),
) -> tuple[int, int] | None:
    """Pick a random legal step; used when prey is already engulfed."""
    if is_stationary(monster):
        return None
    legal = [
        direction
        for direction in MOVEMENT_DIRECTIONS
        if can_move_to(
            world,
            game_map,
            monster,
            origin,
            direction,
            blocked_tiles=blocked_tiles,
        )
    ]
    if not legal:
        return None
    return rng.choice(legal)


def _choose_erratic_random_direction(
    world: Registry,
    game_map: GameMap,
    monster: Entity,
    origin: Position,
    rng: random.Random,
    *,
    blocked_tiles: frozenset[Position] = frozenset(),
    forbid_return_to: Position | None = None,
) -> tuple[int, int] | None:
    """Equal-weight random step including stay; never reverse into ``forbid_return_to``.

    Returns ``(0, 0)`` to remain still, or a movement direction. ``None`` only when
    there is no legal choice at all (should not happen — stay is always allowed).
    """
    if is_stationary(monster):
        return (0, 0)
    options: list[tuple[int, int]] = [(0, 0)]
    for direction in MOVEMENT_DIRECTIONS:
        if not can_move_to(
            world,
            game_map,
            monster,
            origin,
            direction,
            blocked_tiles=blocked_tiles,
        ):
            continue
        dest = origin + direction
        if forbid_return_to is not None and dest == forbid_return_to:
            continue
        options.append(direction)
    if not options:
        return None
    return rng.choice(options)


def _nearest_threat_position(
    threats: list[Entity],
    origin: Position,
    rng: random.Random,
) -> Position:
    best_distance = min(_chebyshev(origin, t.components[Position]) for t in threats)
    tied = [t for t in threats if _chebyshev(origin, t.components[Position]) == best_distance]
    return rng.choice(tied).components[Position]


def _try_predator_holding_attack(
    world: Registry,
    game_map: GameMap,
    predator: Entity,
    message_log: MessageLog,
    *,
    rng: random.Random,
    skipped: set[Entity] | None = None,
) -> None:
    """Bump-attack one adjacent valid target; holding predators cannot move or chase.

    Skips alignment-illegal targets (evil never attacks evil). Tries further
    directions if a neighbor is present but not a valid melee target.
    """
    origin = predator.components[Position]
    for direction in MOVEMENT_DIRECTIONS:
        dest = origin + direction
        if not game_map.in_bounds(dest.x, dest.y):
            continue
        defender = _fighter_at(world, dest.x, dest.y, exclude=predator)
        if defender is None:
            continue
        if not actor_can_melee_damage(predator, defender):
            continue
        if try_action(
            world,
            game_map,
            predator,
            direction,
            message_log,
            rng=rng,
            skip_turn_entities=skipped,
        ):
            return


def resolve_wander_ability_move(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    rng: random.Random,
    *,
    state: AIState,
    alignment: Alignment,
    blocked: frozenset[Position],
    monster_pos: Position,
    cache: ExploreBfsCache | None = None,
    explore_allow_idle: bool = True,
) -> tuple[tuple[int, int] | None, ChaseStepPhase, bool]:
    """Explore-only temperament for ``Wander`` holders; neutral still flees visible evil."""
    if is_stationary(monster):
        return None, "none", False
    explore_blocked = _blocked_tiles_for_explore(monster, world, blocked)
    if alignment == Alignment.NEUTRAL:
        evils = _visible_evils(monster, world, game_map)
        if evils:
            if (
                has_coward(monster)
                and not has_supercoward(monster)
                and not coward_should_flee(monster)
            ):
                return (
                    _choose_explore_direction(
                        world,
                        game_map,
                        monster,
                        monster_pos,
                        _ensure_explore_goal(
                            state,
                            game_map,
                            monster_pos,
                            monster,
                            rng,
                            player=player,
                            cache=cache,
                        ),
                        monster,
                        rng,
                        blocked_tiles=explore_blocked,
                        recent_positions=state.explore_recent_positions,
                        state=state,
                        allow_idle=explore_allow_idle,
                    ),
                    "none",
                    True,
                )
            threat_pos = _nearest_threat_position(evils, monster_pos, rng)
            return (
                _choose_flee_direction(
                    world,
                    game_map,
                    monster,
                    monster_pos,
                    threat_pos,
                    rng,
                    blocked_tiles=blocked,
                ),
                "none",
                False,
            )
    goal = _ensure_explore_goal(
        state,
        game_map,
        monster_pos,
        monster,
        rng,
        player=player,
        cache=cache,
    )
    return (
        _choose_explore_direction(
            world,
            game_map,
            monster,
            monster_pos,
            goal,
            monster,
            rng,
            blocked_tiles=explore_blocked,
            recent_positions=state.explore_recent_positions,
            state=state,
            allow_idle=explore_allow_idle,
        ),
        "none",
        goal is not None,
    )


def _resolve_monster_move_direction(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    rng: random.Random,
    *,
    state: AIState,
    alignment: Alignment,
    blocked: frozenset[Position],
    player_engulfed: bool,
    monster_pos: Position,
    cache: ExploreBfsCache | None = None,
    player_turn_count: int = 0,
    distant_throttle: bool = False,
    explore_allow_idle: bool = True,
) -> tuple[tuple[int, int] | None, ChaseStepPhase]:
    """Alignment-aware chase/explore/wander without the attack pipeline."""
    if has_wander(monster):
        direction, phase, _explore_step = resolve_wander_ability_move(
            monster,
            world,
            game_map,
            player,
            rng,
            state=state,
            alignment=alignment,
            blocked=blocked,
            monster_pos=monster_pos,
            cache=cache,
            explore_allow_idle=explore_allow_idle,
        )
        return direction, phase
    player_pos = player.components[Position]
    explore_blocked = _blocked_tiles_for_explore(monster, world, blocked)
    if alignment == Alignment.NEUTRAL:
        evils = _visible_evils(monster, world, game_map)
        if evils:
            if (
                has_coward(monster)
                and not has_supercoward(monster)
                and not coward_should_flee(monster)
            ):
                return (
                    _choose_explore_direction(
                        world,
                        game_map,
                        monster,
                        monster_pos,
                        _ensure_explore_goal(
                            state,
                            game_map,
                            monster_pos,
                            monster,
                            rng,
                            player=player,
                            cache=cache,
                        ),
                        monster,
                        rng,
                        blocked_tiles=explore_blocked,
                        recent_positions=state.explore_recent_positions,
                        state=state,
                        allow_idle=explore_allow_idle,
                    ),
                    "none",
                )
            threat_pos = _nearest_threat_position(evils, monster_pos, rng)
            return (
                _choose_flee_direction(
                    world,
                    game_map,
                    monster,
                    monster_pos,
                    threat_pos,
                    rng,
                    blocked_tiles=blocked,
                ),
                "none",
            )
        return (
            _choose_explore_direction(
                world,
                game_map,
                monster,
                monster_pos,
                _ensure_explore_goal(
                    state,
                    game_map,
                    monster_pos,
                    monster,
                    rng,
                    player=player,
                    cache=cache,
                ),
                monster,
                rng,
                blocked_tiles=explore_blocked,
                recent_positions=state.explore_recent_positions,
                state=state,
                allow_idle=explore_allow_idle,
            ),
            "none",
        )
    if alignment == Alignment.EVIL:
        entity_target, pos_target, blocked_primary = pick_evil_chase(
            monster,
            world,
            game_map,
            player,
            rng,
            player_engulfed=player_engulfed,
            cache=cache,
            player_turn_count=player_turn_count,
            distant_throttle=distant_throttle,
        )
        if blocked_primary is not None and entity_target is not None:
            debug_print(
                messages.evil_frustrated_by_blocker(
                    entity_log_name(monster, sentence_start=True),
                    entity_log_name(entity_target),
                    entity_log_name(blocked_primary),
                ),
                flush=True,
            )
        if entity_target is not None or pos_target is not None:
            return _resolve_chase_direction(
                world,
                game_map,
                monster,
                monster_pos,
                target_entity=entity_target,
                target_position=pos_target,
                chase_mode="attack",
                player=player,
                blocked=blocked,
                state=state,
                rng=rng,
                alignment=alignment,
                player_engulfed=player_engulfed,
                cache=cache,
                explore_allow_idle=explore_allow_idle,
            )
        if player_engulfed and _has_los(game_map, monster_pos, player_pos):
            if rng.random() < 0.5:
                return None, "none"
            return (
                _choose_wander_direction(
                    world,
                    game_map,
                    monster,
                    monster_pos,
                    rng,
                    blocked_tiles=blocked,
                ),
                "none",
            )
        return None, "none"
    entity_target, pos_target, chase_mode = pick_good_chase(
        monster,
        world,
        game_map,
        player,
        rng,
        player_engulfed=player_engulfed,
        cache=cache,
        player_turn_count=player_turn_count,
        distant_throttle=distant_throttle,
    )
    direction, _phase = _resolve_chase_direction(
        world,
        game_map,
        monster,
        monster_pos,
        target_entity=entity_target,
        target_position=pos_target,
        chase_mode=chase_mode,
        player=player,
        blocked=blocked,
        state=state,
        rng=rng,
        alignment=alignment,
        player_engulfed=player_engulfed,
        cache=cache,
        explore_allow_idle=explore_allow_idle,
    )
    return direction, _phase


def _consume_door_spite_wait_turn(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    message_log: MessageLog,
    rng: random.Random,
    *,
    state: AIState,
    monster_pos: Position,
    skipped: set[Entity] | None,
) -> bool:
    """Stand still while door spite is active. Returns True when the turn was consumed."""
    if has_hands(monster):
        if state.door_spite_turns_left > 0:
            _cancel_door_spite(state)
        return False
    if state.door_spite_turns_left <= 0:
        return False
    _try_monster_move(
        monster,
        world,
        game_map,
        None,
        message_log,
        rng,
        origin=monster_pos,
        state=state,
        pursuit_phase="none",
        skipped=skipped,
        explore_step=False,
        player=player,
    )
    state.door_spite_turns_left -= 1
    return True


def _try_monster_move(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    direction: tuple[int, int] | None,
    message_log: MessageLog,
    rng: random.Random,
    *,
    origin: Position,
    state: AIState,
    pursuit_phase: ChaseStepPhase,
    skipped: set[Entity] | None,
    explore_step: bool = False,
    memory_target: Position | None = None,
    player: Entity | None = None,
    cache: ExploreBfsCache | None = None,
) -> None:
    if direction is None:
        _complete_pursuit_step(
            state,
            None,
            phase=pursuit_phase,
            moved=False,
            origin=origin,
            current_pos=origin,
            memory_target=memory_target,
        )
        if explore_step:
            _complete_explore_step(
                state,
                monster,
                game_map,
                origin,
                rng,
                moved=False,
                cache=cache,
            )
        return
    try_action(
        world,
        game_map,
        monster,
        direction,
        message_log,
        rng=rng,
        skip_turn_entities=skipped,
    )
    moved = monster.components[Position] != origin
    current_pos = monster.components[Position]
    _complete_pursuit_step(
        state,
        direction,
        phase=pursuit_phase,
        moved=moved,
        origin=origin,
        current_pos=current_pos,
        memory_target=memory_target,
    )
    if explore_step:
        _complete_explore_step(
            state,
            monster,
            game_map,
            origin,
            rng,
            moved=moved,
            player=player,
            cache=cache,
        )
