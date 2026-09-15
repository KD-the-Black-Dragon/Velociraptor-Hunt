"""Overnight seed calibration for balance sim (dev helper).

Scans placement viability and trajectory outcomes; appends rows incrementally
so partial results survive interruption.

Usage:
    python -u tools/seed_scan_overnight.py

Outputs:
    balance_seed_scan.csv      — all run rows
    balance_seed_scan.log      — progress log
    balance_seed_scan_summary.txt — written on completion
"""

from __future__ import annotations

import csv
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.components import FloorRune, Position
from src.engine import GameEngine
from src.sim.data_loader import install_stock_game_data
from src.sim.runner import SimTrajectoryRun

CSV_PATH = _ROOT / "balance_seed_scan.csv"
LOG_PATH = _ROOT / "balance_seed_scan.log"
SUMMARY_PATH = _ROOT / "balance_seed_scan_summary.txt"

FIELDNAMES = (
    "phase",
    "seed",
    "difficulty",
    "max_turns",
    "runes_on_map",
    "quota",
    "depth_reached",
    "runes_collected",
    "monsters_defeated",
    "termination",
    "turns_played",
    "hp_at_end",
    "elapsed_s",
)


def _log(msg: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat()} {msg}"
    print(line, flush=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def _append_row(row: dict[str, object]) -> None:
    write_header = not CSV_PATH.is_file()
    with CSV_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in FIELDNAMES})
        handle.flush()


@dataclass(frozen=True)
class Placement:
    seed: int
    runes_on_map: int
    quota: int


def count_map_runes(seed: int) -> Placement:
    engine = GameEngine(save_coordinator=None, skip_new_game=True)
    engine.new_game(seed=seed, log_session_milestones=False)
    runes_on_map = len(list(engine.world.Q.all_of(components=[FloorRune, Position])))
    quota = engine.runes_per_floor()
    return Placement(seed=seed, runes_on_map=runes_on_map, quota=quota)


def run_trajectory(
    *,
    phase: str,
    seed: int,
    difficulty_id: str,
    max_turns: int,
    placement: Placement | None = None,
) -> None:
    started = time.perf_counter()
    result = SimTrajectoryRun(
        difficulty_id=difficulty_id,
        seed=seed,
        max_turns=max_turns,
        floors_max=20,
    ).run()
    elapsed = time.perf_counter() - started
    row = {
        "phase": phase,
        "seed": seed,
        "difficulty": difficulty_id,
        "max_turns": max_turns,
        "runes_on_map": placement.runes_on_map if placement else "",
        "quota": placement.quota if placement else "",
        "depth_reached": result.depth_reached,
        "runes_collected": result.runes_collected,
        "monsters_defeated": result.monsters_defeated,
        "termination": result.termination.name if result.termination else "",
        "turns_played": result.turns_played,
        "hp_at_end": result.hp_at_end,
        "elapsed_s": round(elapsed, 1),
    }
    _append_row(row)
    _log(
        f"{phase} seed={seed} {difficulty_id} turns={max_turns} "
        f"map={placement.runes_on_map if placement else '?'} "
        f"depth={result.depth_reached} runes={result.runes_collected} "
        f"end={row['termination']} hp={result.hp_at_end} ({elapsed:.0f}s)"
    )


