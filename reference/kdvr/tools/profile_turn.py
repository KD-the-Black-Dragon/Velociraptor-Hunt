"""Headless player-turn profiler for performance investigation.

Usage:
    python tools/profile_turn.py
    python tools/profile_turn.py --scenario default --profile
    python tools/profile_turn.py --all --iterations 100
"""

from __future__ import annotations

import argparse
import cProfile
import pstats
import random
import statistics
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from io import StringIO
from pathlib import Path

# Allow running as `python tools/profile_turn.py` from repo root.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.components import AI, AIState, Player, Position  # noqa: E402
from src.engine import GameEngine  # noqa: E402
from src.spawn import spawn_entity_by_id  # noqa: E402
from src.systems.ai import run_monster_turns  # noqa: E402
from tests.map_test_helpers import (  # noqa: E402
    ARENA_X,
    ARENA_Y,
    carve_floor_rect,
    carve_floor_tile,
    clear_wolf_abilities,
    isolate_other_ais,
    relocate_player,
)


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    npc_count: int
    iterations: int
    mean_ms: float
    median_ms: float
    p95_ms: float
    min_ms: float
    max_ms: float


@dataclass(frozen=True)
class ProfileEntry:
    function: str
    cumtime: float
    cumtime_pct: float
    ncalls: int


def _count_npcs(engine: GameEngine) -> int:
    player = engine.player
    return sum(
        1
        for entity in engine.world.Q.all_of(components=[AI, Position])
        if entity is not player
    )


def _make_engine(*, seed: int) -> GameEngine:
    engine = GameEngine(save_coordinator=None)
    engine.rng = random.Random(seed)
    return engine


def _remove_all_npcs(engine: GameEngine) -> None:
    player = engine.player
    for entity in list(engine.world.Q.all_of(components=[AI, Position])):
        if entity is player:
            continue
        entity.clear()


def _clear_ai_memory(engine: GameEngine) -> None:
    for entity in engine.world.Q.all_of(components=[AI]):
        if Player in entity.tags:
            continue
        state = entity.components.get(AIState)
        if state is None:
            state = AIState()
            entity.components[AIState] = state
        state.last_known_primary = None
        state.last_known_neutral = None
        state.last_known_evil = None
        state.last_known_player = None
        state.explore_goal = None
        state.chase_momentum_direction = None
        state.chase_momentum_turns_left = 0
        state.door_spite_turns_left = 0


def _spawn_wolves_grid(engine: GameEngine, count: int, *, start_x: int, start_y: int) -> None:
    x, y = start_x, start_y
    spawned = 0
    while spawned < count:
        carve_floor_tile(engine, x, y)
        spawn_entity_by_id(engine.world, "wolf", x, y)
        spawned += 1
        x += 2
        if x > engine.game_map.width - 3:
            x = start_x
            y += 2
            if y > engine.game_map.height - 3:
                break


def _setup_default(engine: GameEngine) -> None:
    pass


def _setup_sparse(engine: GameEngine) -> None:
    isolate_other_ais(engine)


def _setup_isolated_1(engine: GameEngine) -> None:
    wolves = [
        entity
        for entity in engine.world.Q.all_of(components=[AI, Position])
        if entity is not engine.player
    ]
    if not wolves:
        carve_floor_tile(engine, ARENA_X, ARENA_Y)
        spawn_entity_by_id(engine.world, "wolf", ARENA_X, ARENA_Y)
        wolves = [
            entity
            for entity in engine.world.Q.all_of(components=[AI, Position])
            if entity is not engine.player
        ]
    keep = wolves[0]
    isolate_other_ais(engine, keep=(keep,))
    for entity in list(engine.world.Q.all_of(components=[AI, Position])):
        if entity is engine.player or entity is keep:
            continue
        entity.clear()


def _setup_scale(engine: GameEngine, count: int) -> None:
    _remove_all_npcs(engine)
    carve_floor_rect(engine, 5, 5, engine.game_map.width - 6, engine.game_map.height - 6)
    relocate_player(engine, 10, 10)
    _spawn_wolves_grid(engine, count, start_x=20, start_y=12)
    clear_wolf_abilities(engine)
    _clear_ai_memory(engine)


def _setup_explore_heavy(engine: GameEngine, count: int) -> None:
    _remove_all_npcs(engine)
    carve_floor_rect(engine, 5, 5, engine.game_map.width - 6, engine.game_map.height - 6)
    relocate_player(engine, 10, 10)
    _spawn_wolves_grid(engine, count, start_x=50, start_y=30)
    clear_wolf_abilities(engine)
    _clear_ai_memory(engine)


def _time_turns(
    engine: GameEngine,
    action: Callable[[GameEngine], None],
    *,
    warmup: int,
    iterations: int,
) -> list[float]:
    for _ in range(warmup):
        action(engine)
    samples_ms: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        action(engine)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        samples_ms.append(elapsed_ms)
    return samples_ms


