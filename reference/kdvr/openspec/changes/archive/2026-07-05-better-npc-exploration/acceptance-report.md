# Acceptance Report: better-npc-exploration

**Date:** 2026-07-05  
**Scope:** BFS reachable explore goals (PR1), explore frustration (PR2), BFS explore steps + oscillation + evil-no-swap + door spite (PR3), retire PR10 shim + neutral shared explore path (PR4)

## Automated verification

### Change gate (targeted)

```bash
python -m pytest tests/test_explore_reachable_goals.py tests/test_explore_frustration.py tests/test_explore_bfs_steps.py tests/test_neutral_explore.py tests/test_chase_pursuit_momentum.py tests/test_debug_omniscient_vision.py tests/test_enhancements_3.py -q
```

| Result | Count |
|--------|-------|
| **PASS** | **92** |

*Note: `test_engulfed_neutral_invisible_to_evil_ai` may flake when `iter_wolves` finds fewer than two wolves on the procedural map (pre-existing spawn setup). Re-run gate if needed.*

### Full suite

```bash
python -m pytest -q
```

| Result | Count |
|--------|-------|
| Passed | 841 |
| Failed | 25 |
| Warnings | 101 |
| Duration | ~27 min |

**Failures (not introduced by this change):** wolf-count / spawn-dependent tests (`iter_wolves` empty), stale JSON load assertions, vore modal/UI flakes, erratic movement tie-breaks, dungeon spawn config drift. No failures in explore-specific gate tests after `test_npc_evil_evil_do_not_swap` assertion fix (evil–evil bump combat is expected).

## Manual verification

- [x] PR1–PR3 playtest sign-off (user) — wolf door dispersal, no permanent oscillation
- [x] PR4 playtest sign-off (user) — rabbit movement clean; player-adjacent allowed
- [x] Final acceptance sign-off (2026-07-05)

## Requirement coverage

| PR | Delivered |
|----|-----------|
| PR1 | BFS reachable goals; weighted-random far pick; hands stub; re-pick on unreachable goal |
| PR2 | `explore_frustration` counters; farthest-endpoint once on give-up |
| PR3 | BFS one-step explore; sidestep; oscillation re-pick; evil–evil no swap; door spite counter; explore idle; NPC blocked tiles for explore |
| PR4 | PR10 shim removed; neutral shared explore path; player tile only blocked |

## Spec updates

- `openspec/specs/enhancements-3/spec.md` — **NPC Explore and Wander** requirement; evil–evil swap removed; explore bullets for evil/good/neutral
- `openspec/changes/todo/spec.md` — better-npc-exploration marked addressed; door-spite approach deferred

## Deferred / follow-up

- **Door spite — distant wolf should approach door** — `openspec/changes/todo/spec.md`
- **Performance throttling** — `openspec/changes/todo/spec.md`
- Stabilize wolf-count-dependent tests in full suite (separate hygiene pass)

## Archive

`openspec/changes/archive/2026-07-05-better-npc-exploration/`