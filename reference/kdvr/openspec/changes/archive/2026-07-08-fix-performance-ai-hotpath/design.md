# Design: AI Hot-Path Performance (P + D2/D3/D4)

## Context

**Parent investigation:** `openspec/changes/archive/2026-07-05-fix-performance/investigation-report.md`

**Tier A shipped:** `ExploreBfsCache`, goal-distance episode cache, sanitize empty early-exit, hoisted BFS predicates.

**Fresh profile (2026-07-08):** Still BFS-bound. On `explore_25`, ~90% of turn is `explore_reachable_distances` → `bfs_path_distances` → millions of `can_enter_tile` / `tile_at` calls. On dense `default`, `_sanitize_unreachable_memory_targets` is a large share when memory is set. Spawn density allows up to **30** NPCs (`data/dungeon_spawn.json` `max_npcs`).

**This change:** Group **P** (behavior-preserving hot-path) + distant throttles **D2, D3** gated by **D4**. No D1 (simplified explore), no D5 (stand-still).

---

## Terminology: “distant”

**Distant** = Chebyshev distance from **player position** > **R** tiles (default **22**).

**Not:** TCOD viewport, FOV, or LOS.

**Within R:** full AI always — corner chase via `last_known_*`, door spite, vore, rescue, full explore BFS.

**Beyond R (and only when busy — D4):** D2 + D3 apply.

---

## Constants

| Constant | Default | Meaning |
|----------|---------|---------|
| `DISTANT_AI_RADIUS` (R) | 22 | Chebyshev radius; beyond = distant |
| `BUSY_FLOOR_NPC_THRESHOLD` (N) | 15 | Active AI NPC count must exceed N for D\* |
| `MEMORY_SANITIZE_INTERVAL` (K) | 2 | P4: sanitize full BFS at most every K player turns per NPC when memory set (see P4) |

Place R, N, K in `src/constants.py` (or existing performance/AI constants module if one is preferred — match codebase style).

**Active NPC count for D4:** entities with `AI` + `Position`, excluding player, excluding those that would not take an AI action visit for other reasons is *not* required — use the same set as `_sorted_monsters` length (or count of AI+Position non-player). Compute **once** at start of `run_monster_turns`.

---

## Group P — Intelligence-preserving

### P1 — Walkability grid for explore BFS

**Problem:** Profile shows `can_enter_tile` / `tile_at` / enum overhead dominate BFS wall time.

**Fix:** Once per `run_monster_turns` (or once per distinct mobility/hands key when first needed), build a compact passable mask for explore terrain:

- Key: `(mobility, has_hands)` matching explore predicate semantics (open tiles + closed doors if hands).
- Grid: `bool` or `uint8` array `MAP_HEIGHT × MAP_WIDTH` (or flat length `W*H`).
- BFS reads mask only — no per-tile `Tile()` / component lookups.

**Semantics:** Identical to current `entity_explore_can_traverse` / hoisted closure for static map during the world phase. Doors opened mid-phase by player already applied before monster turns; monster turns do not open doors for others mid-phase in a way that invalidates explore masks (confirm: if any mid-phase door change exists, invalidate masks — expected: none).

**API sketch:**

```text
ExploreWalkabilityCache
  get_mask(game_map, mobility, has_hands) -> ndarray or list[bool]
bfs_path_distances_masked(origin, mask, cardinal_only=False) -> ...
```

Integrate into `_compute_explore_reachable_distances` and door-inclusive variant as needed.

### P2 — Skip reachable BFS when explore goal still valid

**Problem:** `_ensure_explore_goal` always calls `explore_reachable_distances` even when `state.explore_goal` is set and the episode distance map already proves reachability.

**Fix:**

```text
if state.explore_goal is not None and goal != origin:
    if state.explore_goal_distance_map is not None and origin in state.explore_goal_distance_map:
        return state.explore_goal  # still path-reachable under last episode BFS
# else: full reachable BFS + pick / begin episode
```

**Edge cases:**

