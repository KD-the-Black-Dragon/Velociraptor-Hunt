# Proposal: Enhancements 3 — Faction Content and AI

## Why

Enhancements 2 built alignment, naming, player swap, and basic faction rules, but **only evil wolves spawn** and AI is minimal (chase-or-idle). Good/neutral behavior is unit-tested, not played. Combat still **defeats** all NPCs at 0 HP, and wolves cannot vore allies.

Enhancements 3 adds **knights** and **rabbits**, revamps **NPC AI** (memory, exploration, priority), extends **swap** to NPC↔NPC, introduces **NPC stunned/regen**, and adds **log-only NPC vore** with headless engulf (digestion deferred).

## What Changes

- **Content:** Knight (good, cyan `k`), rabbit (neutral, grey `r`); static test spawn counts; examine placeholders
- **Combat:** Good/neutral **stunned** at 0 HP (not removed); evil **defeated** at 0 HP; stunned messages
- **Regen:** Good/neutral +1 HP / 8 player turns; evil +1 HP / 12 player turns
- **AI:** Priority pursuit → last known position → random explore goal; evil tiered targeting (good/player > neutral); good follows player when quiet; neutral flee when HP > 0
- **Swap:** Good↔good, good↔neutral, neutral↔neutral, evil↔evil on bump; **only player** may swap with good/neutral; no NPC swaps onto player
- **NPC vore:** Evil vores weakened good/neutral; **log only** (OV/CV/AV message pools); headless **engulf** on hit; allies can free engulfed good/neutral by defeating the predator
- **Deferred:** Digestion, procedural spawn tables, content-pref UI

## Capabilities

### New Capabilities

- `enhancements-3`: Faction NPC types, exploration AI, NPC stunned/regen, NPC vore logs, NPC engulf.

### Modified Capabilities

- `enhancements-2`: Evil pursues neutrals as secondary; NPC↔NPC swap; supersede “evil ignores neutral”
- `vore`: NPC prey eligibility, log-only attempt resolution, headless engulf

## Impact (anticipated)

- `src/components.py` — `AIState` (last known, explore goal), NPC `Stunned` usage
- `src/spawn.py` — static wolves + knights + rabbits
- `src/systems/ai.py` — priority stack, memory, explore, flee, NPC swap initiation
- `src/systems/combat.py` — stunned good/neutral, NPC swap paths, NPC regen hooks
- `src/systems/vore.py` — NPC vore attempt, message pools, headless engulf
- `src/vore_npc_content.py` (new) — OV/CV/AV log message pools
- `src/engine.py` — NPC regen on player turn
- Tests: `tests/test_enhancements_3.py`; updates to `test_enhancements_2.py` where superseded

## Success Criteria

All scenarios in `openspec/specs/enhancements-3/spec.md` pass. Prior acceptance tests remain green. Manual checklist per PR.

## Resolved decisions

Author confirmed 2026-06-29 — see **Resolved decisions** in [`design.md`](design.md).