# Performance

## Purpose

Player-turn wall-clock responsiveness. Explore AI BFS was the measured bottleneck (2026-07-05 investigation). Tier A + Group P hot-path optimizations preserve AI decisions; distant throttles (D2/D3/D4) apply only on busy floors beyond radius R.

**Terminology:** defeated, stunned, digested.

---

## Requirement: Explore BFS caching and hot-path (behavior-preserving)

Monster explore and chase **decisions** SHALL match pre-optimization behavior except where distant throttle (below) applies. Implementations MAY:

- Memoize per-visit `explore_reachable_distances` (`ExploreBfsCache` in `run_monster_turns`)
- Cache per-episode `explore_goal_distance_map` on `AIState` (ephemeral — not in save snapshot)
- Skip `_sanitize_unreachable_memory_targets` when all `last_known_*` fields are unset
- Hoist terrain predicates / use precomputed walkability masks and array BFS
- Short-circuit `_ensure_explore_goal` when episode distance map still covers origin
- Rate-limit memory sanitize BFS (interval K) and run it at most once per monster visit

`entity_explore_can_traverse` public semantics unchanged for tests and callers.

---

## Requirement: Distant AI throttle (busy floors)

Constants (defaults): `DISTANT_AI_RADIUS` **R** = 22, `BUSY_FLOOR_NPC_THRESHOLD` **N** = 15.

**Distant** = Chebyshev distance from player position > R (not FOV / viewport / LOS).

When active AI NPC count **> N** and the monster is distant:

| Rule | Behavior |
|------|----------|
| **D2 Half-turn** | Monster acts only when `(player_turn_count + ai_turn_salt) % 2 == 0`; otherwise skip the full AI visit |
| **D3 Memory cutoff** | Do not path toward `last_known_*`; visible targets and full explore BFS still apply; skip memory sanitize BFS while throttled |

When count **≤ N**, or monster is within R: full AI (including corner chase via `last_known_*`).

`ai_turn_salt` is 0 or 1, fixed for entity lifetime (set at spawn; saved; default 0 on old saves).

**Out of scope:** D1 simplified explore (no BFS beyond R); D5 stand-still beyond R.

---

## Requirement: Entity registry cache

`get_entity_registry()` SHALL return a cached default `entities.json` registry. `load_entity_registry()` without explicit path SHALL use the same cache.

---

## Requirement: Performance regression gates

Automated tests (`tests/test_performance_regression.py`) SHALL fail when headless turn time exceeds:

| Scenario | P95 limit |
|----------|-----------|
| `default` (seed 42) | 150 ms |
| `explore_10` (seed 42) | 100 ms |

Profiling harness: `tools/profile_turn.py`.

---

## Status

Hot-path (Group P) and distant throttle (D2/D3/D4) shipped — see archive `openspec/changes/archive/2026-07-08-fix-performance-ai-hotpath/`.
