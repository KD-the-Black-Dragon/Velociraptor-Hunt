"""AI targeting: visible hostiles, pick chase targets (PR9)."""
from __future__ import annotations

import random
from typing import TYPE_CHECKING

from tcod.ecs import Entity, Registry

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
from src.systems.ai.common import (
    _cancel_door_spite,
    _closed_door_toward_target,
    _entity_has_hands_ability,
    _start_door_shock,
    _chebyshev,
    _get_ai_state,
    _has_los,
    _is_visible_to_ai,
    _npc_alignment,
    _pick_nearest_tied,
)
from src.systems.ai.explore import (
    ExploreBfsCache,
    _ensure_explore_goal,
    _sanitize_unreachable_memory_targets,
)
from src.systems.abilities import has_no_chase
from src.systems.vore import find_predator_holding_prey

if TYPE_CHECKING:
    from src.systems.ai.chase import ChaseMode
else:
    from typing import Literal
    ChaseMode = Literal["attack", "follow", "memory", "explore"]



def _visible_primary_hostiles(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    *,
    player_engulfed: bool = False,
) -> list[Entity]:
    """Evil enticing targets: the player and good NPCs in line of sight."""
    origin = monster.components[Position]
    hostiles: list[Entity] = []
    player_pos = player.components[Position]
    if not player_engulfed and _has_los(game_map, origin, player_pos):
        hostiles.append(player)
    for entity in world.Q.all_of(components=[AI, Position, NPCAlignment, Fighter]):
        if entity is monster or Player in entity.tags:
            continue
        if not _is_visible_to_ai(entity):
            continue
        if _npc_alignment(entity) != Alignment.GOOD:
            continue
        target_pos = entity.components[Position]
        if _has_los(game_map, origin, target_pos):
            hostiles.append(entity)
    return hostiles


def _visible_neutrals(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
) -> list[Entity]:
    origin = monster.components[Position]
    neutrals: list[Entity] = []
    for entity in world.Q.all_of(components=[AI, Position, NPCAlignment, Fighter]):
        if entity is monster or Player in entity.tags:
            continue
        if not _is_visible_to_ai(entity):
            continue
        if _npc_alignment(entity) != Alignment.NEUTRAL:
            continue
        target_pos = entity.components[Position]
        if _has_los(game_map, origin, target_pos):
            neutrals.append(entity)
    return neutrals


def _visible_good_evils(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
) -> list[Entity]:
    origin = monster.components[Position]
    evils: list[Entity] = []
    for entity in world.Q.all_of(components=[AI, Position, NPCAlignment, Fighter]):
        if entity is monster or Player in entity.tags:
            continue
        if not _is_visible_to_ai(entity):
            continue
        if _npc_alignment(entity) != Alignment.EVIL:
            continue
        target_pos = entity.components[Position]
        if _has_los(game_map, origin, target_pos):
            evils.append(entity)
    return evils


def _frustration_blockers_to_pos(
    origin: Position,
    primary_pos: Position,
    candidates: list[Entity],
) -> list[Entity]:
    """Candidates that stand between origin and primary (hallway-blocker geometry)."""
    dist_to_primary = _chebyshev(origin, primary_pos)
    if dist_to_primary <= 1:
        return []
    blockers: list[Entity] = []
    for candidate in candidates:
        candidate_pos = candidate.components[Position]
        dist_to_candidate = _chebyshev(origin, candidate_pos)
        dist_candidate_to_primary = _chebyshev(candidate_pos, primary_pos)
        if (
            dist_to_candidate < dist_to_primary
            and dist_candidate_to_primary < dist_to_primary
        ):
            blockers.append(candidate)
    return blockers


def _frustration_blockers(
    origin: Position,
    primary: Entity,
    neutrals: list[Entity],
) -> list[Entity]:
    """Neutrals visible to evil that stand between it and an enticing primary target."""
    return _frustration_blockers_to_pos(
        origin,
        primary.components[Position],
        neutrals,
    )


