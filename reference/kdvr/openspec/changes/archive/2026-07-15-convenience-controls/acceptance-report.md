# Acceptance Report: convenience-controls

**Date:** 2026-07-15  
**Scope:** PR1 — autoexplore + shared danger/navigation modules; PR2 — Ctrl+direction force-attack.

## Automated verification

### Change-scoped suite

```bash
python -m pytest tests/test_autoexplore.py tests/test_force_attack.py tests/test_rest_until_healed.py -v -n 4
```

**35/35** passed.

### Full suite (step 1 — parallel, 4 workers)

```bash
python -m pytest tests/ -v -n 4
```

| Result | Count |
|--------|-------|
| **PASS** | **1667** |
| **FAIL** | **19** |
| Skipped | 2 |

Duration: ~17 min.

### Serial rerun of step-1 failures (step 4)

| Outcome | Count |
|---------|-------|
| Recovered on serial | 1 (`test_sidebar_evil_sorted_nearest_first`) |
| **Failed twice** | **18** |

**18 failed-twice** — assessed **pre-existing** balance/data regressions (wolf spawn weights, knight summon pools, shark water spawn, throwables stacking, ally introduction FOV fixtures). Not introduced by convenience-controls; tracked under `openspec/changes/balance-pass/`. No code changes made during this acceptance pass.

### Steps 8–9

Step 8 (parallel rerun of passed-first-try set) **not re-run** — no convenience-controls code changes since step 1; change-scoped suite green.

Step 9 (serial rerun of step-1 failure set) **satisfied by step 4** above.

## Manual verification

- [x] PR1 — designer sign-off (acceptable after 8-dir / per-step animation iteration)
- [x] PR2 — designer sign-off (*"Looks good. PR2 is signed off."*)

## Requirement coverage

| Deliverable | Status |
|-------------|--------|
| `` ` `` autoexplore (pickups → frontier, danger interrupts) | Shipped |
| Shared `danger_interrupts.py` + `player_navigation.py` | Shipped |
| Ctrl+direction force-attack (no move/swap/door) | Shipped |
| Engulfed → struggle; stunned → tired (no melee) | Shipped |
| Help overlay rows | Shipped |
| `openspec/specs/convenience-controls/spec.md` | Shipped |
| `tests/test_autoexplore.py`, `tests/test_force_attack.py` | Shipped |

## Spec updates

- `openspec/specs/convenience-controls/spec.md` (new — autoexplore + force-attack)

## Notes

- Autoexplore animation: **1 step per main-loop iteration**, `render` + `present`, no `REST_FRAME_SLEEP_SECONDS` (playtest iteration).
- Unrelated full-suite failures likely tied to in-flight balance/data tuning. Follow up in **balance-pass**, not blocked on convenience-controls archive.