# Investigation Report: Performance (Phase 1)

**Date:** 2026-07-05  
**Harness:** `tools/profile_turn.py` (Python `cProfile` + `time.perf_counter`)  
**Seed:** 42 (fixed per scenario)  
**Save I/O:** disabled (`save_coordinator=None`)

---

## Executive summary

Player-turn lag is **quantifiably caused by monster AI**, specifically **explore-path BFS** added/enhanced in `better-npc-exploration`. With the default ~10 NPCs spread across a dungeon floor, a single player turn takes **~460 ms** headless (median ~500 ms). Forcing explore-heavy behavior pushes that to **~5 s/turn**. This is not speculation — `run_monster_turns` accounts for **>99%** of world-phase time, and **`bfs_path_distances`** accounts for **>90%** of that in spread/explore scenarios.

**Not the bottleneck:** autosave (disabled in harness), FOV (~0.06 ms/update), `load_entity_registry` (~0.32 ms/call — negligible vs AI).

---

## Methodology

| Parameter | Value |
|-----------|-------|
| Warmup turns | 10 (discarded) |
| Measured turns | 5–30 per scenario (reduced for slow scenarios) |
| Actions profiled | `consume` (full `_consume_player_turn`), `world`, `monsters` |

Scenarios:

| ID | Setup |
|----|-------|
| `default` | Fresh `GameEngine()`, stock dungeon spawn (~10 NPCs) |
| `sparse` | All NPCs stashed to one distant tile (`isolate_other_ais`) |
| `isolated_1` | Exactly 1 wolf, others removed |
| `scale_N` | N wolves on carved open floor, spread on grid |
| `explore_10` | 10 wolves far from player, memory cleared → forced explore/wander |

---

## Wall-clock results (milliseconds per turn)

### Full player turn (`_consume_player_turn`)

| Scenario | NPCs | Iterations | Mean | Median | P95 | Max |
|----------|------|------------|------|--------|-----|-----|
| `default` | 10 | 30 | **461** | 496 | 572 | 577 |
| `sparse` | 10 | 30 | **17** | 17 | 18 | 19 |
| `isolated_1` | 1 | 30 | **86** | 94 | 104 | 106 |
| `scale_10` | 10 | 20 | **1264** | 2 | 4279 | 4749 |
| `scale_25` | 25 | 10 | **6611** | 6292 | 11863 | 11868 |
| `scale_50` | 50 | 5 | **5994** | 2027 | 2332 | **23528** |
| `explore_10` | 10 | 15 | **4819** | 4821 | 5120 | 5194 |

### Phase breakdown (`default`, 30 iterations)

| Action | Mean | Notes |
|--------|------|-------|
| `world` (`_run_world_turn`) | 465 ms | Monster turns + FOV |
| `monsters` (`run_monster_turns` only) | 511 ms | Same order of magnitude; FOV is negligible |

`_consume_player_turn` overhead outside `_run_world_turn` is **< 5%** of total turn time.

---

## Key findings

### 1. Spatial distribution matters more than raw NPC count (at default density)

| Condition | Turn time |
|-----------|-----------|
| 10 NPCs **stacked** on one tile (`sparse`) | ~17 ms |
| 10 NPCs **spread** on stock dungeon (`default`) | ~461 ms |
| 1 NPC **spread** on full map (`isolated_1`) | ~86 ms |

When NPCs are co-located, explore BFS runs once per stacked position and most visits are cheap. When spread, **each NPC runs full-map BFS** for explore goal picking, memory sanitization, and step resolution.

**Conclusion:** The lag is not "10 NPCs is too many" in the abstract — it is "10 NPCs each doing full-map BFS every turn."

### 2. Explore BFS is the dominant cost (quantified)

**`default` scenario — top cumulative functions (30 turns):**

| % of turn | Function | Calls / 30 turns |
|-----------|----------|------------------|
| 91.3% | `map_gen.bfs_path_distances` | 821 |
| 80.6% | `ai.entity_explore_can_traverse` | 1,431,869 |
| 62.8% | `ai.explore_reachable_distances` | 555 |
| 47.2% | `ai._sanitize_unreachable_memory_targets` | 408 |
| 30.2% | `ai.explore_distances_to_goal` | 266 |
| 24.3% | `ai._complete_explore_step` | 77 |

