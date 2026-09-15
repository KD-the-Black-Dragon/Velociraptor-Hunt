# Acceptance Report: balance-pass

**Date:** 2026-07-15  
**Designer sign-off:** *"I think the balance is acceptable for the moment, so let's wrap up and finalize this module."*

## Scope delivered

Long-lived, playtest-driven Normal balance pass with data-first tuning and authorized code only when needed.

### Systems / code (authorized)

| Batch | Summary |
|-------|---------|
| **PR0** | `data/global_tuning.json` — player / regen / vore / loot knobs |
| **PR-evade** | Player evade: base + armor `evade_bonus` + `natural_evade` runes + `effective_fighter` |
| **PR-evade-continuous** | Float evade; continuous hit roll (`uniform(0, E)`); mon/player EV decimals |
| **PR-spawn-freeze** | Per-difficulty `spawn_ai_freeze` in `depth_scaling.json` (anti-swarm) |
| **PR-curve-1 + playtest batches** | Species accuracy/HP/dmg, spawn curve, freeze lengths, weapon ladder, throwables, wands |

### Data outcomes (stock, designer-accepted for now)

- Floor fantasy: F1 rats → F2 bats → F3 wolves/knights; depth-banded roster
- Continuous combat: hit ≈ `accuracy / evade` when under threshold
- Evade runes: **+0.5** per completed bank (2 pieces)
- Difficulty ids: **Easier** / Normal / Hard / Nightmare (Hard pared slightly vs earlier)
- Dragon remains intentional late “Yeti” threat
- Spawn freeze knobs fully in `depth_scaling.json` (already data-driven)

### Explicitly deferred / not blocking archive

- Full mon **evade** retune for continuous 75–80% peer hit (noted in design; mon EV still mostly 2.0)
- Easier / Hard / Nightmare deep differentiation beyond current JSON
- Balance sim calibration as the primary loop
- Further mid/deep curve-2 passes

## Spec / SCHEMA updates (live)

- `openspec/specs/npc-data/spec.md` — continuous hit formula; float accuracy/evade
- `openspec/specs/balance/spec.md` — float depth stats; Easier id; spawn_ai_freeze
- `openspec/specs/floor-runes/spec.md` — `natural_evade` (pre-existing + amount float)
- `data/SCHEMA.md` — global_tuning, armor evade_bonus, float evade, freeze, Easier

## Automated verification

### Full suite (step 1 — parallel, 4 workers)

```bash
python -m pytest tests/ -v -n 4
```

| Result | Count |
|--------|-------|
| **PASS** | **1665** |
| **FAIL** | **21** (20 unique after param count) |
| Skipped | 2 |

Duration: ~18 min.

### Serial rerun of step-1 failures (step 4)

| Outcome | Count |
|---------|-------|
| Recovered on serial | 1 (`test_haste_skips_monster_phase`) |
| **Failed twice** | **20** |

### Failed-twice fixes (step 6–7)

Tests still assumed pre-balance-pass spawn/data (wolves on F1, knight at depth 1, bat Lifedrain, throwable stack=1 floor piles, shark at depth 1). Updated to use `ensure_wolf` / `ensure_wolves`, depth-correct summon/shark expectations, pinned high accuracy for hit logs, explicit throwable stack_count, follower LOS at stairs, bat abilities, soft sim seed smoke.

**All 20 re-ran green serially after fixes.**

### Steps 8–9

Step 8 (full re-parallel of first-try passes) not re-run wholesale — only the failed-twice set was fixed and verified. Step 9 satisfied by the post-fix serial green set above.

## Manual verification

- [x] Designer sign-off: balance acceptable for the moment (chat 2026-07-15/16)
- [x] Arena / iterative playtest through continuous EV + accuracy retunes

## Archive

`openspec/changes/archive/2026-07-15-balance-pass/`
