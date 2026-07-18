from __future__ import annotations

import attrs

from src.components import Alignment

EVIL_ARCHETYPE_ID = "wolf"
GOOD_ARCHETYPE_ID = "knight"
NEUTRAL_ARCHETYPE_ID = "rabbit"

DEFAULT_DIGESTION_DAMAGE_PER_TICK = 3
DEFAULT_DIGEST_TIME = 6


@attrs.define(frozen=True)
class AlignmentProfile:
    """Behavior derived from alignment; archetype ids name the reference species."""

    archetype_id: str
    vore_capable: bool
    digests: bool
    follows_on_descent: bool
    blocks_movement: bool
    default_digestion_damage_per_tick: int
    default_digest_time: int


_ALIGNMENT_PROFILES: dict[Alignment, AlignmentProfile] = {
    Alignment.EVIL: AlignmentProfile(
        archetype_id=EVIL_ARCHETYPE_ID,
        vore_capable=True,
        digests=True,
        follows_on_descent=False,
        blocks_movement=True,
        default_digestion_damage_per_tick=DEFAULT_DIGESTION_DAMAGE_PER_TICK,
        default_digest_time=DEFAULT_DIGEST_TIME,
    ),
    Alignment.GOOD: AlignmentProfile(
        archetype_id=GOOD_ARCHETYPE_ID,
        vore_capable=False,
        digests=False,
        follows_on_descent=True,
        blocks_movement=True,
        default_digestion_damage_per_tick=0,
        default_digest_time=0,
    ),
    Alignment.NEUTRAL: AlignmentProfile(
        archetype_id=NEUTRAL_ARCHETYPE_ID,
        vore_capable=False,
        digests=False,
        follows_on_descent=False,
        blocks_movement=True,
        default_digestion_damage_per_tick=0,
        default_digest_time=0,
    ),
}


def alignment_profile(alignment: Alignment) -> AlignmentProfile:
    return _ALIGNMENT_PROFILES[alignment]


def digestion_damage_for(entity_alignment: Alignment, explicit: int | None) -> int | None:
    """Return per-tick digestion damage for evil entities; None for non-evil."""
    profile = alignment_profile(entity_alignment)
    if not profile.digests:
        return None
    if explicit is not None:
        return explicit
    return profile.default_digestion_damage_per_tick


def digest_time_for(entity_alignment: Alignment, explicit: int | None) -> int | None:
    """Return strike threshold at 0 HP for evil entities; None for non-evil."""
    profile = alignment_profile(entity_alignment)
    if not profile.digests:
        return None
    if explicit is not None:
        return explicit
    return profile.default_digest_time