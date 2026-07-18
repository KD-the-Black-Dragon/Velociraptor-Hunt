from __future__ import annotations

"""NPC digestion message pools keyed by narrative type (OV, CV, AV)."""

DIGESTION_COMPLETE_POOL: dict[str, tuple[str, ...]] = {
    "OV": (
        "{predator} burps triumphantly - {prey} has been digested.",
        "{predator} rumbles contentedly - {prey} is gone.",
    ),
    "CV": (
        "{predator} releases what's left of {prey} as white slime.",
        "{predator} expels the remains of {prey} as pale slime.",
    ),
    "AV": (
        "{predator}'s abdomen compresses - {prey} has been digested.",
        "{predator}'s belly tightens - {prey} has been digested.",
    ),
}

GOOD_PLEA_POOL: tuple[str, ...] = (
    "From inside {predator}, {prey} begs for rescue.",
    "From inside {predator}, {prey} grunts helplessly.",
)

PLAYER_DIGESTION_MODAL: dict[str, str] = {
    "OV": "{predator} howls in triumph as it digests a great prize - you.",
    "CV": "{predator} expels what's left of you as white slime onto the stony floor.",
    "AV": "{predator} howls in triumph as its abdomen compresses on a great prize - you.",
}