"""NPC AI package.

Layout
------
- ``common`` — shared helpers, door spite/shock constants, trail timeout
- ``explore`` — BFS goals, frustration, oscillation
- ``targeting`` — pick_evil_*, pick_good_chase, visible sets
- ``chase`` — memory pursuit, momentum, direction resolve
- ``movement`` — flee/wander/erratic random, try_monster_move
- ``visit`` — plan execution, ``run_monster_turns``, test spawn
- ``pipeline`` — thin historical re-export shim (prefer submodules)

Public production API
---------------------
Prefer these names from ``src.systems.ai`` (or import from the submodule):

- ``run_monster_turns`` — world-phase NPC visits
- ``pick_evil_chase``, ``pick_evil_target``, ``pick_good_chase``, ``pick_hostile_target``
- ``spawn_test_npc`` — tests / tools only

Constants used by tests (door spite, trail timeout, explore/chase limits) remain
importable from this package. Underscore-prefixed helpers stay re-exported for
test compatibility; new production code should import them from the owning
submodule rather than treating the package root as a private grab-bag.
"""
from __future__ import annotations

from src.systems.ai.common import (
    DOOR_SHOCK_TURNS_MAX,
    DOOR_SHOCK_TURNS_MIN,
    DOOR_SPITE_TURNS_MAX,
    DOOR_SPITE_TURNS_MIN,
    MEMORY_TRAIL_TURNS_MAX,
    MEMORY_TRAIL_TURNS_MIN,
    _cancel_door_spite,
    _chebyshev,
    _distant_throttle_applies,
    _distance_squared_to,
    _entity_has_hands_ability,
    _floor_is_busy,
    _forbidden_tiles,
    _get_ability_state,
    _get_ai_state,
    _half_turn_should_act,
    _has_los,
    _is_distant_from_player,
    _is_visible_to_ai,
    _npc_alignment,
    _pick_nearest_tied,
    _pick_random_walkable_tile,
    _sorted_monsters,
    _start_door_spite,
    _visible_evils,
)
from src.systems.ai.explore import (
    EXPLORE_FRUSTRATION_MAX,
    EXPLORE_FRUSTRATION_MIN,
    EXPLORE_IDLE_CHANCE,
    EXPLORE_OSCILLATION_HISTORY,
    ExploreBfsCache,
    ExploreTerrainCache,
    _blocked_tiles_for_explore,
    _choose_explore_direction,
    _choose_explore_sidestep,
    _complete_explore_step,
    _ensure_explore_goal,
    _explore_frustration_give_up,
    _explore_is_oscillating,
    _is_explore_step,
    _is_explore_target_step,
    _is_neutral_explore_step,
    _pick_farthest_explore_goal,
    _pick_weighted_far_explore_goal,
    _sanitize_unreachable_memory_targets,
    entity_explore_can_traverse,
    explore_distances_to_goal,
    explore_reachable_distances,
)
from src.systems.ai.targeting import (
    _frustration_blockers,
    _frustration_blockers_to_pos,
    _monster_should_act,
    _visible_good_evils,
    _visible_hostiles,
    _visible_neutrals,
    _visible_primary_hostiles,
    pick_evil_chase,
    pick_evil_target,
    pick_good_chase,
    pick_hostile_target,
)
from src.systems.ai.chase import (
    CHASE_FRUSTRATION_MAX,
    CHASE_FRUSTRATION_MIN,
    CHASE_MOMENTUM_TURNS_MAX,
    CHASE_MOMENTUM_TURNS_MIN,
    GOOD_CHASE_SWAPPABLE_ALIGNMENTS,
    ChaseMode,
    ChaseStepPhase,
    _adjacent_attack_targets,
    _choose_chase_direction,
    _choose_good_follow_direction,
    _choose_memory_pursuit_direction,
    _choose_momentum_direction,
    _clear_memory_of_engulfed_prey,
    _clear_memory_pursuit_cache,
    _complete_pursuit_step,
    _consume_reached_memory,
    _direction_toward,
    _ensure_memory_pursuit,
    _evil_quarry_visible,
    _give_up_chase,
    _good_quarry_visible,
    _is_memory_chase_target,
    _on_quarry_memory_reached,
    _opposite_direction,
    _pick_pursuit_direction,
    _prepare_chase_pursuit_turn,
    _print_evil_frustration_if_blocked,
    _quarry_visible,
    _record_memory_pursuit_blocked,
    _reset_chase_pursuit,
    _resolve_chase_direction,
    _start_chase_momentum,
    _update_ai_memory,
)
from src.systems.ai.movement import (
    _choose_erratic_random_direction,
    _choose_flee_direction,
    _choose_wander_direction,
    _consume_door_spite_wait_turn,
    _nearest_threat_position,
    _resolve_monster_move_direction,
    _try_monster_move,
    _try_predator_holding_attack,
)
from src.systems.ai.visit import (
    StepResult,
    _execute_erratic_attack_step,
    _execute_erratic_pursuit_step,
    _execute_erratic_random_step,
    _execute_intent_pipeline,
    _run_monster_visit,
    run_monster_turns,
    spawn_test_npc,
)
# Historical test patch target (combat.try_action re-export)
from src.systems.combat import try_action as try_action

# Intended production-facing names (also used by tests).
_PUBLIC = (
    "run_monster_turns",
    "pick_evil_chase",
    "pick_evil_target",
    "pick_good_chase",
    "pick_hostile_target",
    "spawn_test_npc",
    "try_action",
    "ExploreBfsCache",
    "ExploreTerrainCache",
    "entity_explore_can_traverse",
    "explore_distances_to_goal",
    "explore_reachable_distances",
    "DOOR_SPITE_TURNS_MIN",
    "DOOR_SPITE_TURNS_MAX",
    "DOOR_SHOCK_TURNS_MIN",
    "DOOR_SHOCK_TURNS_MAX",
    "MEMORY_TRAIL_TURNS_MIN",
    "MEMORY_TRAIL_TURNS_MAX",
    "EXPLORE_FRUSTRATION_MIN",
    "EXPLORE_FRUSTRATION_MAX",
    "EXPLORE_IDLE_CHANCE",
    "EXPLORE_OSCILLATION_HISTORY",
    "CHASE_FRUSTRATION_MIN",
    "CHASE_FRUSTRATION_MAX",
    "CHASE_MOMENTUM_TURNS_MIN",
    "CHASE_MOMENTUM_TURNS_MAX",
    "ChaseMode",
    "ChaseStepPhase",
    "StepResult",
    "GOOD_CHASE_SWAPPABLE_ALIGNMENTS",
)

# Keep private helpers importable for existing tests; prefer submodule imports.
__all__ = [n for n in globals() if not n.startswith("__") and n != "_PUBLIC"]
