"""AI chase pursuit: memory, momentum, direction choice (PR9)."""
from __future__ import annotations

import random
from collections import deque
from typing import Literal

from tcod.ecs import Entity, Registry

from src import messages
from src.debug_log import debug_print
from src.components import (
    AI,
    AIState,
    Alignment,
    Engulfed,
    Fighter,
    NPCAlignment,
    Player,
    Position,
)
from src.map_gen import GameMap
from src.systems.movement import (
    MOVEMENT_DIRECTIONS,
    can_move_to,
    can_step_for_chase,
    is_stationary,
)
from src.systems.naming import entity_log_name
from src.systems.vore import find_predator_holding_prey
from src.systems.ai.common import (
    MEMORY_TRAIL_TURNS_MAX,
    MEMORY_TRAIL_TURNS_MIN,
    _cancel_door_spite,
    _chebyshev,
    _distance_squared_to,
    _forbidden_tiles,
    _get_ai_state,
    _has_los,
    _is_visible_to_ai,
    _npc_alignment,
    _pick_nearest_tied,
)
from src.systems.ai.explore import (
    ExploreBfsCache,
    _blocked_tiles_for_explore,
    _choose_explore_direction,
    _clear_explore_goal_distance_map,
    _is_explore_target_step,
    _reset_explore_frustration,
    _sanitize_unreachable_memory_targets,
    explore_distances_to_goal,
)
from src.systems.abilities import has_no_chase
from src.systems.ai.targeting import (
    _visible_good_evils,
    _visible_neutrals,
    _visible_primary_hostiles,
    pick_evil_chase,
    pick_good_chase,
)

ChaseMode = Literal["attack", "follow", "memory", "explore"]
ChaseStepPhase = Literal["none", "memory", "momentum"]

CHASE_MOMENTUM_TURNS_MIN = 3
CHASE_MOMENTUM_TURNS_MAX = 6
CHASE_FRUSTRATION_MIN = 8
CHASE_FRUSTRATION_MAX = 12
GOOD_CHASE_SWAPPABLE_ALIGNMENTS: frozenset[Alignment] = frozenset({Alignment.NEUTRAL})



def _clear_memory_of_engulfed_prey(state: AIState, world: Registry) -> None:
    """Drop memory entries that only refer to hidden engulfed prey."""
    for entity in world.Q.all_of(components=[Position, NPCAlignment]):
        if Engulfed not in entity.tags:
            continue
        prey_pos = entity.components[Position]
        if state.last_known_primary == prey_pos:
            state.last_known_primary = None
        if state.last_known_neutral == prey_pos:
            state.last_known_neutral = None


def _consume_reached_memory(state: AIState, pos: Position) -> bool:
    """Clear memory tiles reached this turn. Returns True when a quarry memory was cleared."""
    consumed_quarry = False
    if state.last_known_primary == pos:
        state.last_known_primary = None
        consumed_quarry = True
    if state.last_known_neutral == pos:
        state.last_known_neutral = None
        consumed_quarry = True
    if state.last_known_evil == pos:
        state.last_known_evil = None
        consumed_quarry = True
    if state.last_known_player == pos:
        state.last_known_player = None
        consumed_quarry = True
    if state.explore_goal == pos:
        state.explore_goal = None
        _reset_explore_frustration(state)
        _clear_explore_goal_distance_map(state)
    return consumed_quarry


def _reset_chase_pursuit(state: AIState) -> None:
    state.chase_momentum_direction = None
    state.chase_momentum_turns_left = 0
    state.chase_frustration = 0
    state.chase_frustration_limit = 0


def _clear_memory_pursuit_cache(state: AIState) -> None:
    """Drop ephemeral path-distance cache used for last-known pursuit."""
    state.memory_pursuit_distance_map = None
    state.memory_pursuit_map_target = None


def _reset_memory_blind_trail(state: AIState) -> None:
    state.memory_blind_turns = 0
    state.memory_blind_limit = 0


def _has_memory_quarry(state: AIState, alignment: Alignment) -> bool:
    if alignment == Alignment.EVIL:
        return (
            state.last_known_primary is not None
            or state.last_known_neutral is not None
        )
    if alignment == Alignment.GOOD:
        return (
            state.last_known_evil is not None
            or state.last_known_player is not None
        )
    return False


