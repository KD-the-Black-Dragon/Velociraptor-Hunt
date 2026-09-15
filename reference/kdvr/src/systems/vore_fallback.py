"""Prefs-immune GENERIC vore type — last-resort copy when no OV/CV/AV is attemptable.

Not shown in Options. Extremely basic templates for edge cases (capability∩prefs
empty, data mismatch). Digestion uses the standard (non-alternate-CV) path.

Likely unreachable under current design: run prefs are snapshotted at New Game and
cannot change mid-run, and spawn OR already excludes species with no capability∩prefs
intersection. Kept as a stub if that contract ever changes (or for odd save/mod edges).
"""

from __future__ import annotations

GENERIC_VORE_TYPE = "GENERIC"

# Player engulf modal (attempt / success phases).
GENERIC_PLAYER_ATTEMPT: tuple[str, ...] = (
    "{predator} attempts to swallow you.",
)
GENERIC_PLAYER_SUCCESS: tuple[str, ...] = (
    "{predator} swallows you.",
)

# Player digestion completion modal phases.
GENERIC_PLAYER_DIGESTION_MODAL: tuple[str, ...] = (
    "{predator} digests you.",
)

# NPC-vs-NPC on-screen logs.
GENERIC_NPC_VORE_HIT: tuple[str, ...] = (
    "{predator} swallows {prey}.",
)
GENERIC_NPC_VORE_MISS: tuple[str, ...] = (
    "{predator} fails to swallow {prey}.",
)

# NPC digestion complete (on-screen).
GENERIC_DIGESTION_COMPLETE: tuple[str, ...] = (
    "{predator} digests {prey}.",
)

# Off-screen atmospheric one-liners (optional {predator}/{prey}).
GENERIC_OFFSCREEN_VORE: tuple[str, ...] = (
    "Somewhere nearby, {predator} swallows {prey}.",
)
GENERIC_OFFSCREEN_DIGEST: tuple[str, ...] = (
    "Somewhere nearby, {predator} finishes digesting {prey}.",
)


def is_generic_vore_type(narrative_type: str) -> bool:
    return narrative_type == GENERIC_VORE_TYPE
