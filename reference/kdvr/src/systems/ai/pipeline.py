"""Backward-compatible AI pipeline re-exports (PR10/PR11).

Historical tests and tools may patch ``src.systems.ai.pipeline.*``.
Prefer ``src.systems.ai.movement`` / ``src.systems.ai.visit`` for new code.
"""
from __future__ import annotations

from src.systems.combat import try_action
from src.systems.ai.movement import (
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

__all__ = [
    "StepResult",
    "try_action",
    "_choose_flee_direction",
    "_choose_wander_direction",
    "_consume_door_spite_wait_turn",
    "_execute_erratic_attack_step",
    "_execute_erratic_pursuit_step",
    "_execute_erratic_random_step",
    "_execute_intent_pipeline",
    "_nearest_threat_position",
    "_resolve_monster_move_direction",
    "_run_monster_visit",
    "_try_monster_move",
    "_try_predator_holding_attack",
    "run_monster_turns",
    "spawn_test_npc",
]
