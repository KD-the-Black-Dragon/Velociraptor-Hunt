"""Headless turn-time checks (manual / optional — not a parallel CI gate).

Designer policy (engineering-cleanup): real lag is noticed in playtest; p95
thresholds flake under ``pytest -n 6`` due to CPU contention. Keep
``tools/profile_turn.py`` for intentional profiling.
"""

from __future__ import annotations

import pytest

from tools.profile_turn import run_scenario

# Historical budgets (for manual comparison only).
DEFAULT_P95_MS_LIMIT = 150.0
EXPLORE_10_P95_MS_LIMIT = 100.0

_PROFILE_SEED = 42
_PROFILE_WARMUP = 5
_PROFILE_ITERATIONS = 20

pytestmark = pytest.mark.skip(
    reason="Perf p95 is not a CI gate; use tools/profile_turn.py manually "
    "(flakes under parallel pytest load)."
)


def test_default_turn_p95_within_budget() -> None:
    result, _ = run_scenario(
        "default",
        seed=_PROFILE_SEED,
        warmup=_PROFILE_WARMUP,
        iterations=_PROFILE_ITERATIONS,
        action="consume",
        profile=False,
    )
    assert result.p95_ms < DEFAULT_P95_MS_LIMIT, (
        f"default p95 {result.p95_ms:.1f}ms exceeds {DEFAULT_P95_MS_LIMIT}ms "
        f"(mean={result.mean_ms:.1f}ms)"
    )


def test_explore_10_turn_p95_within_budget() -> None:
    result, _ = run_scenario(
        "explore_10",
        seed=_PROFILE_SEED,
        warmup=_PROFILE_WARMUP,
        iterations=10,
        action="consume",
        profile=False,
    )
    assert result.p95_ms < EXPLORE_10_P95_MS_LIMIT, (
        f"explore_10 p95 {result.p95_ms:.1f}ms exceeds {EXPLORE_10_P95_MS_LIMIT}ms "
        f"(mean={result.mean_ms:.1f}ms)"
    )