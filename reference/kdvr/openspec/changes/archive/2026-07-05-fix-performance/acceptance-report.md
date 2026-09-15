# Acceptance Report: fix-performance

**Date:** 2026-07-05  
**Scope:** Tier A only — BFS caching (PR2), registry cache + regression gates (PR3). Tier B deferred.

## Automated verification

### Performance regression gate

```bash
python -m pytest tests/test_performance_regression.py -v
```

| Result | Count |
|--------|-------|
| **PASS** | **2** |

### Explore / chase gate

```bash
python -m pytest tests/test_explore_bfs_steps.py tests/test_explore_frustration.py tests/test_explore_reachable_goals.py tests/test_neutral_explore.py tests/test_chase_pursuit_momentum.py -q
```

| Result | Count |
|--------|-------|
| **PASS** | **42** |

### Full suite

```bash
python -m pytest -q
```

| Result | Count |
|--------|-------|
| Passed | 933 |
| Failed | 5 |
| Duration | ~27 min |

**Failures (pre-existing, not introduced by this change):** `test_dungeon_pr3`, `test_dungeon_spawn_config`, `test_npc_abilities_rangen`, `test_npc_data_pr1`, `test_vore_engulfed`.

## Profile results (PR2+PR3, seed 42, headless)

| Scenario | Before | After |
|----------|--------|-------|
| `default` mean | 461 ms | **77 ms** |
| `default` p95 | 572 ms | **92 ms** |
| `explore_10` mean | 4819 ms | **231 ms** |

## Manual verification

- [x] PR2 playtest sign-off (user) — massive improvement, responsive turns
- [x] PR3 sign-off (user)
- [x] Final acceptance (2026-07-05)

## Delivered

| PR | Deliverable |
|----|-------------|
| PR1 | `tools/profile_turn.py`, `investigation-report.md` |
| PR2 | `ExploreBfsCache`, goal-distance cache, sanitize early exit, hoisted BFS |
| PR3 | `get_entity_registry()`, `test_performance_regression.py` |

## Deferred

- **Tier B distant throttle** → `openspec/changes/deferred-fix-performance-distant-throttle/`

## Spec updates

- `openspec/specs/performance/spec.md` (new)
- `openspec/changes/todo/spec.md` — performance core addressed; throttle deferred

## Archive

`openspec/changes/archive/2026-07-05-fix-performance/`