def _tick_memory_blind_trail(state: AIState, rng: random.Random) -> bool:
    """Count a blind turn; clear memory when the trail goes cold. Returns True if gave up."""
    if state.memory_blind_limit <= 0:
        state.memory_blind_limit = rng.randint(
            MEMORY_TRAIL_TURNS_MIN,
            MEMORY_TRAIL_TURNS_MAX,
        )
        state.memory_blind_turns = 0
    state.memory_blind_turns += 1
    if state.memory_blind_turns >= state.memory_blind_limit:
        _give_up_chase(state)
        return True
    return False


def _give_up_chase(state: AIState) -> None:
    state.last_known_primary = None
    state.last_known_neutral = None
    state.last_known_evil = None
    state.last_known_player = None
    # Come-here is honest pursuit of the player; lose-track ends the order.
    state.come_here = False
    _clear_memory_pursuit_cache(state)
    _reset_memory_blind_trail(state)
    _reset_chase_pursuit(state)


def _opposite_direction(direction: tuple[int, int]) -> tuple[int, int]:
    return (-direction[0], -direction[1])


def _evil_quarry_visible(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    *,
    player_engulfed: bool,
) -> bool:
    if _visible_primary_hostiles(
        monster,
        world,
        game_map,
        player,
        player_engulfed=player_engulfed,
    ):
        return True
    return bool(_visible_neutrals(monster, world, game_map))


def _good_quarry_visible(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    *,
    player_engulfed: bool,
) -> bool:
    origin = monster.components[Position]
    if player_engulfed:
        predator = find_predator_holding_prey(world, player)
        if predator is not None:
            predator_pos = predator.components[Position]
            if _has_los(game_map, origin, predator_pos):
                return True
    if _visible_good_evils(monster, world, game_map):
        return True
    player_pos = player.components[Position]
    return not player_engulfed and _has_los(game_map, origin, player_pos)


def _quarry_visible(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    *,
    alignment: Alignment,
    player_engulfed: bool,
) -> bool:
    if alignment == Alignment.EVIL:
        return _evil_quarry_visible(
            monster,
            world,
            game_map,
            player,
            player_engulfed=player_engulfed,
        )
    if alignment == Alignment.GOOD:
        return _good_quarry_visible(
            monster,
            world,
            game_map,
            player,
            player_engulfed=player_engulfed,
        )
    return False


def _ensure_memory_pursuit(state: AIState, rng: random.Random) -> None:
    if state.chase_frustration_limit == 0:
        state.chase_frustration_limit = rng.randint(
            CHASE_FRUSTRATION_MIN,
            CHASE_FRUSTRATION_MAX,
        )
        state.chase_frustration = 0


def _record_memory_pursuit_blocked(state: AIState) -> bool:
    """Count a failed step toward last-known position. Returns True if chase gives up."""
    if state.chase_frustration_limit == 0:
        return False
    state.chase_frustration += 1
    if state.chase_frustration >= state.chase_frustration_limit:
        _give_up_chase(state)
        return True
    return False


def _start_chase_momentum(state: AIState, rng: random.Random) -> None:
    if state.chase_momentum_direction is None:
        return
    state.chase_momentum_turns_left = rng.randint(
        CHASE_MOMENTUM_TURNS_MIN,
        CHASE_MOMENTUM_TURNS_MAX,
    )


def _on_quarry_memory_reached(
    state: AIState,
    rng: random.Random,
    *,
    consumed_quarry: bool,
    quarry_visible: bool,
    alignment: Alignment,
) -> None:
    if alignment not in (Alignment.EVIL, Alignment.GOOD):
        return
    if not consumed_quarry or quarry_visible:
        return
    state.chase_frustration = 0
    state.chase_frustration_limit = 0
    _start_chase_momentum(state, rng)


def _is_memory_chase_target(
    state: AIState,
    alignment: Alignment,
    *,
    entity_target: Entity | None,
    pos_target: Position | None,
    chase_mode: ChaseMode,
) -> bool:
    if entity_target is not None or pos_target is None:
        return False
    if alignment == Alignment.GOOD:
        return chase_mode == "memory"
    if alignment == Alignment.EVIL:
        return (
            state.last_known_primary is not None
            and pos_target == state.last_known_primary
        ) or (
            state.last_known_neutral is not None
            and pos_target == state.last_known_neutral
        )
    return False


