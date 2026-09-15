# Proposal: Engulfed flavor text

**Status:** Active  
**Change id:** `engulfed-flavor-text`  
**Extends:** `openspec/specs/vore/spec.md`; `data/entities.json` schema; message log categories

## Why

While engulfed, the player currently gets struggle / digestion / modal feedback but little ongoing **atmospheric** belly text. Predators should optionally emit typed flavor lines (OV / CV / AV) on a steady cadence so content authors can deepen the engulfment feel without changing mechanics.

## What

1. Optional per-entity `engulfed_flavor` object: `{ "OV"|"CV"|"AV": string[] }`. Missing field, missing key, or empty array → that type has no lines (silent no-op; never log blank).
2. While the **player** is held, after every **completed world phase**, increment a counter on the holding `Predator`. On phases **3, 6, 9…** of that hold, if a non-empty pool exists for `Predator.narrative_type`, pick one line at random, format `{predator}`/`{prey}`, log in **bright white** (`MessageCategory.SPEECH`).
3. Stops when engulfment ends (escape, predator defeated, game over). No stock entity text in this change — schema + systems only.

## Out of scope

- Filling flavor for all stock predators
- Flavor for NPC-as-prey
- Player-turn-based cadence
- New MessageCategory (reuse SPEECH white)

## Success

- Predators with no / empty flavor stay silent
- Typed pools only fire for matching narrative type
- Cadence is every 3rd world phase of the hold; white log color; placeholders work
- Tests use pinned fixtures (no live `data/entities.json` pins)

## Phased delivery

See `tasks.md` (data → runtime → specs/archive).
