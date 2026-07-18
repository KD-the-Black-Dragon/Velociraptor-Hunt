"""Threat assessment for sim policy (PR3): bail and lethal-risk."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.components import Engulfed, Fighter, Stunned
from src.sim.inventory_policy import has_potion_effect, policy_lethal_consumables_available
from src.sim.perception import adjacent_evil_entities, visible_evil_entities

if TYPE_CHECKING:
    from src.engine import GameEngine
    from src.sim.snapshots import FloorVisitTracker

REST_SKIP_FRACTION = 0.10
REST_OPTIONAL_HP_FRACTION = 0.70


def player_hp_fraction(engine: GameEngine) -> float:
    player = engine.player
    if player is None:
        return 1.0
    fighter = player.components.get(Fighter)
    if fighter is None or fighter.max_hp <= 0:
        return 1.0
    return fighter.hp / fighter.max_hp


def update_bail_for_survival(engine: GameEngine, visit: FloorVisitTracker | None) -> None:
    """Latch ``bail_for_survival`` when any really-bad condition holds."""
    if visit is None or visit.bail_for_survival:
        return
    player = engine.player
    if player is None:
        return

    visible_count = len(visible_evil_entities(engine))
    adjacent_count = len(adjacent_evil_entities(engine))
    hp_frac = player_hp_fraction(engine)

    if (
        hp_frac < 0.25
        and not has_potion_effect(player, "heal")
        and visible_count >= 1
    ):
        visit.bail_for_survival = True
        return

    if visible_count >= 3:
        visit.bail_for_survival = True
        return

    if adjacent_count >= 2 and not policy_lethal_consumables_available(player):
        visit.bail_for_survival = True


def lethal_risk_active(engine: GameEngine) -> bool:
    player = engine.player
    if player is None:
        return False
    visible_count = len(visible_evil_entities(engine))
    adjacent_count = len(adjacent_evil_entities(engine))
    hp_frac = player_hp_fraction(engine)
    if visible_count >= 2:
        return True
    if adjacent_count >= 1 and hp_frac < 0.5:
        return True
    return hp_frac < 0.35 and visible_count >= 1


def should_attempt_rest(engine: GameEngine) -> bool:
    """Hurt and rest pre-checks would pass (not stunned/engulfed, no visible evil)."""
    player = engine.player
    if player is None:
        return False
    if Stunned in player.tags or Engulfed in player.tags:
        return False
    fighter = player.components.get(Fighter)
    if fighter is None or fighter.hp >= fighter.max_hp:
        return False
    if engine.rest_in_progress():
        return False
    from src.systems.fov import player_has_visible_evil

    return not player_has_visible_evil(engine.game_map, engine.world)


def rest_imperfection_skips(engine: GameEngine) -> bool:
    """~10% skip optional rest when HP ≥ 70% max."""
    if player_hp_fraction(engine) < REST_OPTIONAL_HP_FRACTION:
        return False
    return engine.rng.random() < REST_SKIP_FRACTION