def _prepare_chase_pursuit_turn(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    rng: random.Random,
    state: AIState,
    *,
    alignment: Alignment,
    player_engulfed: bool,
    monster_pos: Position,
) -> None:
    if alignment not in (Alignment.EVIL, Alignment.GOOD):
        return
    quarry_visible = _quarry_visible(
        monster,
        world,
        game_map,
        player,
        alignment=alignment,
        player_engulfed=player_engulfed,
    )
    if alignment == Alignment.EVIL and has_no_chase(monster) and not quarry_visible:
        _give_up_chase(state)
        return
    if quarry_visible:
        _reset_chase_pursuit(state)
        _reset_memory_blind_trail(state)
        _cancel_door_spite(state)
        return
    # Fair vision timeout: without LOS, last-known cannot last forever.
    if _has_memory_quarry(state, alignment):
        if _tick_memory_blind_trail(state, rng):
            return
    consumed_quarry = _consume_reached_memory(state, monster_pos)
    _on_quarry_memory_reached(
        state,
        rng,
        consumed_quarry=consumed_quarry,
        quarry_visible=quarry_visible,
        alignment=alignment,
    )


def _choose_momentum_direction(
    world: Registry,
    game_map: GameMap,
    monster: Entity,
    origin: Position,
    state: AIState,
    *,
    blocked_tiles: frozenset[Position],
) -> tuple[int, int] | None:
    if is_stationary(monster):
        return None
    preferred = state.chase_momentum_direction
    if preferred is None:
        return None
    backtrack = _opposite_direction(preferred)
    if can_move_to(
        world,
        game_map,
        monster,
        origin,
        preferred,
        blocked_tiles=blocked_tiles,
    ):
        return preferred
    candidates: list[tuple[int, int]] = []
    for direction in MOVEMENT_DIRECTIONS:
        if direction == backtrack:
            continue
        if can_move_to(
            world,
            game_map,
            monster,
            origin,
            direction,
            blocked_tiles=blocked_tiles,
        ):
            candidates.append(direction)
    if not candidates:
        return None
    if preferred != (0, 0):
        px, py = preferred
        candidates.sort(key=lambda direction: -(direction[0] * px + direction[1] * py))
    return candidates[0]


def _pick_pursuit_direction(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    rng: random.Random,
    state: AIState,
    origin: Position,
    *,
    alignment: Alignment,
    blocked_tiles: frozenset[Position],
    player_engulfed: bool,
    entity_target: Entity | None,
    pos_target: Position | None,
    chase_mode: ChaseMode,
) -> tuple[tuple[int, int] | None, ChaseStepPhase]:
    if alignment not in (Alignment.EVIL, Alignment.GOOD):
        return None, "none"
    if entity_target is not None:
        _reset_chase_pursuit(state)
        return None, "none"
    if alignment == Alignment.EVIL and has_no_chase(monster):
        if not _quarry_visible(
            monster,
            world,
            game_map,
            player,
            alignment=alignment,
            player_engulfed=player_engulfed,
        ):
            return None, "none"
    if _quarry_visible(
        monster,
        world,
        game_map,
        player,
        alignment=alignment,
        player_engulfed=player_engulfed,
    ):
        _reset_chase_pursuit(state)
        return None, "none"
    if state.chase_momentum_turns_left > 0:
        return (
            _choose_momentum_direction(
                world,
                game_map,
                monster,
                origin,
                state,
                blocked_tiles=blocked_tiles,
            ),
            "momentum",
        )
    if _is_memory_chase_target(
        state,
        alignment,
        entity_target=entity_target,
        pos_target=pos_target,
        chase_mode=chase_mode,
    ):
        _ensure_memory_pursuit(state, rng)
        assert pos_target is not None
        return (
            _choose_memory_pursuit_direction(
                world,
                game_map,
                monster,
                origin,
                pos_target,
                state,
                rng,
                blocked_tiles=blocked_tiles,
                swappable_bump_alignments=(
                    GOOD_CHASE_SWAPPABLE_ALIGNMENTS
                    if alignment == Alignment.GOOD
                    else None
                ),
            ),
            "memory",
        )
    return None, "none"