- Goal cleared / frustration / oscillation repick → existing paths already clear distance map; full BFS on next ensure.
- Map change that would invalidate distance map without clearing goal: world phase assumes static terrain; no extra invalidation.
- Neutral filter (`_filter_reachable_for_neutral_explore`): if episode was begun under filter, goal already filtered; if player moved onto goal tile mid-episode, existing step completion handles arrival.

**Semantics:** Same goals chosen; fewer BFS when mid-episode.

### P3 — Array BFS + fewer allocations

**Problem:** `dict[tuple[int,int], int]` + conversion to `dict[Position, int]` allocates heavily.

**Fix (within explore path only unless shared helper is clean):**

- BFS over flat or 2D distance array (`-1` = unvisited).
- Convert to `Position` dict **only** when a caller needs the full reachable map (goal pick weights).
- Prefer returning distance array + width for internal step checks when P2 already uses goal distance map.

Do **not** change 8-directional vs cardinal rules.

**Compatibility:** Public helpers used by tests (`explore_reachable_distances`, `explore_distances_to_goal`) may keep `dict[Position, int]` return type; internal path may use arrays.

### P4 — Sanitize once per visit + interval

**Problem:** `_sanitize_unreachable_memory_targets` can run multiple times per monster visit (e.g. multi-step plan re-entering `pick_*_chase`) and every turn while memory is held — full BFS each time.

**Fix (two layers):**

1. **Once per visit (behavior-preserving):** Thread a flag or use `ExploreBfsCache` visit-scoped “sanitize already done” so multiple `pick_evil_chase` / `pick_good_chase` in one visit share one sanitize.
2. **Interval K (micro delay):** When memory fields are set, run full sanitize BFS only if `player_turn_count % K == entity_stable_bucket` or `turns_since_last_sanitize >= K` stored ephemerally on `AIState` (not saved — on load, sanitize next visit). Default **K = 2**.

**Within R / busy off:** P4 still applies (engineering). Interval does **not** skip clearing when memory is cleared by other systems.

**Visible effect of K=2:** At most one extra turn before an unreachable memory waypoint is dropped. Acceptable micro-delay; document in spec.

If once-per-visit alone is enough in profile after P1–P3, still ship interval only if it remains hot — **prefer implementing both as designed** unless tests prove interval harmful.

---

## Group D — Distant throttles (busy-gated)

### D4 — Busy-floor gate

```text
busy = (active_npc_count > N)
distant(monster) = chebyshev(monster.pos, player.pos) > R
throttle = busy and distant(monster)
```

When `not throttle`: full AI (plus Group P always).

### D2 — Half-turn cadence (when throttle)

Beyond R on busy floors: monster acts only when:

```text
(player_turn_count + stable_entity_salt(monster)) % 2 == 0
```