def pick_evil_target(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    rng: random.Random,
    *,
    player_engulfed: bool = False,
) -> tuple[Entity | None, Entity | None]:
    """
    Visible primary target with frustration: retarget a neutral blocking the path
    to a visible player or good NPC. Returns (chase_target, blocked_primary).
    """
    primaries = _visible_primary_hostiles(
        monster, world, game_map, player, player_engulfed=player_engulfed
    )
    if not primaries:
        return None, None

    origin = monster.components[Position]
    primary = _pick_nearest_tied(origin, primaries, rng)
    blockers = _frustration_blockers(
        origin,
        primary,
        _visible_neutrals(monster, world, game_map),
    )
    if blockers:
        return _pick_nearest_tied(origin, blockers, rng), primary
    return primary, None


def pick_evil_chase(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    rng: random.Random,
    *,
    player_engulfed: bool = False,
    cache: ExploreBfsCache | None = None,
    player_turn_count: int = 0,
    distant_throttle: bool = False,
) -> tuple[Entity | None, Position | None, Entity | None]:
    """
    Evil priority: primary (with frustration) → last known primary → neutral
    → last known neutral → explore. Returns (entity, position, blocked_primary).

    When distant_throttle (D3): skip sanitize and last_known_* position pursuit;
    visible targets and full explore BFS still apply.
    """
    state = _get_ai_state(monster)
    origin = monster.components[Position]
    if not distant_throttle:
        _sanitize_unreachable_memory_targets(
            state,
            game_map,
            origin,
            monster,
            rng,
            cache=cache,
            player_turn_count=player_turn_count,
        )
    if _entity_has_hands_ability(monster):
        _cancel_door_spite(state)
    elif state.door_spite_turns_left > 0:
        return None, None, None
    primaries = _visible_primary_hostiles(
        monster, world, game_map, player, player_engulfed=player_engulfed
    )
    if primaries:
        _cancel_door_spite(state)
        entity, blocked = pick_evil_target(
            monster,
            world,
            game_map,
            player,
            rng,
            player_engulfed=player_engulfed,
        )
        return entity, None, blocked

    if has_no_chase(monster):
        neutrals = _visible_neutrals(monster, world, game_map)
        if neutrals:
            return _pick_nearest_tied(origin, neutrals, rng), None, None
        return (
            None,
            _ensure_explore_goal(
                state,
                game_map,
                origin,
                monster,
                rng,
                cache=cache,
            ),
            None,
        )

    if not distant_throttle and state.last_known_primary is not None:
        # Door slammed in face: brief shock early in the blind trail, then detour.
        if (
            not _entity_has_hands_ability(monster)
            and state.door_spite_turns_left <= 0
            and state.memory_blind_turns <= 2
            and _closed_door_toward_target(game_map, origin, state.last_known_primary)
        ):
            _start_door_shock(state, rng)
        if state.door_spite_turns_left > 0:
            return None, None, None
        return None, state.last_known_primary, None

    neutrals = _visible_neutrals(monster, world, game_map)
    if neutrals:
        return _pick_nearest_tied(origin, neutrals, rng), None, None

    if not distant_throttle and state.last_known_neutral is not None:
        if (
            not _entity_has_hands_ability(monster)
            and state.door_spite_turns_left <= 0
            and state.memory_blind_turns <= 2
            and _closed_door_toward_target(game_map, origin, state.last_known_neutral)
        ):
            _start_door_shock(state, rng)
        if state.door_spite_turns_left > 0:
            return None, None, None
        return None, state.last_known_neutral, None

    return (
        None,
        _ensure_explore_goal(
            state,
            game_map,
            origin,
            monster,
            rng,
            cache=cache,
        ),
        None,
    )