def _memory_step_made_progress(
    state: AIState,
    *,
    origin: Position | None,
    current_pos: Position | None,
    memory_target: Position | None,
) -> bool:
    """True when the step reduced BFS path distance (preferred) or Euclidean distance."""
    if origin is None or current_pos is None or memory_target is None:
        return True
    if (
        state.memory_pursuit_map_target == memory_target
        and state.memory_pursuit_distance_map is not None
    ):
        before = state.memory_pursuit_distance_map.get(origin)
        after = state.memory_pursuit_distance_map.get(current_pos)
        if before is None or after is None:
            return False
        return after < before
    return _distance_squared_to(current_pos, memory_target) < _distance_squared_to(
        origin, memory_target
    )


def _complete_pursuit_step(
    state: AIState,
    direction: tuple[int, int] | None,
    *,
    phase: ChaseStepPhase,
    moved: bool,
    origin: Position | None = None,
    current_pos: Position | None = None,
    memory_target: Position | None = None,
) -> None:
    if phase == "none":
        return
    if phase == "memory":
        if direction is None or not moved:
            _record_memory_pursuit_blocked(state)
            return
        if not _memory_step_made_progress(
            state,
            origin=origin,
            current_pos=current_pos,
            memory_target=memory_target,
        ):
            _record_memory_pursuit_blocked(state)
            return
        state.chase_frustration = 0
        state.chase_momentum_direction = direction
        return
    if direction is not None and moved:
        state.chase_momentum_direction = direction
    if phase == "momentum":
        state.chase_momentum_turns_left = max(0, state.chase_momentum_turns_left - 1)
        if state.chase_momentum_turns_left == 0:
            _give_up_chase(state)


def _update_ai_memory(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    rng: random.Random,
    *,
    player_engulfed: bool,
) -> None:
    state = _get_ai_state(monster)
    origin = monster.components[Position]
    alignment = _npc_alignment(monster)

    if alignment == Alignment.EVIL:
        primaries = _visible_primary_hostiles(
            monster, world, game_map, player, player_engulfed=player_engulfed
        )
        neutrals = _visible_neutrals(monster, world, game_map)
        if has_no_chase(monster):
            if primaries:
                state.last_known_primary = _pick_nearest_tied(
                    origin, primaries, rng
                ).components[Position]
            else:
                state.last_known_primary = None
            if neutrals:
                state.last_known_neutral = _pick_nearest_tied(
                    origin, neutrals, rng
                ).components[Position]
            else:
                state.last_known_neutral = None
            if not primaries and not neutrals:
                _reset_chase_pursuit(state)
                _reset_memory_blind_trail(state)
            _clear_memory_of_engulfed_prey(state, world)
            return
        if primaries:
            state.last_known_primary = _pick_nearest_tied(
                origin, primaries, rng
            ).components[Position]
        if neutrals:
            state.last_known_neutral = _pick_nearest_tied(
                origin, neutrals, rng
            ).components[Position]
        _clear_memory_of_engulfed_prey(state, world)
        return

    if alignment == Alignment.GOOD:
        evils = _visible_good_evils(monster, world, game_map)
        if evils:
            state.last_known_evil = _pick_nearest_tied(
                origin, evils, rng
            ).components[Position]
        player_pos = player.components[Position]
        if not player_engulfed and _has_los(game_map, origin, player_pos):
            state.last_known_player = player_pos
        _clear_memory_of_engulfed_prey(state, world)


