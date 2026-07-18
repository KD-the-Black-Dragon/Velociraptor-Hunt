"""Headless 1v1 arena batch runner (honors enabled mods).

Usage:
    python tools/sim_arena.py --difficulty normal
    python tools/sim_arena.py --seed 4242 --output arena_compare.csv
    python tools/sim_arena.py --label after_tweak --output arena_compare.csv
    python tools/sim_arena.py --overwrite --output arena_compare.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.data.depth_scaling_config import validate_difficulty_id  # noqa: E402
from src.mods.reload import reload_all_game_data  # noqa: E402
from src.sim.arena_batch import (  # noqa: E402
    run_arena_batch,
    should_append_arena_compare_sheet,
    write_arena_csv,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run 1v1 arena trials for every Evil entity (mods honored).",
    )
    parser.add_argument(
        "--difficulty",
        default="normal",
        help="Difficulty id: easier, normal, hard, nightmare (default: normal)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="RNG root seed (default: random); stored in meta.seed row",
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=10,
        help="Trials per entity (default: 10)",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=1000,
        help="Turn cap per trial (default: 1000)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("arena_compare.csv"),
        help="Compare-sheet CSV path (default: arena_compare.csv)",
    )
    parser.add_argument(
        "--label",
        default=None,
        help="Column header for this run (default: auto timestamp label)",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append when the output file exists (default behavior; flag kept for scripts)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace the output file instead of appending a new column",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    difficulty_id = validate_difficulty_id(args.difficulty)
    reload_all_game_data(report=False)

    result = run_arena_batch(
        difficulty_id=difficulty_id,
        seed=args.seed,
        trials_per_entity=max(1, int(args.trials)),
        max_turns=max(1, int(args.max_turns)),
    )
    try:
        column_label = write_arena_csv(
            args.output,
            result,
            column_label=args.label,
            append=args.append,
            overwrite=args.overwrite,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    appended = should_append_arena_compare_sheet(
        args.output,
        append=args.append,
        overwrite=args.overwrite,
    )
    action = "Appended to" if appended else "Wrote"
    print(f"seed: {result.seed}")
    print(
        f"{action} {args.output} "
        f"(column {column_label!r}, {len(result.reports)} entities, "
        f"{result.trials_per_entity} trials each)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())