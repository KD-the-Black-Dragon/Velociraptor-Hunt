"""Advance blocking modals during headless simulation."""

from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

from src.components import Engulfed, Position
from src.systems.inventory import pickup_all_items_at
from src.systems.movement import MOVEMENT_DIRECTIONS
from src.systems.vore import try_struggle

if TYPE_CHECKING:
    from src.engine import GameEngine


class ModalStepResult(Enum):
    CONTINUE = auto()
    RUN_ENDED = auto()


def advance_modals(engine: GameEngine) -> ModalStepResult:
    """Advance one step of any blocking modal, or return CONTINUE."""
    if engine.game_over.active:
        return ModalStepResult.RUN_ENDED

    if engine.digestion_modal.active:
        engine._advance_digestion_modal()
        if engine.game_over.active:
            return ModalStepResult.RUN_ENDED
        return ModalStepResult.CONTINUE

    if engine.vore_modal.active:
        predator = engine.vore_modal.predator
        if (
            predator is None
            or Position not in predator.components
            or engine.player is None
        ):
            engine.vore_modal.reset()
        else:
            engine._advance_vore_modal()
            if engine.game_over.active:
                return ModalStepResult.RUN_ENDED
        return ModalStepResult.CONTINUE

    if engine.ground_pickup_modal.active:
        _take_all_ground_pickup(engine)
        return ModalStepResult.CONTINUE

    if engine.inventory_modal.active:
        engine.inventory_modal.reset()

    if engine.macguffin_victory_confirm.active:
        engine.macguffin_victory_confirm.reset()

    return ModalStepResult.CONTINUE


def execute_engulfed_struggle(engine: GameEngine) -> None:
    """Struggle while engulfed; consumes a player turn."""
    player = engine.player
    if player is None or Engulfed not in player.tags:
        return
    direction = engine.rng.choice(MOVEMENT_DIRECTIONS)
    try_struggle(
        engine.world,
        engine.game_map,
        player,
        direction,
        engine.message_log,
        engine.rng,
        run_stats=engine.run_stats,
        alternate_cv_mechanics=engine.alternate_cv_mechanics,
        difficulty_profile=engine.difficulty_profile(),
    )
    engine._consume_player_turn()


def _take_all_ground_pickup(engine: GameEngine) -> None:
    player = engine.player
    if player is None:
        engine.ground_pickup_modal.reset()
        return
    pos = player.components.get(Position)
    if pos is None:
        engine.ground_pickup_modal.reset()
        return
    pickup_all_items_at(
        engine.world,
        player,
        pos.x,
        pos.y,
        engine.message_log,
    )
    engine.ground_pickup_modal.reset()