def _choose_chase_direction(
    world: Registry,
    game_map: GameMap,
    monster: Entity,
    origin: Position,
    target: Position,
    *,
    blocked_tiles: frozenset[Position] = frozenset(),
    avoid_positions: frozenset[Position] = frozenset(),
    swappable_bump_alignments: frozenset[Alignment] | None = None,
) -> tuple[int, int] | None:
    """Pick the legal step that minimizes Euclidean distance to the target.

    Visible chase / follow stay greedy. Memory pursuit uses
    ``_choose_memory_pursuit_direction`` (BFS path distance) instead so NPCs
    take detours around closed doors instead of dancing on the Euclidean local
    minimum at the door face.
    """
    best_direction: tuple[int, int] | None = None
    best_distance = float("inf")
    origin_distance = (target.x - origin.x) ** 2 + (target.y - origin.y) ** 2

    for direction in MOVEMENT_DIRECTIONS:
        dest = origin + direction
        if dest in avoid_positions:
            continue
        if is_stationary(monster) and dest != target:
            continue
        if dest == target:
            if dest in blocked_tiles:
                continue
            distance = (target.x - dest.x) ** 2 + (target.y - dest.y) ** 2
            if distance < best_distance:
                best_distance = distance
                best_direction = direction
            continue
        step_legal = (
            can_step_for_chase(
                world,
                game_map,
                monster,
                origin,
                direction,
                blocked_tiles=blocked_tiles,
                swappable_defender_alignments=swappable_bump_alignments,
            )
            if swappable_bump_alignments is not None
            else can_move_to(
                world,
                game_map,
                monster,
                origin,
                direction,
                blocked_tiles=blocked_tiles,
            )
        )
        if not step_legal:
            continue
        distance = (target.x - dest.x) ** 2 + (target.y - dest.y) ** 2
        if distance < best_distance:
            best_distance = distance
            best_direction = direction

    # Do not walk *away* from a visible target when no improving step exists;
    # standing still lets callers treat the step as blocked/frustrated.
    if best_direction is not None and best_distance >= origin_distance:
        return None
    return best_direction


def _memory_pursuit_distances(
    state: AIState,
    game_map: GameMap,
    target: Position,
    entity: Entity,
) -> dict[Position, int]:
    """BFS path distances to a last-known tile (cached for the active target)."""
    if (
        state.memory_pursuit_map_target == target
        and state.memory_pursuit_distance_map is not None
    ):
        return state.memory_pursuit_distance_map
    distances = explore_distances_to_goal(game_map, target, entity)
    state.memory_pursuit_map_target = target
    state.memory_pursuit_distance_map = distances
    return distances


def _choose_memory_pursuit_direction(
    world: Registry,
    game_map: GameMap,
    monster: Entity,
    origin: Position,
    target: Position,
    state: AIState,
    rng: random.Random,
    *,
    blocked_tiles: frozenset[Position] = frozenset(),
    swappable_bump_alignments: frozenset[Alignment] | None = None,
) -> tuple[int, int] | None:
    """One BFS-shortest-path step toward last-known; None when no path progress."""
    if is_stationary(monster):
        return None
    distances = _memory_pursuit_distances(state, game_map, target, monster)
    origin_dist = distances.get(origin)
    if origin_dist is None:
        return None

    best_distance = origin_dist
    best_directions: list[tuple[int, int]] = []
    for direction in MOVEMENT_DIRECTIONS:
        dest = origin + direction
        if dest in blocked_tiles:
            continue
        step_legal = (
            can_step_for_chase(
                world,
                game_map,
                monster,
                origin,
                direction,
                blocked_tiles=blocked_tiles,
                swappable_defender_alignments=swappable_bump_alignments,
            )
            if swappable_bump_alignments is not None
            else can_move_to(
                world,
                game_map,
                monster,
                origin,
                direction,
                blocked_tiles=blocked_tiles,
            )
        )
        if not step_legal:
            continue
        dest_dist = distances.get(dest)
        if dest_dist is None:
            continue
        if dest_dist < best_distance:
            best_distance = dest_dist
            best_directions = [direction]
        elif dest_dist == best_distance and dest_dist < origin_dist:
            best_directions.append(direction)

    if not best_directions:
        return None
    return rng.choice(best_directions)


def _choose_good_follow_direction(
    world: Registry,
    game_map: GameMap,
    monster: Entity,
    origin: Position,
    player: Entity,
) -> tuple[int, int] | None:
    player_pos = player.components[Position]
    blocked = _forbidden_tiles(monster, player)
    ideal = _choose_chase_direction(
        world,
        game_map,
        monster,
        origin,
        player_pos,
        blocked_tiles=frozenset(),
        swappable_bump_alignments=GOOD_CHASE_SWAPPABLE_ALIGNMENTS,
    )
    if ideal is not None and (origin + ideal) == player_pos:
        debug_print(
            messages.good_attempted_player_swap(entity_log_name(monster)),
            flush=True,
        )
        return None
    return _choose_chase_direction(
        world,
        game_map,
        monster,
        origin,
        player_pos,
        blocked_tiles=blocked,
        swappable_bump_alignments=GOOD_CHASE_SWAPPABLE_ALIGNMENTS,
    )


