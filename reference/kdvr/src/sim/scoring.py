"""Per-floor event scoring for balance analysis (v1 weights)."""

from __future__ import annotations

from src.sim.snapshots import FloorOutcomeSnapshot

RUNES_MISSED_MAX = 30.0
CONSUMABLES_MAX = 25.0
UPGRADE_SLOT_MAX = 10.0
EARLY_BAIL_OVERLAY = 10.0
NON_DIGEST_CAP = 99.0

HEAL_WEIGHT = 8.0
MIGHT_WEIGHT = 6.0
HASTE_WEIGHT = 5.0
TELEPORT_WEIGHT = 4.0
WAND_WEIGHT = 2.0


def consumable_sacrifice_score(snapshot: FloorOutcomeSnapshot) -> float:
    raw = (
        snapshot.consumable_heal * HEAL_WEIGHT
        + snapshot.consumable_might * MIGHT_WEIGHT
        + snapshot.consumable_haste * HASTE_WEIGHT
        + snapshot.consumable_teleport * TELEPORT_WEIGHT
        + snapshot.wand_evokes * WAND_WEIGHT
    )
    return min(CONSUMABLES_MAX, raw)


def runes_missed_score(snapshot: FloorOutcomeSnapshot) -> float:
    quota = max(1, snapshot.rune_quota)
    missed = max(0, quota - snapshot.runes_this_floor)
    return (missed / quota) * RUNES_MISSED_MAX


def upgrade_sacrifice_score(snapshot: FloorOutcomeSnapshot) -> float:
    score = 0.0
    if not snapshot.weapon_improved:
        score += UPGRADE_SLOT_MAX
    if not snapshot.armor_improved:
        score += UPGRADE_SLOT_MAX
    return score


def early_bail_overlay(snapshot: FloorOutcomeSnapshot) -> float:
    if not snapshot.descended:
        return 0.0
    if snapshot.runes_this_floor >= snapshot.rune_quota:
        return 0.0
    if not snapshot.bail_for_survival:
        return 0.0
    return EARLY_BAIL_OVERLAY


def event_score(snapshot: FloorOutcomeSnapshot) -> float:
    """Composite difficulty score for one floor visit (0–100)."""
    if snapshot.digested:
        return 100.0

    total = (
        runes_missed_score(snapshot)
        + consumable_sacrifice_score(snapshot)
        + upgrade_sacrifice_score(snapshot)
        + early_bail_overlay(snapshot)
    )
    return min(NON_DIGEST_CAP, total)