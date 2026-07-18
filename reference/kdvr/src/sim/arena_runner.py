"""Single 1v1 arena trial loop for headless balance probing."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from src.arena import clear_arena_state, initialize_arena
from src.components import Engulfed, Fighter, Stunned
from src.data.entity_loader import load_entity_registry
from src.engine import GameEngine
from src.sim.arena_policy import execute_arena_policy_turn
from src.sim.modals import ModalStepResult, advance_modals, execute_engulfed_struggle


class ArenaTrialOutcome(Enum):
    PLAYER_WIN = auto()
    ENEMY_WIN = auto()
    DRAW = auto()


@dataclass(frozen=True)
class ArenaTrialResult:
    outcome: ArenaTrialOutcome
    player_hp_percent: float | None = None
    enemy_hp_percent: float | None = None
    turns_played: int = 0


def _hp_percent(entity) -> float | None:
    fighter = entity.components.get(Fighter)
    if fighter is None or fighter.max_hp <= 0:
        return None
    return round(100.0 * fighter.hp / fighter.max_hp, 1)


def _drain_rest_and_projectiles(engine: GameEngine) -> None:
    while engine.rest_in_progress():
        engine.advance_rest_animation()
    while engine.projectile_in_progress():
        engine.advance_projectile_animation()


def _enemy_hp_percent(engine: GameEngine) -> float | None:
    """HP% of the arena foe, preferring the live entity then digestion predator."""
    enemy = engine.arena_enemy_entity
    pct = _hp_percent(enemy) if enemy is not None else None
    if pct is not None:
        return pct
    predator = engine.digestion_modal.predator
    if predator is not None:
        return _hp_percent(predator)
    return None


def _run_one_arena_turn(engine: GameEngine) -> ModalStepResult:
    _drain_rest_and_projectiles(engine)

    if engine.arena_victory_active:
        return ModalStepResult.RUN_ENDED

    if engine.game_over.active:
        return ModalStepResult.RUN_ENDED

    modal_result = advance_modals(engine)
    if modal_result is ModalStepResult.RUN_ENDED:
        return modal_result

    if engine.arena_victory_active:
        return ModalStepResult.RUN_ENDED

    # Digestion / vore modals must only advance via advance_modals. Consuming
    # extra player turns while digestion_modal is open re-ticks digestion and
    # never finishes the modal → game_over never opens → false DRAWs.
    if engine.digestion_modal.active or engine.vore_modal.active:
        return ModalStepResult.CONTINUE

    player = engine.player
    if player is not None and Engulfed in player.tags:
        if Stunned not in player.tags:
            execute_engulfed_struggle(engine)
        else:
            engine._consume_player_turn()
        return ModalStepResult.CONTINUE

    execute_arena_policy_turn(engine)
    return ModalStepResult.CONTINUE


class ArenaSimRun:
    """Play one arena trial against a single entity id."""

    def __init__(
        self,
        *,
        entity_id: str,
        difficulty_id: str,
        seed: int,
        max_turns: int = 1000,
    ) -> None:
        self.entity_id = entity_id
        self.difficulty_id = difficulty_id
        self.seed = seed
        self.max_turns = max_turns

    def run(self) -> ArenaTrialResult:
        registry = load_entity_registry()
        engine = GameEngine(
            player_name="Player",
            difficulty_id=self.difficulty_id,
            save_coordinator=None,
            skip_new_game=True,
        )
        initialize_arena(engine, self.entity_id, seed=self.seed, registry=registry)

        turns = 0
        for _ in range(self.max_turns):
            turns += 1
            step = _run_one_arena_turn(engine)
            if engine.arena_victory_active:
                player = engine.player
                hp_pct = _hp_percent(player) if player is not None else None
                clear_arena_state(engine)
                return ArenaTrialResult(
                    outcome=ArenaTrialOutcome.PLAYER_WIN,
                    player_hp_percent=hp_pct,
                    turns_played=turns,
                )
            if step is ModalStepResult.RUN_ENDED or engine.game_over.active:
                hp_pct = _enemy_hp_percent(engine)
                clear_arena_state(engine)
                return ArenaTrialResult(
                    outcome=ArenaTrialOutcome.ENEMY_WIN,
                    enemy_hp_percent=hp_pct,
                    turns_played=turns,
                )

        clear_arena_state(engine)
        return ArenaTrialResult(
            outcome=ArenaTrialOutcome.DRAW,
            turns_played=turns,
        )