def _load_csv_rows() -> list[dict[str, str]]:
    if not CSV_PATH.is_file():
        return []
    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_summary(started_at: float) -> None:
    rows = _load_csv_rows()
    total_elapsed = time.perf_counter() - started_at

    placement_rows = [r for r in rows if r["phase"] == "placement"]
    zero_rune_seeds = sorted(
        int(r["seed"]) for r in placement_rows if int(r["runes_on_map"]) == 0
    )
    sim_rows = [r for r in rows if r["phase"] != "placement"]

    def _best(filter_fn, key):
        candidates = [r for r in sim_rows if filter_fn(r)]
        if not candidates:
            return None
        return max(candidates, key=lambda r: (int(r[key]), int(r["depth_reached"])))

    best_normal_runes = _best(
        lambda r: r["difficulty"] == "normal" and r["phase"] == "sim_normal",
        "runes_collected",
    )
    best_normal_depth = _best(
        lambda r: r["difficulty"] == "normal" and int(r["depth_reached"]) >= 2,
        "depth_reached",
    )
    best_easy_depth = _best(
        lambda r: r["difficulty"] == "easier" and int(r["depth_reached"]) >= 2,
        "depth_reached",
    )

    lines = [
        "Balance sim seed scan summary",
        f"Completed UTC: {datetime.now(timezone.utc).isoformat()}",
        f"Total wall time: {total_elapsed / 3600:.2f} h",
        f"CSV rows: {len(rows)} ({CSV_PATH.name})",
        "",
        f"Placement checks: {len(placement_rows)}",
        f"Seeds with 0 runes on map: {len(zero_rune_seeds)}",
        f"  examples: {zero_rune_seeds[:20]}",
        "",
        "Best normal sim (runes collected):",
        str(best_normal_runes),
        "Best normal sim (depth >= 2):",
        str(best_normal_depth),
        "Best easier sim (depth >= 2):",
        str(best_easy_depth),
        "",
        "Rows with runes_collected >= 1 (normal, phase sim_normal):",
    ]
    for r in sorted(
        (
            r
            for r in sim_rows
            if r["phase"] == "sim_normal" and int(r["runes_collected"]) >= 1
        ),
        key=lambda r: (-int(r["runes_collected"]), -int(r["depth_reached"])),
    )[:30]:
        lines.append(
            f"  seed={r['seed']} runes={r['runes_collected']} depth={r['depth_reached']} "
            f"hp={r['hp_at_end']} end={r['termination']}"
        )

    lines.extend(
        [
            "",
            "Rows with depth >= 2:",
        ]
    )
    for r in sorted(
        (r for r in sim_rows if int(r["depth_reached"]) >= 2),
        key=lambda r: (-int(r["depth_reached"]), -int(r["runes_collected"])),
    )[:30]:
        lines.append(
            f"  seed={r['seed']} {r['difficulty']} depth={r['depth_reached']} "
            f"runes={r['runes_collected']} hp={r['hp_at_end']} phase={r['phase']}"
        )

    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _log(f"Wrote summary to {SUMMARY_PATH.name}")


def main() -> None:
    started_at = time.perf_counter()
    _log("=== seed scan start ===")
    fingerprint = install_stock_game_data()
    _log(f"data_fingerprint={fingerprint}")

    # Phase 1: placement viability (seeds 1-100; ~2-4h)
    placements: dict[int, Placement] = {}
    for seed in range(1, 101):
        t0 = time.perf_counter()
        placement = count_map_runes(seed)
        placements[seed] = placement
        elapsed = time.perf_counter() - t0
        _append_row(
            {
                "phase": "placement",
                "seed": seed,
                "difficulty": "",
                "max_turns": 0,
                "runes_on_map": placement.runes_on_map,
                "quota": placement.quota,
                "depth_reached": "",
                "runes_collected": "",
                "monsters_defeated": "",
                "termination": "",
                "turns_played": "",
                "hp_at_end": "",
                "elapsed_s": round(elapsed, 1),
            }
        )
        _log(
            f"placement seed={seed} runes_on_map={placement.runes_on_map} "
            f"quota={placement.quota} ({elapsed:.0f}s)"
        )

    viable = [p for p in placements.values() if p.runes_on_map >= p.quota]
    _log(f"viable placements (runes_on_map >= quota): {len(viable)} / {len(placements)}")

    # Phase 2: normal trajectory on viable seeds (5000 turns)
    for placement in viable:
        if placement.seed > 100:
            continue
        run_trajectory(
            phase="sim_normal",
            seed=placement.seed,
            difficulty_id="normal",
            max_turns=5_000,
            placement=placement,
        )

    # Phase 3: easier trajectory on viable seeds 1-60 (8000 turns)
    for placement in viable:
        if placement.seed > 60:
            continue
        run_trajectory(
            phase="sim_easier",
            seed=placement.seed,
            difficulty_id="easier",
            max_turns=8_000,
            placement=placement,
        )

    # Phase 4: deep follow-up on promising seeds from CSV
    rows = _load_csv_rows()
    promising: set[int] = set()
    for row in rows:
        if row["phase"] in (
            "sim_normal",
            "sim_easier",
            "sim_easy",  # legacy phase name
            "sim_deep_normal",
            "sim_deep_easier",
            "sim_deep_easy",  # legacy phase name
        ):
            if int(row.get("runes_collected") or 0) >= 1:
                promising.add(int(row["seed"]))
            if int(row.get("depth_reached") or 0) >= 2:
                promising.add(int(row["seed"]))

    for seed in sorted(promising):
        placement = placements.get(seed)
        if placement is None or placement.runes_on_map < placement.quota:
            continue
        run_trajectory(
            phase="sim_deep_normal",
            seed=seed,
            difficulty_id="normal",
            max_turns=12_000,
            placement=placement,
        )
        run_trajectory(
            phase="sim_deep_easier",
            seed=seed,
            difficulty_id="easier",
            max_turns=12_000,
            placement=placement,
        )

    _write_summary(started_at)
    _log("=== seed scan complete ===")


if __name__ == "__main__":
    main()