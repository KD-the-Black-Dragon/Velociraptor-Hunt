# Cost / benefit review (selected package 2026-07-08)

**Baseline (post Tier A, re-profile 2026-07-08, headless seed 42):**

| Scenario | Mean | P95 |
|----------|------|-----|
| `default` (variable 16–30 NPCs) | 55–180 ms | 102–287 ms |
| `explore_10` | ~221 ms | ~255 ms |
| `explore_25` | ~540 ms | ~560 ms |
| `scale_25` | ~340 ms | ~565 ms |
| `scale_50` | ~514 ms | ~1140 ms |

**After PR1 Group P (same machine, seed 42):**

| Scenario | Mean | P95 |
|----------|------|-----|
| `default` (30 NPCs) | **~71 ms** | **~144 ms** |
| `explore_10` | **~14 ms** | **~24 ms** |
| `explore_25` | **~43 ms** | **~43 ms** |
| `scale_25` | **~35 ms** | **~66 ms** |

Post-PR1 profile: BFS no longer dominates; visibility / query iteration is the new top cost.

---

## Selected

### P1 — Walkability grid

| Cost | Benefit |
|------|---------|
| Build mask(s) once per turn / mobility key | **High** — profile shows tile predicate ~50–65% of explore time |

### P2 — Ensure-goal short-circuit

| Cost | Benefit |
|------|---------|
| None intentional | **Medium–high** on sustained explore episodes |

### P3 — Array BFS

| Cost | Benefit |
|------|---------|
| Slightly more code complexity | **Low–medium** constant-factor + less GC |

### P4 — Sanitize once + interval

| Cost | Benefit |
|------|---------|
| Up to K−1 turns delay clearing dead memory | **Medium** on chase-heavy dense floors |

### D2 — Half-turn (busy ∧ distant)

| Cost | Benefit |
|------|---------|
| Distant NPCs at ½ action rate when busy | **~half** of distant visit cost |

### D3 — Memory cutoff (busy ∧ distant)

| Cost | Benefit |
|------|---------|
| No far-map corner chase from memory when busy | Saves sanitize + memory path BFS for throttled NPCs |

### D4 — Busy gate

| Cost | Benefit |
|------|---------|
| None when ≤N NPCs | Protects sparse floors from any D\* behavior change |

---

## Not selected (backlog)

| ID | Notes |
|----|-------|
| D1 simplified explore | Largest remaining distant BFS cut if targets miss |
| D5 stand-still | Last resort |
| G1–G4 global cuts | Only if P+D insufficient |

---

## Expected outcome

| After | Expectation |
|-------|-------------|
| PR1 only | Large cut on explore scenarios; default better; may still miss “always snappy” at 25+ |
| PR1+PR2 | Distant busy visits ~½ rate; less memory BFS far away; near-player full fidelity |

If `explore_25` remains &gt; 250 ms mean after PR1+PR2, discuss **D1** with user before acceptance.
