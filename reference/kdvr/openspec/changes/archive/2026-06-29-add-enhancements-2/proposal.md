# Proposal: Enhancements 2 — NPC Identity

## Why

Combat logs, vore narrative, and AI still treat predators generically ("the monster") despite wolves already carrying a `DisplayName`. There is no faction behavior, no way to distinguish allies from enemies beyond bump-combat, and no in-game inspection of entities. Future content (knights, named NPCs, shops, quests) needs a consistent identity and alignment layer before more systems attach.

Enhancements 2 lays that groundwork without adding new NPC species in v1 — wolves remain the only spawn, tagged **evil**.

## What Changes

- **Named combat and log messages** — every NPC referenced by species or proper name; no generic "monster" strings in gameplay logs
- **Alignment** — every NPC has `good`, `evil`, or `neutral`; evil hunts nearest hostile (player or good) with random tie-break; good hunts evil; neutral flees evil and is indifferent to the player
- **Player-initiated swap** — bumping good or neutral NPCs swaps tiles and skips their turn; only the player may initiate swap; good/neutral never attack or swap onto the player
- **NPC vs NPC combat** — evil and good fight when in line of sight
- **Vore alignment gate** — good and neutral never initiate vore
- **Examine (`x`)** — free cursor mode; engulfed `x` logs *"You can't see anything!"*
- **Enhanced descriptions** — placeholder prose on all NPCs and floor items
- **Input** — **`Ctrl+Q`** quits; **`Escape`** cancels in-progress commands only

## Capabilities

### New Capabilities

- `enhancements-2`: Identity, alignment, examine, and faction-aware AI/combat messaging.

### Modified Capabilities

- `core-roguelike`: Bump combat messaging, quit key (`Ctrl+Q`), player-vs-NPC swap rules.
- `vore`: Vore eligibility checks alignment; naming helpers shared with combat logs.

## Impact (anticipated)

- `src/components.py` — `Alignment`, `ProperName`, `ExamineDescription`; clarify `DisplayName` as species/type
- `src/messages.py` — parameterized templates for all combat parties
- `src/systems/naming.py` (new) — shared log/display name resolution
- `src/systems/combat.py`, `src/systems/ai.py`, `src/systems/movement.py` — swap, faction targeting, skip-turn
- `src/systems/examine.py`, `src/engine.py`, `src/input_handlers.py`, `src/systems/render.py` — examine mode + modal
- `src/spawn.py` — wolf evil alignment + descriptions; potion descriptions
- Tests: `tests/test_enhancements_2.py`, updates to combat/vore acceptance tests

## Success Criteria

All scenarios in `openspec/specs/enhancements-2/spec.md` pass. Existing core, enhancements-1, and vore tests remain green.

## Resolved decisions

Author confirmed 2026-06-29 — see **Resolved decisions** in [`design.md`](design.md). Ready for implementation.