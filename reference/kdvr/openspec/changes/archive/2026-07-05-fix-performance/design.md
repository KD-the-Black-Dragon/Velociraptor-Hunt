# Design: Fix Performance

## Design philosophy

Measure first, fix second. Every optimization traces to `investigation-report.md`. **Tier A** changes are behavior-preserving (same decisions, fewer redundant computations). **Tier B** changes trade NPC intelligence for speed — each option is documented so you can choose what to keep and what to lose.

---

## Goals (user priorities)

| Priority | Goal |
|----------|------|
| **1** | Preserve current AI behavior while eliminating noticeable turn lag |
| **2** | If (1) is not achievable, reduce lag as much as possible |
| **3** | Any intelligence reduction must be **explicit and choosable** — not accidental |

### “Player won't notice” — acceptance targets

Turn-based roguelikes tolerate more latency than action games, but investigation showed **461 ms mean / 572 ms p95** headless per turn on a default floor — far above comfortable.

| Metric | Today (`default`) | Tier A target | Tier A + chosen Tier B |
|--------|-------------------|---------------|------------------------|
| Mean turn (headless) | 461 ms | **< 100 ms** | **< 50 ms** |
| P95 turn (headless) | 572 ms | **< 150 ms** | **< 100 ms** |
| `explore_10` mean | 4819 ms | **< 800 ms** | **< 300 ms** |

Headless timings exclude TCOD render; real play will be slightly higher. Hitting Tier A targets on `default` should make typical dungeon play feel instant; worst-case explore packs may still need a Tier B choice.

**Regression gate:** `tools/profile_turn.py` run before/after each PR; no scenario may regress vs previous PR.

---

## Root cause (recap)

Per monster, per turn, explore AI runs **multiple full-map BFS passes**:

```
pick_evil_chase / pick_good_chase
  └─ _sanitize_unreachable_memory_targets → explore_reachable_distances (BFS #1)

_ensure_explore_goal (when wandering)
  └─ explore_reachable_distances (BFS #2, often same origin)

_complete_explore_step (each explore move)
  └─ _explore_path_distance_to_goal → explore_distances_to_goal (BFS #3–5)

_target_blocked_only_by_closed_door (memory clear)
  └─ explore_reachable_distances + _explore_reachable_including_closed_doors (BFS #6–7)
```

Investigation: **~27 BFS calls per player turn** with 10 spread NPCs; **~2.7 per monster visit**. Stacked NPCs (`sparse`) drop to **17 ms** because redundant work collapses.

---

## Tier A — Behavior-preserving optimizations (implement first)

**Player-visible behavior:** identical decisions, same goals, same movement, same memory/door-spite rules. Only redundant work is eliminated.

### A1. Per-visit reachability memo (high impact)

**Problem:** `explore_reachable_distances` called ~2× per monster visit (sanitize + ensure_goal + door checks).

**Fix:** Thread a `ExploreBfsCache` through `run_monster_turns` → `_run_monster_visit` → chase/explore helpers.

```python
@dataclass
class ExploreBfsCache:
    reachable_by_key: dict[tuple[int, int, int, str], dict[Position, int]]  # (ox, oy, entity_id, mobility_key)
    goal_distances_by_key: dict[tuple[int, int, int, str], dict[Position, int]]  # (gx, gy, entity_id, mobility_key)
```

- `reachable_from(origin, entity)` — compute once per visit, reuse for sanitize, ensure_goal, door-spite check.
- Cache key includes mobility + hands (terrain predicate inputs). **Not** saved across turns (map static within world phase; doors opened on prior player turn are already in `game_map`).

**Estimated impact:** ~40–50% BFS reduction on `default`.

### A2. Explore goal-distance episode cache (high impact)

**Problem:** `_explore_path_distance_to_goal` runs `explore_distances_to_goal` (full BFS from goal) up to **3× per explore step** — 266 BFS-weighted calls in 30 default turns.