**`explore_10` scenario — top cumulative functions (15 turns):**

| % of turn | Function | Calls / 15 turns |
|-----------|----------|------------------|
| 97.5% | `map_gen.bfs_path_distances` | 1,110 |
| 53.9% | `ai.explore_reachable_distances` | 600 |
| 45.7% | `ai.explore_distances_to_goal` | 510 |
| 27.0% | `ai._sanitize_unreachable_memory_targets` | 300 |
| 26.9% | `ai._ensure_explore_goal` | 300 |

**`sparse` scenario — BFS absent from top 25.** Dominant cost is LOS/visibility (`_has_los`, `can_see`) at ~38%, total turn still only ~17 ms.

**Conclusion:** `better-npc-exploration` BFS paths (`explore_reachable_distances`, `explore_distances_to_goal`, `_sanitize_unreachable_memory_targets`) are the measured bottleneck. Multiple BFS passes occur **per monster per turn**.

### 3. NPC count scaling (open floor, spread wolves)

| NPCs | Mean turn | Observation |
|------|-----------|-------------|
| 10 | 1264 ms* | Bimodal: many ~2 ms turns, spikes to ~4–5 s when BFS repicks fire |
| 25 | 6611 ms | Consistently multi-second |
| 50 | 5994 ms | Max single turn **23.5 s** |

\*Open-floor `scale_10` differs from `default` (carved arena, all wolves, no dungeon walls) — shows worst-case explore on open terrain.

Rough scaling: **~0.5–6 s per turn at 10 spread NPCs**, **~6 s at 25**, with extreme spikes beyond that.

### 4. Ruled out (measured, not guessed)

| Suspect | Measured cost | Verdict |
|---------|---------------|---------|
| `load_entity_registry()` per turn | ~0.32 ms | **Not significant** |
| `update_fov()` | ~0.06 ms | **Not significant** |
| Autosave | Disabled in harness | **Excluded**; unlikely to explain 0.5–5 s turns |
| Message log / UI | Not in harness | Real play adds rendering; headless AI alone explains multi-second stalls |

---

## BFS call sites (for Phase 2 design)

These functions trigger full-map (or large-region) BFS and appeared in profiles:

1. **`explore_reachable_distances`** — goal picking (`_ensure_explore_goal`, `_pick_explore_goal_from_reachable`)
2. **`explore_distances_to_goal`** — per-step distance check (`_explore_path_distance_to_goal`, `_complete_explore_step`)
3. **`_sanitize_unreachable_memory_targets`** — called from `pick_evil_chase` / `pick_good_chase` **every monster visit**
4. **`_explore_reachable_including_closed_doors`** — second BFS when strict reachability is small

All funnel through **`map_gen.bfs_path_distances`** with **`entity_explore_can_traverse`** as the tile predicate (millions of calls per turn).

---

## Reproducing

```bash
# Full turn, default dungeon, with function breakdown
python tools/profile_turn.py --scenario default --action consume --iterations 30 --profile

# Control: stacked NPCs (fast)
python tools/profile_turn.py --scenario sparse --action consume --iterations 30 --profile

# Worst case: forced explore
python tools/profile_turn.py --scenario explore_10 --action consume --iterations 15 --profile
```

---

## Phase 2 inputs (not prescriptions)

Investigation confirms **where** time goes. Design should target:

1. **Reducing BFS invocations per monster per turn** (cache reachability, incremental invalidation, or cheaper distance checks for explore steps).
2. **Throttling distant NPCs** (todo spec) — evidence supports this: stacked/distant-skip scenarios are ~25× faster than spread full-AI.
3. **Avoiding repeated full-map BFS in `_sanitize_unreachable_memory_targets`** on every chase pick when memory is empty.

**Not supported by data as primary fix:** caching `load_entity_registry`, FOV changes, save-load optimization.

---

## Sign-off

- [x] User reviewed investigation report
- [x] Phase 2 design approved to proceed