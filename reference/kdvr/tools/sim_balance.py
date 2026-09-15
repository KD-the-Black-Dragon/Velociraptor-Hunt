"""Balance difficulty analyzer CLI (headless trajectory + isolation sim).

Usage:
    python tools/sim_balance.py --difficulty normal --seconds 300
    python tools/sim_balance.py --label baseline --output balance_compare.csv
    python tools/sim_balance.py --label after_wolf_buff --append --output balance_compare.csv
    python tools/sim_balance.py --curve-output balance_curve.csv --seconds 60
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.data.depth_scaling_config import validate_difficulty_id  # noqa: E402
from src.sim.data_loader import install_stock_game_data  # noqa: E402
from src.sim.stats import (  # noqa: E402
    FLOORS_MAX_DEFAULT,
    run_balance_analysis,
    write_balance_report,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run balance difficulty analysis (stock data/ only).",
    )
    parser.add_argument(
        "--difficulty",
        default="normal",
        help="Difficulty id: easier, normal, hard, nightmare (default: normal)",
    )
    parser.add_argument(
        "--seconds",
        type=float,
        default=300.0,
        help="Total wall-clock budget in seconds (default: 300)",
    )
    parser.add_argument(
        "--trajectory-fraction",
        type=float,
        default=0.7,
        help="Fraction of --seconds for trajectory pass (default: 0.7)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("balance_compare.csv"),
        help="CSV output path (default: balance_compare.csv)",
    )
    parser.add_argument(
        "--format",
        choices=("compare", "wide"),
        default="compare",
        help="compare = side-by-side columns (default); wide = floor curve table",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append this run as a new column to an existing compare sheet",
    )
    parser.add_argument(
        "--label",
        default=None,
        help="Column header for this run (default: auto timestamp label)",
    )
    parser.add_argument(
        "--curve-output",
        type=Path,
        default=None,
        help="Also write wide floor-curve CSV (only with --format compare)",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=50_000,
        help="Safety turn cap per trajectory run (default: 50000)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="RNG root seed (default: random)",
    )
    parser.add_argument(
        "--floors-max",
        type=int,
        default=FLOORS_MAX_DEFAULT,
        help=f"Maximum floor depth to analyze (default: {FLOORS_MAX_DEFAULT})",
    )
    parser.add_argument(
        "--trajectory-only",
        action="store_true",
        help="Skip isolation pass (trajectory-only analysis)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    difficulty_id = validate_difficulty_id(args.difficulty)
    if not 0.0 < args.trajectory_fraction <= 1.0:
        print("error: --trajectory-fraction must be in (0, 1]", file=sys.stderr)
        return 2
    if args.seconds <= 0:
        print("error: --seconds must be positive", file=sys.stderr)
        return 2
    if args.append and args.format != "compare":
        print("error: --append requires --format compare", file=sys.stderr)
        return 2
    if args.curve_output is not None and args.format != "compare":
        print("error: --curve-output requires --format compare", file=sys.stderr)
        return 2

    fingerprint = install_stock_game_data()
    seed = args.seed if args.seed is not None else random.randint(0, 2_147_483_647)

    trajectory_fraction = 1.0 if args.trajectory_only else args.trajectory_fraction
    rows, metadata = run_balance_analysis(
        difficulty_id=difficulty_id,
        seconds_budget=args.seconds,
        trajectory_fraction=trajectory_fraction,
        seed=seed,
        max_turns=args.max_turns,
        floors_max=args.floors_max,
        data_fingerprint=fingerprint,
        run_isolation=not args.trajectory_only,
    )
    try:
        column_label = write_balance_report(
            args.output,
            rows=rows,
            metadata=metadata,
            column_label=args.label,
            floors_max=args.floors_max,
            append=args.append,
            output_format=args.format,
            curve_output=args.curve_output,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    iso_summary = ""
    if metadata.isolation_runs_total > 0:
        iso_summary = (
            f", {metadata.isolation_runs_total} isolation runs, "
            f"{metadata.isolation_seconds:.1f}s isolation"
        )
    print(
        f"Wrote {args.output} "
        f"(column {column_label!r}, "
        f"{metadata.trajectory_runs} trajectory runs, "
        f"{metadata.trajectory_seconds:.1f}s trajectory"
        f"{iso_summary})"
    )
    if args.curve_output is not None:
        print(f"Wrote curve {args.curve_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())