`stable_entity_salt`: deterministic from entity identity stable for the run (e.g. `id` is unstable across sessions — prefer hash of species+spawn position if available, or component that persists; if nothing better, use sorted-monster index is wrong across deaths — use `id(monster)` only for ephemeral stagger within session, **or** hash of `(Position at spawn)` — simplest acceptable: `hash((pos.x, pos.y, species_id)) % 2` recomputed each visit is **bad** (moves change salt). **Required:** salt fixed for entity lifetime.

**Implementation:** Store `ai_turn_salt: int` on `AIState` at spawn (0 or 1 from rng or hash of entity key), include in save if `AIState` is saved — check save schema. If `AIState` already snapshots, add field with default 0 for old saves.

**Skip behavior:** Entire action visit skipped (no move, no chase pick, no explore BFS). Still process:

- Engulfed prey digestion (already separate branch before normal AI)
- Stunned / Predator holding branches unchanged (those `continue` before throttle)

Apply D2 check **after** engulfed/stunned/predator early branches, **before** expensive `_run_monster_visit` / intent pipeline.

### D3 — Memory pursuit cutoff (when throttle)

When `throttle`:

- Do **not** path toward `last_known_primary` / `last_known_neutral` / `last_known_evil` / `last_known_player`.
- Still update memory when targets are **visible** (normal LOS updates).
- Visible entity targets unchanged.
- Explore: **full BFS explore remains** (D1 not selected) — fall through to `_ensure_explore_goal` as today when no visible target.
- Optionally still run sanitize on interval (P4) so memory does not grow stale forever; or skip sanitize when throttle to save BFS — **prefer skip sanitize BFS when throttle** (memory unused for pursuit until within R again; within R next time sanitize runs).

**Within R:** full memory pursuit mandatory (including around corners).

### Interaction matrix

| Condition | D2 half-turn | D3 no memory path | Explore BFS |
|-----------|--------------|-------------------|-------------|
| count ≤ N | off | off | full |
| count > N, within R | off | off | full |
| count > N, beyond R, act turn | on (acts) | on (no memory path) | full |
| count > N, beyond R, skip turn | skip visit | n/a | none |

---

## Implementation touch points

| Area | Files |
|------|--------|
| Constants R, N, K | `src/constants.py` |
| Walkability cache + array BFS | `src/map_gen.py` and/or `src/systems/ai.py` |
| P2 ensure-goal short-circuit | `src/systems/ai.py` `_ensure_explore_goal` |
| P4 sanitize gate | `src/systems/ai.py` `_sanitize_unreachable_memory_targets`, visit flag |
| D2/D3/D4 | `src/systems/ai.py` `run_monster_turns` / chase pickers |
| AIState salt + last sanitize turn | `src/components.py`; save/load if AIState persisted |
| Tests | new `tests/test_performance_distant_throttle.py`, extend explore/chase tests; regression gates |
| Spec | `openspec/specs/performance/spec.md` |

---

## PR plan

### PR1 — Group P (behavior-preserving)

1. P1 walkability grid + wire explore BFS  
2. P3 array BFS internals  
3. P2 ensure-goal short-circuit  
4. P4 once-per-visit sanitize + interval K  
5. Targeted tests: explore/chase parity where practical; no intentional decision change  
6. Profile before/after PR1; note numbers in PR checklist  

**Does not** change distant behavior.

### PR2 — D2 + D3 + D4

1. Constants R, N; `ai_turn_salt` on spawn  
2. Busy count once per `run_monster_turns`  
3. D2 skip visit when throttle and wrong cadence  
4. D3 suppress memory pos targets when throttle  
5. Tests: within-R corner chase; beyond-R no memory path when busy; busy gate off at ≤N; half-turn stagger  
6. Update `openspec/specs/performance/spec.md`  

### PR3 — Acceptance

1. Full profile table vs targets  
2. Manual playtest checklist  
3. Tighten regression gates if warranted  
4. Archive change; update `AGENTS.md` pointer + `todo/spec.md`  

---

## Testing strategy

| Layer | What |
|-------|------|
| Unit | Throttle predicate (busy × distant); half-turn salt; memory cutoff returns explore/visible only |
| Regression | Existing explore + chase suite must pass after P |
| Performance | `tools/profile_turn.py` scenarios `default`, `explore_10`, `explore_25`, `scale_25` |
| Manual | Busy floor lag feel; corner chase near player; distant half-speed when crowded; quiet floor unchanged |

---

## Resolved decisions

| # | Decision |
|---|----------|
| 1 | Distant = Chebyshev > R from player; not FOV |
| 2 | Within R: full memory corner chase mandatory |
| 3 | Selected: **P1–P4 + D2 + D3 + D4** (2026-07-08) |
| 4 | **Not** selected: D1 simplified explore, D5 stand-still, all G\* |
| 5 | D2+D3 apply only when busy (D4); P always on |
| 6 | D3 without D1: fall through to **full** explore BFS, not random step |
| 7 | When throttle: skip sanitize BFS (memory not used for pursuit) |
| 8 | `ai_turn_salt` fixed per entity lifetime; default 0 for old saves |
| 9 | Success targets in `proposal.md`; miss → discuss D1/G with user |

---

## Risks

| Risk | Mitigation |
|------|------------|
| Without D1, explore BFS still dominates distant act-turns | P1–P3 + D2 (half the distant visits); re-profile; D1 backlog |
| Half-turn feels wrong near fog edge | R=22 ≈ beyond typical engagement; tune R if playtest complains |
| P4 interval delays door-spite from unreachable memory | K=2 only; door spite within engagement range usually has LOS/memory refresh |
| Save compatibility | New AIState fields defaulted |
