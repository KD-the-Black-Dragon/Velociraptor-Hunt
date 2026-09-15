# Acceptance Report: add-tutorial-page

**Date:** 2026-07-12  
**Scope:** PR1 — first-run onboarding (tutorial prompt, paginated Quick Start, vore prefs, all-set screen, Options → Tutorial).

## Automated verification

### Change-scoped suite

```bash
python -m pytest tests/test_onboarding_pr1.py -v
```

**12/12** passed (includes copy and flow assertions).

### Full suite (step 1 — parallel, 4 workers)

```bash
python -m pytest tests/ -v -n 4
```

| Result | Count |
|--------|-------|
| **PASS** | **1587** |
| **FAIL** | **10** |
| Skipped | 2 |

### Serial rerun of step-1 failures (step 4)

| Test | Step 1 | Step 4 serial |
|------|--------|---------------|
| `test_evil_still_targets_last_known_primary_while_pathing` | FAIL | PASS |
| `test_engulfed_good_npc_invisible_to_evil_ai` | FAIL | PASS |
| `test_wolf_playtest_overrides_reverted` | FAIL | FAIL |
| `test_haste_skips_monster_phase` | FAIL | PASS |
| `test_engine_post_turn_hook_invokes_coordinator` | FAIL | PASS |
| `test_start_isolation_floor_at_depth_three` | FAIL | FAIL |
| `test_sim_isolation_run_returns_snapshot` | FAIL | FAIL |
| `test_balance_analysis_includes_isolation_runs` | FAIL | FAIL |
| `test_vore_modal_drawn_on_root_console_over_sidebar` | FAIL | PASS |
| `test_after_miss_complete_next_player_turn_starts_from_zero` | FAIL | FAIL |

Seven xdist flakes; three **failed-twice** (wolf stock data, missing sim isolation hook, fragile wolf spawn).

### Failed-twice fixes (step 7)

| Test | Fix |
|------|-----|
| `test_wolf_playtest_overrides_reverted` | Assert wolf `abilities == ()` — Range6 removed in stock balance pass |
| `test_start_isolation_floor_at_depth_three` (+ 2 sim isolation tests) | Add `GameEngine.initialize_isolation_floor` → `engine_floor.initialize_floor_isolation` (sim-only hook from balance simulator) |
| `test_after_miss_complete_next_player_turn_starts_from_zero` | Pin `new_game(seed=42)` + `ensure_wolves(engine, 1)` |

All failed-twice cases passed on serial rerun after fix.

### Step 9 — serial rerun of step-1 failure set + onboarding

```bash
python -m pytest <10 step-1 failures> tests/test_onboarding_pr1.py -v
```

**22/22** passed.

## Manual verification

- [x] PR1 — designer sign-off (*"Okay, I think we're all good."*)

## Requirement coverage

| Deliverable | Status |
|-------------|--------|
| First-run tutorial prompt (no default selection) | Shipped |
| Paginated tutorial (pages 1–2 + reminder; Options replay) | Shipped |
| Vore prefs onboarding (independent leg) | Shipped |
| All-set screen after vore confirm | Shipped |
| `tutorial_prompt_answered` + `vore_prefs_onboarding_complete` | Shipped |
| Options → Tutorial row | Shipped |
| `openspec/specs/onboarding/spec.md` | Shipped |

## Spec updates

- **Created:** `openspec/specs/onboarding/spec.md`

## Out of scope (confirmed)

- In-game contextual tutorials
- F1 help content overhaul

## Ancillary fixes (acceptance gate)

- Sim isolation floor bootstrap hook (`initialize_floor_isolation`) — completes balance-simulator PR6 engine delegate that was missing from `GameEngine`.
- Wolf abilities content test aligned with stock `entities.json`.