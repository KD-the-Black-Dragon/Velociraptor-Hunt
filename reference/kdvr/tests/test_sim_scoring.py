"""PR5 tests for per-floor event scoring."""

from __future__ import annotations

from src.sim.scoring import (
    EARLY_BAIL_OVERLAY,
    RUNES_MISSED_MAX,
    UPGRADE_SLOT_MAX,
    event_score,
)
from src.sim.snapshots import FloorOutcomeSnapshot


def _snapshot(**kwargs) -> FloorOutcomeSnapshot:
    defaults = {
        "floor": 1,
        "seed": 1,
        "digested": False,
        "descended": True,
        "rune_quota": 3,
        "runes_this_floor": 3,
        "bail_for_survival": False,
        "weapon_improved": True,
        "armor_improved": True,
    }
    defaults.update(kwargs)
    return FloorOutcomeSnapshot(**defaults)


def test_digest_scores_100() -> None:
    assert event_score(_snapshot(digested=True)) == 100.0


def test_perfect_floor_scores_zero() -> None:
    assert event_score(_snapshot()) == 0.0


def test_runes_missed_scales_with_quota() -> None:
    half = event_score(_snapshot(runes_this_floor=0, descended=True))
    assert half == RUNES_MISSED_MAX


def test_upgrade_not_improved_adds_ten_per_slot() -> None:
    score = event_score(
        _snapshot(weapon_improved=False, armor_improved=False),
    )
    assert score == UPGRADE_SLOT_MAX * 2


def test_early_bail_overlay_when_below_quota() -> None:
    score = event_score(
        _snapshot(
            runes_this_floor=1,
            bail_for_survival=True,
            descended=True,
        ),
    )
    missed = (2 / 3) * RUNES_MISSED_MAX
    assert score == missed + EARLY_BAIL_OVERLAY


def test_consumable_weights_cap_at_25() -> None:
    score = event_score(
        _snapshot(
            consumable_heal=10,
            consumable_might=10,
            consumable_haste=10,
        ),
    )
    assert score == 25.0