def _resolve_chase_direction(
    world: Registry,
    game_map: GameMap,
    monster: Entity,
    origin: Position,
    *,
    target_entity: Entity | None,
    target_position: Position | None,
    chase_mode: ChaseMode,
    player: Entity,
    blocked: frozenset[Position],
    state: AIState | None = None,
    rng: random.Random | None = None,
    alignment: Alignment | None = None,
    player_engulfed: bool = False,
    cache: ExploreBfsCache | None = None,
    explore_allow_idle: bool = True,
) -> tuple[tuple[int, int] | None, ChaseStepPhase]:
    if (
        state is not None
        and rng is not None
        and alignment is not None
        and alignment in (Alignment.EVIL, Alignment.GOOD)
    ):
        pursuit_direction, phase = _pick_pursuit_direction(
            monster,
            world,
            game_map,
            player,
            rng,
            state,
            origin,
            alignment=alignment,
            blocked_tiles=blocked,
            player_engulfed=player_engulfed,
            entity_target=target_entity,
            pos_target=target_position,
            chase_mode=chase_mode,
        )
        if phase != "none":
            return pursuit_direction, phase

    if target_entity is not None:
        if chase_mode == "follow" and Player in target_entity.tags:
            return (
                _choose_good_follow_direction(world, game_map, monster, origin, player),
                "none",
            )
        target_pos = target_entity.components[Position]
        swappable = (
            GOOD_CHASE_SWAPPABLE_ALIGNMENTS
            if _npc_alignment(monster) == Alignment.GOOD
            else None
        )
        return (
            _choose_chase_direction(
                world,
                game_map,
                monster,
                origin,
                target_pos,
                blocked_tiles=blocked,
                swappable_bump_alignments=swappable,
            ),
            "none",
        )
    if target_position is not None:
        if (
            state is not None
            and rng is not None
            and _is_explore_target_step(monster, state, target_position, chase_mode)
        ):
            explore_blocked = _blocked_tiles_for_explore(monster, world, blocked)
            return (
                _choose_explore_direction(
                    world,
                    game_map,
                    monster,
                    origin,
                    target_position,
                    monster,
                    rng,
                    blocked_tiles=explore_blocked,
                    recent_positions=state.explore_recent_positions,
                    state=state,
                    allow_idle=explore_allow_idle,
                ),
                "none",
            )
        swappable = (
            GOOD_CHASE_SWAPPABLE_ALIGNMENTS
            if _npc_alignment(monster) == Alignment.GOOD
            else None
        )
        return (
            _choose_chase_direction(
                world,
                game_map,
                monster,
                origin,
                target_position,
                blocked_tiles=blocked,
                swappable_bump_alignments=swappable,
            ),
            "none",
        )
    return None, "none"


def _adjacent_attack_targets(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    *,
    alignment: Alignment,
    player_engulfed: bool,
) -> list[Entity]:
    """Visible hostiles within Chebyshev distance 1 that Erratic ATTACK may strike."""
    origin = monster.components[Position]
    candidates: list[Entity] = []
    if alignment == Alignment.EVIL:
        candidates.extend(
            _visible_primary_hostiles(
                monster,
                world,
                game_map,
                player,
                player_engulfed=player_engulfed,
            )
        )
        candidates.extend(_visible_neutrals(monster, world, game_map))
    elif alignment == Alignment.GOOD:
        candidates.extend(_visible_good_evils(monster, world, game_map))
    else:
        candidates.extend(_visible_evils(monster, world, game_map))

    adjacent: list[Entity] = []
    seen: set[int] = set()
    for entity in candidates:
        if id(entity) in seen:
            continue
        seen.add(id(entity))
        if _chebyshev(origin, entity.components[Position]) == 1:
            adjacent.append(entity)
    if adjacent:
        return adjacent
    return []


def _direction_toward(origin: Position, target: Position) -> tuple[int, int] | None:
    dx = target.x - origin.x
    dy = target.y - origin.y
    if dx == 0 and dy == 0:
        return None
    step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
    step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
    return (step_x, step_y)


def _print_evil_frustration_if_blocked(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    rng: random.Random,
    *,
    player_engulfed: bool,
    cache: ExploreBfsCache | None = None,
    player_turn_count: int = 0,
    distant_throttle: bool = False,
) -> None:
    """System-log frustration when a visible primary is blocked by a neutral."""
    entity_target, _, blocked_primary = pick_evil_chase(
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

