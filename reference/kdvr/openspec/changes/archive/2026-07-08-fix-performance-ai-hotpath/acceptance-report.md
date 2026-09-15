# Acceptance Report: fix-performance-ai-hotpath

**Date:** 2026-07-08  
**Scope:** Group P (P1–P4 behavior-preserving hot-path) + distant throttle D2/D3/D4 (busy-gated).  
**Not in scope:** D1 simplified explore, D5 stand-still, G\* global cuts.

## Success targets vs measured (headless, seed 42)

| Metric | Target | Measured | Result |
|--------|--------|----------|--------|
| `default` p95 | &lt; 100 ms | **~80 ms** (30 NPCs) | **PASS** |
| `explore_10` mean | &lt; 120 ms | **~13 ms** | **PASS** |
| `explore_25` mean | &lt; 250 ms | **~22 ms** | **PASS** |
| `scale_25` p95 | &lt; 200 ms | **~43 ms** | **PASS** |

### Full profile table (acceptance)

| Scenario | NPCs | Mean | Median | P95 | Max |
|----------|------|------|--------|-----|-----|
| `default` | 30 | 63 ms | 61 ms | **80 ms** | 84 ms |
| `explore_10` | 10 | 13 ms | 11 ms | 24 ms | 25 ms |
| `explore_25` | 25 | 22 ms | 21 ms | 43 ms | 43 ms |
| `scale_25` | 25 | 18 ms | 15 ms | 43 ms | 47 ms |
| `scale_50` | 50 | 27 ms | 23 ms | 39 ms | 49 ms |
| `sparse` | 30 | 55 ms | 55 ms | 72 ms | 74 ms |

### Baseline comparison (pre this change, 2026-07-08 re-profile)

| Scenario | Before | After |
|----------|--------|-------|
| `default` p95 | up to ~287 ms | **~80 ms** |
| `explore_10` mean | ~221 ms | **~13 ms** |
| `explore_25` mean | ~540 ms | **~22 ms** |
| `scale_25` p95 | ~565 ms | **~43 ms** |
| `scale_50` p95 | ~1140 ms | **~39 ms** |

## Automated verification

### Performance regression gate (tightened)

```bash
python -m pytest tests/test_performance_regression.py -v
```

Limits: `default` p95 &lt; **150 ms**, `explore_10` p95 &lt; **100 ms**.

### Targeted AI / throttle suite

```bash
python -m pytest tests/test_performance_ai_hotpath_pr1.py tests/test_performance_distant_throttle.py tests/test_explore_bfs_steps.py tests/test_chase_pursuit_momentum.py tests/test_performance_regression.py -q
```

### Full suite

```bash
python -m pytest -q
```

| Result | Count |
|--------|-------|
| Passed | **1091** |
| Failed | **40** (mostly pre-existing data/content drift: macguffins depth, entity/narrative pools, balance numbers — same class as prior acceptance reports) |
| Duration | ~24 min |

**Performance-related / in-scope:** regression gates + distant throttle suite **PASS**. One `test_vore_engulfed` flaky-with-explore case fixed by also patching `_choose_explore_direction` (not a gameplay change).

## Manual verification

- [x] PR1 playtest sign-off (user) — Group P responsiveness
- [x] PR2 playtest sign-off (user) — distant throttle feel OK
- [x] Final acceptance (user authorized PR3)

## Delivered

| PR | Deliverable |
|----|-------------|
| PR1 | Walkability masks, array BFS, ensure-goal short-circuit, sanitize once/interval |
| PR2 | D2 half-turn, D3 memory cutoff, D4 busy gate; R=22 N=15; `ai_turn_salt` save |
| PR3 | Profile acceptance, tightened regression gates, archive |

## Spec updates

- `openspec/specs/performance/spec.md` — Group P + D2/D3/D4 requirements; gates 150/100 ms
- `openspec/changes/todo/spec.md` — item marked addressed

## Archive

`openspec/changes/archive/2026-07-08-fix-performance-ai-hotpath/`
