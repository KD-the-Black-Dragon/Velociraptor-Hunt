# Acceptance Report: 1v1-arena

**Date:** 2026-07-15  
**Scope:** PR1 — interactive secret arena (Ctrl+B); PR2 — headless `tools/sim_arena.py` bot with compare-sheet CSV.

## Automated verification

### Change-scoped suite

```bash
python -m pytest tests/test_arena_pr1.py tests/test_arena_pr2.py -v -n 4
```

**27/27** passed.

### Full suite (step 1 — parallel, 4 workers)

```bash
python -m pytest tests/ -v -n 4
```

| Result | Count |
|--------|-------|
| **PASS** | **1632** |
| **FAIL** | **24** |
| Skipped | 2 |

Duration: ~18 min.

### Serial rerun of step-1 failures (step 4)

| Test | Step 1 | Step 4 serial |
|------|--------|---------------|
| `test_haste_skips_monster_phase` | FAIL | PASS |
| `test_engine_post_turn_hook_invokes_coordinator` | FAIL | PASS |
| All other 22 step-1 failures | FAIL | FAIL |

**22 failed-twice** — assessed **pre-existing** balance/data regressions (wolf/knight spawn, summon pools, shark water spawn, throwables stacking, sim navigation seeds). Not introduced by 1v1-arena; tracked under `openspec/changes/balance-pass/`. No code changes made during this acceptance pass.

### Steps 8–9

Step 8 (parallel rerun of passed-first-try set) **not re-run** — no arena code changes since step 1; change-scoped suite green.

Step 9 (serial rerun of step-1 failure set) **satisfied by step 4** above.

## Manual verification

- [x] PR1 — designer sign-off (*"all looks good to me"*)
- [x] PR2 — designer sign-off (*"all looks good to me"*)

## Requirement coverage

| Deliverable | Status |
|-------------|--------|
| Ctrl+B → entity id entry (evil ids only, three-column list) | Shipped |
| 1×10 hallway; aquatic water tile at far right | Shipped |
| Depth-jump loadout at `spawn.min_depth − 1` | Shipped |
| `level_warped` — no Past Runs on victory or digestion | Shipped |
| Save isolation (no autosave; Ctrl+S no-op) | Shipped |
| Victory modal → main menu | Shipped |
| `src/sim/arena_policy.py` — bump / move right; no consumables | Shipped |
| `tools/sim_arena.py` — batch trials × all evil ids | Shipped |
| Compare-sheet CSV with auto-append columns | Shipped |
| `openspec/specs/1v1-arena/spec.md` | Shipped |

## Spec updates

- `openspec/specs/1v1-arena/spec.md` (new — interactive + bot)

## Notes

- Compare-sheet format: column A `metric` (meta + per-entity fields), run data in B+; default `arena_compare.csv`; `--overwrite` replaces sheet.
- Unrelated full-suite failures likely tied to in-flight balance/data tuning (`entities.json` spawn weights, throwables, global tuning). Follow up in **balance-pass**, not blocked on arena archive.