def pick_good_chase(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    rng: random.Random,
    *,
    player_engulfed: bool = False,
    cache: ExploreBfsCache | None = None,
    player_turn_count: int = 0,
    distant_throttle: bool = False,
) -> tuple[Entity | None, Position | None, ChaseMode]:
    """Good priority: rescue → (come-here tag) → evil → follow → memory → explore.

    When distant_throttle (D3): skip sanitize and last_known_* pathing.
    """
    from src.systems.vore import is_adjacent

    state = _get_ai_state(monster)
    origin = monster.components[Position]
    player_pos = player.components[Position]
    if not distant_throttle:
        _sanitize_unreachable_memory_targets(
            state,
            game_map,
            origin,
            monster,
            rng,
            cache=cache,
            player_turn_count=player_turn_count,
        )
    if _entity_has_hands_ability(monster):
        _cancel_door_spite(state)
    elif state.door_spite_turns_left > 0:
        return None, None, "explore"

    # Tag complete: any adjacency ends come-here before other priorities.
    if state.come_here and not player_engulfed and is_adjacent(origin, player_pos):
        state.come_here = False

    if player_engulfed:
        predator = find_predator_holding_prey(world, player)
        if predator is not None:
            predator_pos = predator.components[Position]
            if _has_los(game_map, origin, predator_pos):
                _cancel_door_spite(state)
                return predator, None, "attack"

    # Come-here: approach player only (honest LOS/memory); frustration vs blocking evil.
    if state.come_here:
        _cancel_door_spite(state)
        if not player_engulfed and _has_los(game_map, origin, player_pos):
            evils = _visible_good_evils(monster, world, game_map)
            blockers = _frustration_blockers_to_pos(origin, player_pos, evils)
            if blockers:
                return _pick_nearest_tied(origin, blockers, rng), None, "attack"
            return player, None, "follow"
        if not distant_throttle and state.last_known_player is not None:
            evils = _visible_good_evils(monster, world, game_map)
            blockers = _frustration_blockers_to_pos(
                origin, state.last_known_player, evils
            )
            if blockers:
                return _pick_nearest_tied(origin, blockers, rng), None, "attack"
            return None, state.last_known_player, "memory"
        # Cannot pursue honestly — drop order and fall through to standard AI.
        state.come_here = False

    evils = _visible_good_evils(monster, world, game_map)
    if evils:
        _cancel_door_spite(state)
        return _pick_nearest_tied(origin, evils, rng), None, "attack"

    if not player_engulfed and _has_los(game_map, origin, player_pos):
        _cancel_door_spite(state)
        return player, None, "follow"

    if not distant_throttle and state.last_known_evil is not None:
        if (
            not _entity_has_hands_ability(monster)
            and state.door_spite_turns_left <= 0
            and state.memory_blind_turns <= 2
            and _closed_door_toward_target(game_map, origin, state.last_known_evil)
        ):
            _start_door_shock(state, rng)
        if state.door_spite_turns_left > 0:
            return None, None, "explore"
        return None, state.last_known_evil, "memory"

    if not distant_throttle and state.last_known_player is not None:
        if (
            not _entity_has_hands_ability(monster)
            and state.door_spite_turns_left <= 0
            and state.memory_blind_turns <= 2
            and _closed_door_toward_target(game_map, origin, state.last_known_player)
        ):
            _start_door_shock(state, rng)
        if state.door_spite_turns_left > 0:
            return None, None, "explore"
        return None, state.last_known_player, "memory"

    return (
        None,
        _ensure_explore_goal(
            state,
            game_map,
            origin,
            monster,
            rng,
            cache=cache,
        ),
        "explore",
    )


def _visible_hostiles(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    *,
    player_engulfed: bool = False,
) -> list[Entity]:
    alignment = _npc_alignment(monster)

    if alignment == Alignment.EVIL:
        return _visible_primary_hostiles(
            monster, world, game_map, player, player_engulfed=player_engulfed
        )
    if alignment == Alignment.GOOD:
        return _visible_good_evils(monster, world, game_map)
    return []


def pick_hostile_target(
    monster: Entity,
    world: Registry,
    game_map: GameMap,
    player: Entity,
    rng: random.Random,
    *,
    player_engulfed: bool = False,
) -> Entity | None:
    if _npc_alignment(monster) == Alignment.EVIL:
        target, _ = pick_evil_target(
            monster,
            world,
            game_map,
            player,
            rng,
            player_engulfed=player_engulfed,
        )
        return target
    hostiles = _visible_hostiles(
        monster, world, game_map, player, player_engulfed=player_engulfed
    )
    if not hostiles:
        return None
    origin = monster.components[Position]
    return _pick_nearest_tied(origin, hostiles, rng)


def _monster_should_act(monster: Entity) -> bool:
    if _npc_alignment(monster) == Alignment.NEUTRAL:
        fighter = monster.components.get(Fighter)
        if fighter is None or fighter.hp <= 0:
            return False
    return True

