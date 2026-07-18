"""Single-seed sim smoke (dev helper)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.sim.data_loader import install_stock_game_data
from src.sim.runner import SimTrajectoryRun

install_stock_game_data()
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7
turns = int(sys.argv[2]) if len(sys.argv) > 2 else 2500
r = SimTrajectoryRun(
    difficulty_id="normal",
    seed=seed,
    max_turns=turns,
    floors_max=20,
).run()
print(
    "seed", seed,
    "depth", r.depth_reached,
    "runes", r.runes_collected,
    "end", r.termination.name,
    "turns", r.turns_played,
    "hp", r.hp_at_end,
    flush=True,
)