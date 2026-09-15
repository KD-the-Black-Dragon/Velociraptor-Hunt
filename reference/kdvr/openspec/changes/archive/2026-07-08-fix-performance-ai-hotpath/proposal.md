# Proposal: AI Hot-Path Performance (P + distant throttle)

**Status:** Active — user selected option package 2026-07-08.

**Revived from:** `deferred-fix-performance-distant-throttle` (split from `fix-performance` 2026-07-05).

**Source:** `openspec/changes/todo/spec.md` — performance distant throttle; fresh profile 2026-07-08.

## Why

Tier A (BFS visit/episode caching) shipped and helped, but busy floors remain laggy. Fresh headless profile (seed 42):

| Scenario | Mean | P95 |
|----------|------|-----|
| `default` (16–30 NPCs) | 55–180 ms | 102–287 ms |
| `explore_25` | ~540 ms | ~560 ms |
| `scale_25` | ~340 ms | ~565 ms |

Hot path is still full-map explore BFS (`explore_reachable_distances` / `bfs_path_distances`) plus per-tile `can_enter_tile` cost. User playtest: NPC AI performance still unacceptable.

## Selected package (user 2026-07-08)

| Group | IDs | Summary |
|-------|-----|---------|
| **P** (intelligence-preserving) | P1–P4 | Walkability grids, skip redundant ensure-goal BFS, array BFS, sanitize once-per-visit / rate-limit |
| **D** (distant, busy-gated) | D2, D3, D4 | Half-turn cadence + memory pursuit cutoff beyond R, only when NPC count > N |

## Explicitly out of scope

| ID | Why |
|----|-----|
| **D1 / B3** | Simplified explore (no BFS) beyond R — not accepted |
| **D5 / B1** | Stand-still beyond R — last resort only, not accepted |
| **G\*** | Global intelligence cuts (BFS radius cap, round-robin, density nerf) — not accepted |
| **B6** | Vore message cap — rejected earlier |

## What players may notice (D only)

On **busy** floors (**> N** NPCs, default 15):

- NPCs **beyond R** (Chebyshev from player, default 22) act on **half-turn cadence** (D2).
- Beyond R: no pathing to `last_known_*` memory (D3). **Within R: full corner chase preserved.**

On floors with **≤ N** NPCs: no D\* behavior change (D4 gate off).

Group P: no intentional AI decision changes.

## Success targets (headless, seed 42)

| Metric | Current (approx) | Target |
|--------|------------------|--------|
| `default` p95 | up to ~287 ms | **&lt; 100 ms** |
| `explore_10` mean | ~221 ms | **&lt; 120 ms** |
| `explore_25` mean | ~540 ms | **&lt; 250 ms** |
| `scale_25` p95 | ~565 ms | **&lt; 200 ms** |

If targets miss after this package, revisit D1 or G\* with user — do not add silently.

## Full design

`design.md`, `tasks.md`, `review.md` in this folder.
