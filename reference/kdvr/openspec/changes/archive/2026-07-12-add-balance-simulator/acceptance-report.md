# Acceptance Report: add-balance-simulator

**Date:** 2026-07-12  
**Scope:** Hybrid balance difficulty analyzer (PR1–PR7): headless trajectory + isolation passes, policy bot, compare-sheet CSV, `tools/sim_balance.py`.

## Automated verification

### Full suite (step 1 — parallel, 4 workers)

```bash
python -m pytest tests/ -v -n 4
```

| Result | Count |
|--------|-------|
| **PASS** | **1579** |
| **FAIL** | **6** |
| Skipped | 2 |

### Serial rerun of step-1 failures (step 4)

| Test | Step 1 | Step 4 serial |
|------|--------|---------------|
| `test_wolf_visible_to_knight_blocks_introduction` | FAIL | FAIL |
| `test_engulfed_player_immune_to_combat_damage` | FAIL | PASS |
| `test_wolf_playtest_overrides_reverted` | FAIL | FAIL |
| `test_descend_with_follower_keeps_good_ally_on_new_floor` | FAIL | PASS |
| `test_engine_post_turn_hook_invokes_coordinator` | FAIL | PASS |
| `test_vore_modal_drawn_on_root_console_over_sidebar` | FAIL | PASS |

Four xdist flakes; two **failed-twice** (wolf stock data + fragile spawn assumption).

### Failed-twice fixes (step 7)

| Test | Fix |
|------|-----|
| `test_wolf_playtest_overrides_reverted` | Assert wolf `abilities == ()` — Range6 removed in stock balance pass |
| `test_wolf_visible_to_knight_blocks_introduction` | Use `ensure_wolf()` instead of `next(iter_wolves())` |
| `test_engulfed_player_immune_to_combat_damage` | Use `ensure_wolves(engine, 2)` for second hunter wolf |

All three passed on serial rerun after fix. Remaining step-1 failures were xdist flakes only.

### Change-scoped sim suite

```bash
python -m pytest tests/test_sim_aggregator.py tests/test_sim_equip.py tests/test_sim_isolation.py tests/test_sim_navigation.py tests/test_sim_runner.py tests/test_sim_scoring.py tests/test_sim_threat.py -v -n 4
```

**56/56** passed.

## Manual verification

- [x] PR1–PR6 — designer sign-off through PR6 (*"I believe we're good. Proceed with PR7."*)
- [ ] PR7 — final acceptance checklist (`testing-checklist-pr7.md`)

## Requirement coverage

| Deliverable | Status |
|-------------|--------|
| `tools/sim_balance.py` hybrid CLI | Shipped |
| Trajectory pass + `traj_*` columns | Shipped |
| Isolation pass + `iso_*` columns | Shipped |
| Compare-sheet CSV + `--append` | Shipped |
| Stock-only data + fingerprint | Shipped |
| Policy: navigation, survival, loot, equip | Shipped |
| Pinned seeds + seed scan tool | Shipped |
| `openspec/specs/balance-simulator/spec.md` | Shipped |

## Spec updates

- **Created/updated:** `openspec/specs/balance-simulator/spec.md`
- **Cross-reference:** `openspec/specs/balance/spec.md` Related table

## Supersedes

- `openspec/changes/deferred-add-balance-simulator/` (depth-only deferred design)

## Out of scope (confirmed)

- Macguffin pursuit in sim
- Modded data in sim production paths
- JSONL per-event export (deferred)
- CI gate on sim runtime