def _summarize(name: str, npc_count: int, samples_ms: list[float]) -> ScenarioResult:
    ordered = sorted(samples_ms)
    p95_index = max(0, int(len(ordered) * 0.95) - 1)
    return ScenarioResult(
        name=name,
        npc_count=npc_count,
        iterations=len(samples_ms),
        mean_ms=statistics.mean(samples_ms),
        median_ms=statistics.median(samples_ms),
        p95_ms=ordered[p95_index],
        min_ms=min(samples_ms),
        max_ms=max(samples_ms),
    )


def _profile_action(
    engine: GameEngine,
    action: Callable[[GameEngine], None],
    *,
    iterations: int,
    top_n: int = 25,
) -> list[ProfileEntry]:
    profiler = cProfile.Profile()
    profiler.enable()
    for _ in range(iterations):
        action(engine)
    profiler.disable()

    stream = StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.strip_dirs()
    stats.sort_stats("cumulative")
    stats.print_stats(top_n)
    total = stats.total_tt

    entries: list[ProfileEntry] = []
    for func, (cc, nc, tt, ct, callers) in stats.stats.items():
        filename, line, name = func
        label = f"{Path(filename).name}:{line}({name})"
        entries.append(
            ProfileEntry(
                function=label,
                cumtime=ct,
                cumtime_pct=(ct / total * 100.0) if total else 0.0,
                ncalls=nc,
            )
        )
    entries.sort(key=lambda entry: entry.cumtime, reverse=True)
    return entries[:top_n]


def _consume_player_turn(engine: GameEngine) -> None:
    engine._consume_player_turn()


def _run_world_turn(engine: GameEngine) -> None:
    engine._run_world_turn()


def _run_monster_turns_only(engine: GameEngine) -> None:
    player = engine.player
    assert player is not None
    run_monster_turns(
        engine.world,
        engine.game_map,
        player,
        engine.message_log,
        rng=engine.rng,
        modal=engine.vore_modal,
        vore_prefs=engine.vore_content_prefs,
        skipped=engine.skipped_this_phase,
        player_turn_count=engine.player_turn_count,
    )


SCENARIOS: dict[str, Callable[[GameEngine], None]] = {
    "default": _setup_default,
    "sparse": _setup_sparse,
    "isolated_1": _setup_isolated_1,
    "scale_10": lambda e: _setup_scale(e, 10),
    "scale_25": lambda e: _setup_scale(e, 25),
    "scale_50": lambda e: _setup_scale(e, 50),
    "explore_10": lambda e: _setup_explore_heavy(e, 10),
    "explore_25": lambda e: _setup_explore_heavy(e, 25),
    "explore_50": lambda e: _setup_explore_heavy(e, 50),
}


def run_scenario(
    name: str,
    *,
    seed: int,
    warmup: int,
    iterations: int,
    action: str,
    profile: bool,
) -> tuple[ScenarioResult, list[ProfileEntry] | None]:
    engine = _make_engine(seed=seed)
    SCENARIOS[name](engine)
    npc_count = _count_npcs(engine)

    action_fn = {
        "consume": _consume_player_turn,
        "world": _run_world_turn,
        "monsters": _run_monster_turns_only,
    }[action]

    samples = _time_turns(engine, action_fn, warmup=warmup, iterations=iterations)
    result = _summarize(name, npc_count, samples)
    entries = _profile_action(engine, action_fn, iterations=iterations) if profile else None
    return result, entries


def _print_result(result: ScenarioResult, action: str) -> None:
    print(
        f"{result.name:12}  npcs={result.npc_count:3}  "
        f"action={action:8}  "
        f"mean={result.mean_ms:7.2f}ms  "
        f"median={result.median_ms:7.2f}ms  "
        f"p95={result.p95_ms:7.2f}ms  "
        f"max={result.max_ms:7.2f}ms"
    )


def _print_profile(entries: list[ProfileEntry]) -> None:
    print("  Top functions (cumulative):")
    for entry in entries:
        print(
            f"    {entry.cumtime_pct:5.1f}%  {entry.cumtime:8.4f}s  "
            f"ncalls={entry.ncalls:6}  {entry.function}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile player-turn hot path")
    parser.add_argument(
        "--scenario",
        choices=list(SCENARIOS.keys()),
        default=None,
        help="Run one scenario (default: all)",
    )
    parser.add_argument("--all", action="store_true", help="Run all scenarios")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--iterations", type=int, default=80)
    parser.add_argument(
        "--action",
        choices=["consume", "world", "monsters"],
        default="consume",
        help="What to time per iteration",
    )
    parser.add_argument("--profile", action="store_true", help="Print cProfile top functions")
    args = parser.parse_args()

    names = list(SCENARIOS.keys()) if args.all or args.scenario is None else [args.scenario]

    print(f"Profiling action={args.action}  seed={args.seed}  iterations={args.iterations}")
    print("-" * 90)

    all_results: list[ScenarioResult] = []
    profile_for = args.scenario or "default"

    for name in names:
        result, entries = run_scenario(
            name,
            seed=args.seed,
            warmup=args.warmup,
            iterations=args.iterations,
            action=args.action,
            profile=args.profile and name == profile_for,
        )
        all_results.append(result)
        _print_result(result, args.action)
        if entries is not None:
            _print_profile(entries)
            print()


if __name__ == "__main__":
    main()