**Fix:** When `_begin_explore_goal_episode` sets `explore_goal`, compute `explore_distances_to_goal` **once** and store on `AIState`:

```python
explore_goal_distance_map: dict[Position, int] | None = None  # ephemeral, not saved
```

- `_explore_path_distance_to_goal` → `state.explore_goal_distance_map.get(origin)` (O(1)).
- Invalidate when `explore_goal` changes, on frustration repick, on `_explore_oscillation_repick`.
- Omit from save snapshot (recomputed lazily on load if needed).

**Estimated impact:** ~30–35% BFS reduction on `default`; largest win on `explore_10`.

### A3. Sanitize early exit (medium impact)

**Problem:** `_sanitize_unreachable_memory_targets` always runs BFS even when all four `last_known_*` fields are `None` (common when not chasing).

**Fix:** Return immediately when no memory targets are set.

**Estimated impact:** ~10–20% BFS reduction (depends on how many NPCs carry memory each turn).

### A4. Hoist per-entity predicate in BFS (medium impact, constant-factor)

**Problem:** `entity_explore_can_traverse` called **1.4M×** per 30 turns — re-reads `entity_mobility` and `Abilities` per tile.

**Fix:** Build a closure once per BFS:

```python
mobility = entity_mobility(entity)
has_hands = _entity_has_hands_ability(entity)
def can_traverse(x, y): ...
```

**Estimated impact:** No change to BFS call count; expect **1.5–2× faster per BFS** (constant factor).

### A5. Door-spite reachability reuse (low–medium impact)

**Problem:** `_target_blocked_only_by_closed_door` runs strict BFS + optional second BFS including closed doors.

**Fix:** Reuse A1 reachable cache for strict check; only run door-inclusive BFS when strict fails **and** a memory target needs door-spite evaluation.

**Estimated impact:** Small on `default`; helps door-adjacent wolf packs.

### A6. Minor per-turn overhead (low impact — include if cheap)

| Fix | Cost today | Action |
|-----|------------|--------|
| `load_entity_registry()` every turn | ~0.32 ms | Module-level cache (correctness unchanged) |
| Duplicate `load_entity_registry` import in `engine.py` | noise | Clean up |

Not a substitute for A1–A4; bundle into first implementation PR.

### Tier A realistic outcome

| Scenario | Today | Tier A estimate |
|----------|-------|-----------------|
| `default` | 461 ms mean | **80–150 ms** |
| `sparse` | 17 ms | **10–15 ms** (already fast) |
| `explore_10` | 4819 ms | **600–1200 ms** (still slow) |

**Shipped outcome (PR2+PR3):** `default` **77 ms** mean / **92 ms** p95; `explore_10` **231 ms** mean. Acceptance targets met.

---

## Tier B — deferred

Distant NPC throttling (B2–B5, B1 last resort) moved to:

`openspec/changes/deferred-fix-performance-distant-throttle/`

Deferred 2026-07-05 after Tier A met targets; user playtest sign-off PR2–PR3.

*(Tier B design preserved in deferred module — not repeated here.)*

---

## Shipped implementation (PR2–PR3)

- `src/systems/ai.py` — `ExploreBfsCache`, goal-distance episode cache, sanitize early exit
- `src/components.py` — ephemeral `explore_goal_distance_map` on `AIState`
- `src/data/entity_loader.py` — `get_entity_registry()` cache
- `tools/profile_turn.py` — profiling harness
- `tests/test_performance_regression.py` — p95 gates

---

## Resolved decisions

| # | Decision |
|---|----------|
| 1 | Tier A shipped; behavior preserved |
| 2 | Tier B deferred to `deferred-fix-performance-distant-throttle` |
| 3 | `explore_goal_distance_map` not in save snapshot |
| 4 | Live spec: `openspec/specs/performance/spec.md` |

---

## Phase 1 — Investigation methodology

*(Unchanged — see git history or `investigation-report.md`.)*