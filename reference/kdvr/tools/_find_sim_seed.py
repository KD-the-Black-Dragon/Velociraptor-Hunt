"""One-off seed calibration for sim smoke tests (not shipped CLI)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.sim.data_loader import install_stock_game_data
from src.sim.runner import SimTrajectoryRun

install_stock_game_data()
for seed in range(1, 11):
    r = SimTrajectoryRun(
        difficulty_id="normal",
        seed=seed,
        max_turns=3_500,
        floors_max=20,
    ).run()
    print(
        seed,
        r.depth_reached,
        r.runes_collected,
        r.termination.name,
        r.turns_played,
        r.hp_at_end,
        flush=True,
    )