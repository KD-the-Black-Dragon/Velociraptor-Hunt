"""Minimal encode helpers used by debug (full run codec in reference/kdvr)."""

from __future__ import annotations

import random
from typing import Any


def encode_rng_state(rng: random.Random) -> dict[str, Any]:
    return {"version": 1, "state": list(rng.getstate()[1])}
