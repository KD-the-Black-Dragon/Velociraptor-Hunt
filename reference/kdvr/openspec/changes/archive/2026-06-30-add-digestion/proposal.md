# Proposal: Digestion — NPC and Player Defeat via Vore

## Why

Enhancements 3 added **headless engulf** for good/neutral NPC prey and player modal engulf, but explicitly **deferred digestion**. Stunned allies can persist indefinitely inside a predator unless rescued. The vore spec still states digestion and player game-over are out of scope.

Digestion completes the vore loop: engulfed prey take periodic damage, accumulate **strikes** at 0 HP, and are **removed** (NPC) or **game over** (player) after three strikes. Predators gain attack-only behavior while holding prey; freed prey gain mercy invincibility (extended to NPCs).

## What Changes

### Phase 1 — NPC digestion (good/neutral prey)

- Digestion tick when prey's AI slot would run (skip turn + damage)
- Per-predator `digestion_damage` (wolf **3** initially)
- HP-first, then three-strike timer at 0 HP (no strike on same tick as HP→0)
- `DigestionStrikes` on prey; reset on freedom; regen blocked while `strikes >= 1`
- Good NPC 10% plea messages per tick (player LOS); neutrals silent on tick
- OV/CV/AV **completion** message pools on NPC digested (log only)
- `narrative_type` stored on `Predator` at engulf time
- Predator **attack-only** while holding (no move, no new vore); not fully frozen
- **NPC `VoreMercy`** on release (parity with player)
- Predator may act again **next player turn** after digest completes

### Phase 2 — Player digestion

- Same HP / strike cadence while engulfed (per player turn, alongside struggle)
- Third strike → **digestion modal** (OV/CV/AV × predator placeholders)
- Then **game over** screen (name/score stubs, digested-by line)
- **Enter** dismisses → exit game (main menu stub acceptable later)

### Content constraint (AV)

**Clean AV only:** abdominal crushing and engulfment. No implicit expansion of AV semantics in messages or modals.

## Capabilities

### New

- `digestion`: strike timer, per-predator damage, NPC removal, player game over

### Modified

- `vore`: digestion in scope; predator holding behavior; mercy for NPCs
- `enhancements-3`: good/neutral removal path via digestion (supersedes “indefinite until digestion” deferral)

## Impact (anticipated)

| Area | Files |
|------|--------|
| Components | `src/components.py` — `DigestionStrikes`, `DigestionDamage` or spawn stats; extend `Predator` |
| Constants / spawn | `src/constants.py`, `src/spawn.py` — wolf digestion damage |
| Digestion logic | `src/systems/digestion.py` (new) or extend `src/systems/vore.py` |
| AI | `src/systems/ai.py` — prey tick hook; predator attack-only |
| Combat / regen | `src/systems/combat.py`, `src/engine.py` — mercy for NPCs; regen gate |
| Content | `src/digestion_content.py` (new) — completion + plea pools |
| Engine / render | `src/engine.py` — player digest modal, game over state |
| Tests | `tests/test_digestion.py` (new); updates to vore/enhancements tests |
| Specs | `openspec/specs/vore/spec.md`, `openspec/specs/enhancements-3/spec.md`, new `digestion/spec.md` |

## Success Criteria

- All scenarios in `openspec/specs/digestion/spec.md` (authored with this change) pass automated tests
- Prior acceptance suite remains green
- Manual checklist per PR
- AV content reviewed for clean scope

## Resolved decisions

Author confirmed 2026-06-30 — see **Resolved decisions** in [`design.md`](design.md).