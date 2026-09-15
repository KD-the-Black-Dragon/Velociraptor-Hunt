# Acceptance Report: add-extra-npc-prefixes

**Date:** 2026-07-11  
**Scope:** Extra evil NPC prefixes (Brute, Berserk, Veteran, Starving, Sniper, Bloated), filter-then-roll requirements, ability grants, `ranged_accuracy` (PR1–PR3).

## Automated verification

### Full suite (step 1 — parallel, 4 workers)

```bash
python -m pytest tests/ -v -n 4
```

| Result | Count |
|--------|-------|
| **PASS** | **1525** |
| **FAIL** | **4** |
| Skipped | 2 |

### Serial rerun of step-1 failures (step 4)

| Test | Step 1 | Step 4 serial |
|------|--------|---------------|
| `test_engulfed_player_immune_to_combat_damage` | FAIL | PASS |
| `test_engulfed_neutral_invisible_to_evil_ai` | FAIL | PASS |
| `test_engine_post_turn_hook_invokes_coordinator` | FAIL | PASS |
| `test_vore_modal_drawn_on_root_console_over_sidebar` | FAIL | PASS |

All recovered on serial rerun (xdist flake). **No failed-twice cases** — no code changes required for acceptance.

### Change-scoped tests (PR1–PR2)

| Area | Files |
|------|-------|
| Infrastructure | `test_npc_prefixes_extra_pr1.py` |
| Elite regression | `test_npc_prefixes_pr4.py` |
| Stock content | `test_npc_prefixes_content_pr2.py` |

**21/21** prefix tests passed.

## Manual verification

- [x] PR1 — infrastructure (user authorized)
- [x] PR2 — stock content + playtest sign-off (*"All good, proceed with PR2."*)
- [x] PR3 — final acceptance authorized (*"All good, proceed with PR3."*)

## Requirement coverage

| Deliverable | Status |
|-------------|--------|
| Filter-then-roll with `requirements.ability_families` | Shipped |
| `grant_abilities` (Slow, PreferVore) | Shipped |
| `ranged_accuracy` stat key | Shipped |
| Stock prefixes: brute, berserk, veteran, starving, sniper, bloated | Shipped |
| Elite supplements shared weight pool | Shipped |
| Sniper gated to `RangeN` hosts only | Shipped |

## Spec updates

- **Updated:** `openspec/specs/balance/spec.md`, `data/SCHEMA.md` (PR1)

## Out of scope (confirmed)

- Good/neutral prefix rolls
- Prefixes on summons
- `prefix_spawn` curve changes (unchanged in PR2)
- Prefix soft-drop stat/ability revert on load (legacy behavior)