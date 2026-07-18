"""Headless trajectory run loop."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from src.components import Engulfed, Fighter, Stunned
from src.engine import GameEngine
from src.sim.floor_entry import start_isolation_floor
from src.sim.modals import ModalStepResult, advance_modals, execute_engulfed_struggle
from src.sim.policy import execute_policy_turn
from src.sim.snapshots import FloorOutcomeSnapshot, FloorTrackingState, LoadoutProfile


class SimTerminationReason(Enum):
    DIGESTED = auto()
    DEPTH_CAP = auto()
    TURN_CAP = auto()
    TIME_BUDGET = auto()


@dataclass
class SimTrajectoryRunResult:
    seed: int
    difficulty_id: str
    termination: SimTerminationReason | None
    depth_reached: int
    runes_collected: int
    monsters_defeated: int
    turns_played: int
    hp_at_end: int
    floor_snapshots: list[FloorOutcomeSnapshot] = field(default_factory=list)


def execute_wait_turn(engine: GameEngine) -> None:
    """Pass one player turn (PR1 policy stub; replaced by SimPolicy in PR2+)."""
    if engine.player is None:
        return
    engine._consume_player_turn()


def _drain_rest_and_projectiles(engine: GameEngine) -> None:
    while engine.rest_in_progress():
        engine.advance_rest_animation()
    while engine.projectile_in_progress():
        engine.advance_projectile_animation()


def _run_one_turn(engine: GameEngine, *, tracking: FloorTrackingState) -> ModalStepResult:
    _drain_rest_and_projectiles(engine)

    modal_result = advance_modals(engine)
    if modal_result is ModalStepResult.RUN_ENDED:
        return modal_result

    if engine.player is not None and Engulfed in engine.player.tags:
        if Stunned not in engine.player.tags:
            execute_engulfed_struggle(engine)
        else:
            execute_wait_turn(engine)
        return ModalStepResult.CONTINUE

    execute_policy_turn(engine, tracking=tracking)
    return ModalStepResult.CONTINUE


def _ending_kind(engine: GameEngine) -> str | None:
    ending = engine.game_over.ending
    if ending is None:
        return None
    return ending.kind


class SimTrajectoryRun:
    """Play one full trajectory run from floor 1."""

    def __init__(
        self,
        *,
        difficulty_id: str,
        seed: int,
        max_turns: int = 50_000,
        floors_max: int = 20,
        log_session_milestones: bool = False,
    ) -> None:
        self.difficulty_id = difficulty_id
        self.seed = seed
        self.max_turns = max_turns
        self.floors_max = floors_max
        self.log_session_milestones = log_session_milestones

    def run(self, *, deadline: float | None = None) -> SimTrajectoryRunResult:
        engine = GameEngine(
            difficulty_id=self.difficulty_id,
            save_coordinator=None,
            skip_new_game=True,
        )
        engine.new_game(
            seed=self.seed,
            log_session_milestones=self.log_session_milestones,
        )

        tracking = FloorTrackingState()
        tracking.begin_floor(
            floor=engine.floor_depth,
            seed=self.seed,
            runes_collected=engine.run_stats.runes_collected,
            player=engine.player,
        )

        snapshots: list[FloorOutcomeSnapshot] = []
        termination: SimTerminationReason | None = None
        previous_depth = engine.floor_depth

        for _ in range(self.max_turns):
            if deadline is not None and time.perf_counter() >= deadline:
                termination = SimTerminationReason.TIME_BUDGET
                snapshot = tracking.finish_visit(
                    digested=False,
                    descended=False,
                    runes_collected=engine.run_stats.runes_collected,
                    rune_quota=engine.runes_per_floor(),
                    player=engine.player,
                )
                if snapshot is not None:
                    snapshots.append(snapshot)
                break

            if engine.floor_depth > self.floors_max:
                termination = SimTerminationReason.DEPTH_CAP
                break

            step = _run_one_turn(engine, tracking=tracking)
            if step is ModalStepResult.RUN_ENDED:
                snapshot = tracking.finish_visit(
                    digested=_ending_kind(engine) == "digested",
                    descended=False,
                    runes_collected=engine.run_stats.runes_collected,
                    rune_quota=engine.runes_per_floor(),
                    player=engine.player,
                )
                if snapshot is not None:
                    snapshots.append(snapshot)
                termination = SimTerminationReason.DIGESTED
                break

            if engine.floor_depth != previous_depth:
                snapshot = tracking.finish_visit(
                    digested=False,
                    descended=True,
                    runes_collected=engine.run_stats.runes_collected,
                    rune_quota=engine.runes_per_floor(),
                    player=engine.player,
                )
                if snapshot is not None:
                    snapshots.append(snapshot)
                if engine.floor_depth <= self.floors_max:
                    tracking.begin_floor(
                        floor=engine.floor_depth,
                        seed=self.seed,
                        runes_collected=engine.run_stats.runes_collected,
                        player=engine.player,
                    )
                previous_depth = engine.floor_depth

            if engine.floor_depth > self.floors_max:
                termination = SimTerminationReason.DEPTH_CAP
                break
        else:
            termination = SimTerminationReason.TURN_CAP
            snapshot = tracking.finish_visit(
                digested=False,
                descended=False,
                runes_collected=engine.run_stats.runes_collected,
                rune_quota=engine.runes_per_floor(),
                player=engine.player,
            )
            if snapshot is not None:
                snapshots.append(snapshot)

        hp_at_end = 0
        if engine.player is not None:
            fighter = engine.player.components.get(Fighter)
            if fighter is not None:
                hp_at_end = fighter.hp

        return SimTrajectoryRunResult(
            seed=self.seed,
            difficulty_id=self.difficulty_id,
            termination=termination,
            depth_reached=engine.floor_depth,
            runes_collected=engine.run_stats.runes_collected,
            monsters_defeated=engine.run_stats.monsters_defeated,
            turns_played=engine.player_turn_count,
            hp_at_end=hp_at_end,
            floor_snapshots=snapshots,
        )


@dataclass
class SimIsolationRunResult:
    floor: int
    seed: int
    snapshot: FloorOutcomeSnapshot | None
    termination: SimTerminationReason | None
    turns_played: int


class SimIsolationRun:
    """Play one isolation floor with injected loadout."""

    def __init__(
        self,
        *,
        difficulty_id: str,
        floor: int,
        seed: int,
        loadout: LoadoutProfile,
        max_turns: int = 50_000,
    ) -> None:
        self.difficulty_id = difficulty_id
        self.floor = floor
        self.seed = seed
        self.loadout = loadout
        self.max_turns = max_turns

    def run(self, *, deadline: float | None = None) -> SimIsolationRunResult:
        engine = GameEngine(
            difficulty_id=self.difficulty_id,
            save_coordinator=None,
            skip_new_game=True,
        )
        start_isolation_floor(
            engine,
            depth=self.floor,
            seed=self.seed,
            loadout=self.loadout,
        )

        tracking = FloorTrackingState()
        tracking.begin_floor(
            floor=engine.floor_depth,
            seed=self.seed,
            runes_collected=engine.run_stats.runes_collected,
            player=engine.player,
        )

        termination: SimTerminationReason | None = None
        snapshot: FloorOutcomeSnapshot | None = None
        start_depth = engine.floor_depth

        for _ in range(self.max_turns):
            if deadline is not None and time.perf_counter() >= deadline:
                termination = SimTerminationReason.TIME_BUDGET
                snapshot = tracking.finish_visit(
                    digested=False,
                    descended=False,
                    runes_collected=engine.run_stats.runes_collected,
                    rune_quota=engine.runes_per_floor(),
                    player=engine.player,
                )
                break

            step = _run_one_turn(engine, tracking=tracking)
            if step is ModalStepResult.RUN_ENDED:
                snapshot = tracking.finish_visit(
                    digested=_ending_kind(engine) == "digested",
                    descended=False,
                    runes_collected=engine.run_stats.runes_collected,
                    rune_quota=engine.runes_per_floor(),
                    player=engine.player,
                )
                termination = SimTerminationReason.DIGESTED
                break

            if engine.floor_depth != start_depth:
                snapshot = tracking.finish_visit(
                    digested=False,
                    descended=True,
                    runes_collected=engine.run_stats.runes_collected,
                    rune_quota=engine.runes_per_floor(),
                    player=engine.player,
                )
                termination = SimTerminationReason.DEPTH_CAP
                break
        else:
            termination = SimTerminationReason.TURN_CAP
            snapshot = tracking.finish_visit(
                digested=False,
                descended=False,
                runes_collected=engine.run_stats.runes_collected,
                rune_quota=engine.runes_per_floor(),
                player=engine.player,
            )

        return SimIsolationRunResult(
            floor=self.floor,
            seed=self.seed,
            snapshot=snapshot,
            termination=termination,
            turns_played=engine.player_turn_count,
        )