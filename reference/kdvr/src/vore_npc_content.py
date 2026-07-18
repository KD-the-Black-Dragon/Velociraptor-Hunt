from __future__ import annotations

"""NPC vore message pools keyed by narrative type (OV, CV, AV)."""

NPC_VORE_MISS_POOL: dict[str, tuple[str, ...]] = {
    "OV": (
        "{predator} tries to swallow {prey} but fails.",
        "{predator} lunges at {prey}, but {prey} wriggles free.",
    ),
    "CV": (
        "{predator} coils around {prey} but cannot finish the swallow.",
        "{predator} squeezes {prey}, but loses its grip.",
    ),
    "AV": (
        "{predator} reaches for {prey}, but {prey} evades being taken in.",
        "{predator} attempts to draw {prey} inside, without success.",
    ),
}

NPC_VORE_HIT_POOL: dict[str, tuple[str, ...]] = {
    "OV": (
        "{predator} swallows {prey} whole!",
        "{predator} gulps {prey} down in one motion.",
    ),
    "CV": (
        "{predator} constricts and swallows {prey}!",
        "{predator} pulls {prey} into its gullet with a crushing squeeze.",
    ),
    "AV": (
        "{predator} draws {prey} inside!",
        "{predator} takes {prey} in completely.",
    ),
}