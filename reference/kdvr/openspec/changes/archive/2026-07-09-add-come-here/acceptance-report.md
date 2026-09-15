# Acceptance Report: add-come-here

**Date:** 2026-07-09  
**Scope:** Come here! shout (PR1 plumbing, PR2 AI, PR3 help/spec). Cooldown **4** turns.

## Automated verification

### Change-scoped

```bash
python -m pytest tests/test_come_here_pr1.py tests/test_come_here_pr2.py tests/test_help_overlay.py -q
```

| Result | Detail |
|--------|--------|
| **PASS** | 26 tests |

### Full suite

```bash
python -m pytest tests/ -n 6 --tb=line -q
```

| Result | Count |
|--------|-------|
| Passed | 1250 |
| Failed (first run) | 1 |
| Duration | ~12m 54s |

**First-run failure (re-run only):**

| Test | Re-run | Notes |
|------|--------|--------|
| `test_primary_at_three_preferred_over_neutral_at_two_for_ranged_pick` | **PASS** | Unrelated ranged AI identity assert; flake under parallel load |

## Manual verification

Designer signed off PR1–PR2 play (cooldown 4, approach, frustration, tag-clear). PR3 help line present.

## Live specs

- `openspec/specs/command-allies/spec.md`
