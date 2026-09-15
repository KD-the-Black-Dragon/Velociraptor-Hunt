# Design: Better NPC Exploration

## Resolved decisions

### Round 1 (2026-07-04)

| # | Decision |
|---|----------|
| 1 | **Defer** until `fix-deferred-bugfixes` completes — do not bundle into PR10/PR11 |
| 2 | **Explore/wander only** — no pathfinding rewrite for visible chase, follow, flee, or memory pursuit |
| 3 | **Closed doors** remain NPC-hard-blocks by default; player-only door open unchanged today |
| 4 | Explore frustration band: **8–12** failed steps (align with memory chase `CHASE_FRUSTRATION_*`) |
| 5 | Reachability: **BFS** from NPC position over mobility-passable tiles; walls + closed doors block (unless `hands`) |
| 6 | Reachable BFS goals apply to **all alignments** in explore/wander — not neutral-only |
| 7 | **Retire PR10 shim** (`recent_positions`, wait-on-recent) in PR4 — no temporary hacks |
| 8 | Prefer **re-pick reachable goal** over **full stop** when explore is blocked |

### Round 2 (2026-07-04 — design review with user)

| # | Decision |
|---|----------|
| 9 | **Paradigm B — “Far landmark”:** BFS reachable goals + **BFS one-step** movement for explore only; **greedy steps unchanged** for visible chase / follow / flee / memory |
| 10 | Goal pick: **weighted random** toward farther reachable tiles (any reachable tile remains possible) |
| 11 | On explore frustration re-pick: **force farthest-endpoint goal once** (tile(s) at maximum BFS distance from current position within reachable set), then resume weighted-random far picks |
| 12 | Blocked explore turn: **sidestep** if any legal move exists, even when it does not progress toward goal; only **stand still** when zero legal moves |
| 13 | **Drop PR3 door-bias / “prefer behind”** — far goals + BFS explore steps replace it |
| 14 | **Neutral explore:** treat **player tile only** as blocked for goal pick and step selection (may path onto player-adjacent tiles) |
| 15 | **Hands ability (future):** traversability predicate is per-entity; default NPCs cannot pass closed doors; stub path for rare `"hands"` entities (actual open-on-step behavior is a **future module**) |
| 16 | **Aquatic NPCs:** same rules using aquatic passable tiles |
| 17 | Wolves **may linger at a closed door** during frustration — narrative “growl at the door” is intended, not a bug |
| 18 | **Playtest fix (2026-07-05):** memory pursuit frustration must count **no progress** toward last-known (not only zero-move); otherwise wolves shuffle in open rooms forever without reaching explore |
| 19 | **PR3:** explore uses **BFS one-step** + sidestep away from goal; **4-step oscillation** (position or path-distance ABAB) triggers immediate opposite-goal re-pick |
| 20 | **Evil–evil swap disabled** — bump attacks instead; prevents pack ping-pong at doors |
| 21 | **Door spite counter** — unreachable quarry memory still **clears immediately**; when only a **closed door** blocked the path, start `door_spite_turns_left` (8–12) and **stand still** (no memory chase, no explore) until it expires, then explore |
| 22 | **Explore pathing** treats other NPC-occupied tiles as blocked (plan around allies) |
| 23 | **Explore idle:** 20% chance per explore turn to wait (no move); **never** during pursuit/chase |

---

## Design philosophy

Explore is **idle wandering after prey is lost**, not a robot march. Evil wolves at a slammed door should **stack and fail to pass** for several turns (frustration band), then **re-pick a distant landmark** and **drift back into the dungeon**. Rear wolves should **resume moving promptly** when space exists; the pack should **unwind from the back** over a reasonable number of turns.

Visible quarry chase stays **greedy** — if they can see it, charging is correct.

---

## Problem statement (playtest)

### Pack dispersal (PR9)

**Scenario:** Large wolf pack chases player down a corridor; player closes door and waits.

**Observed:**

- Wolves remain clustered at the door far longer than expected.
- Rear wolves blocked by front wolves; only back of pack can move backward slowly.
- After chase give-up (PR9 frustration), wolves still face the door — explore goal may lie **beyond** the door.
- Front wolves keep greedy-stepping toward unreachable goals; no re-pick on repeated failure.

**Expected:**

- After chase ends, wolves **linger at the door** briefly, then **pick reachable far goals** and wander off.
- Once any gap opens, pack unwinds single-file: rearmost wolf moves within 1–2 turns; cascade until front clears.

### Neutral clustering (PR10 shim)

**Scenario:** Neutral rabbits explore with no evil in sight; player walks nearby.

**Observed after PR10:**

- Two-tile ping-pong is gone.
- Rabbits remain in **small constrained regions** (greedy steps + globally random unreachable goals).
- **Wait-on-recent** can cause a **full stop** when the player is adjacent.

**Expected:**

- Explore goals from **BFS-reachable** tiles; explore frustration + re-pick; no wait shim.
- Rabbits do not stall near the player (player + adjacent blocked).

---

## Current implementation (baseline)

| Piece | Location | Behavior |
|-------|----------|----------|
| Explore goal pick | `_pick_random_walkable_tile()` | Random tile with passable **terrain**; ignores connectivity |
| Goal retention | `_ensure_explore_goal()` | Keeps goal until reached or tile type invalid |
| Step choice | `_choose_chase_direction()` | Greedy: legal adjacent tile minimizing Euclidean distance² |
| Doors (NPC) | `can_enter_tile` | `DOOR_CLOSED` not traversable; NPCs cannot open |
| Chase give-up | PR9 `chase_frustration` | Memory reach + momentum only — not explore |
| Neutral anti-oscillation (shim) | PR10 `recent_positions` + wait | Neutral explore only; **retired in PR4** |

---

## Explore paradigm B (target behavior)

### Goal pick (PR1 + PR2)

```text
reachable = BFS(origin, entity_traversability_predicate)
candidates = reachable - {origin}

# Normal pick (PR1):
goal = weighted_random(candidates, weight = bfs_distance_from_origin)

# Frustration re-pick (PR2) — once per frustration event:
goal = random_among(tiles_with_max_bfs_distance_from_origin)

# Ongoing picks after forced endpoint:
resume weighted_random far picks
```

- `_ensure_explore_goal()`: if current goal ∉ reachable, re-pick immediately (e.g. door closed).
- **Hands stub:** `entity_can_traverse_tile(entity, x, y)` — today equals `can_enter_tile`; future `hands` may treat `DOOR_CLOSED` as passable for BFS only.

### Explore step (PR3)

For explore/wander steps only (not chase/follow/flee/memory):

```text
1. Compute BFS path distances from origin to explore_goal over traversable tiles.
2. Among legal adjacent steps (respecting blocked_tiles, swaps, mobility):
   prefer the tile with lowest path distance to goal (one step on shortest route).
3. If no step reduces path distance (ally/door block):
   sidestep — any legal adjacent move (deterministic tie-break / rng among legal).
4. If zero legal moves: stand still (counts as failed explore step in PR2).
```

Chase pipeline continues to use `_choose_chase_direction()` (greedy).

### Explore frustration (PR2)

`AIState` fields:

```python
explore_frustration: int = 0
explore_frustration_limit: int = 0  # rng.randint(8, 12) per goal episode
explore_force_farthest_on_repick: bool = False  # or equivalent one-shot flag
```

Rules (explore episodes only):

- **Failed step:** no move, **or** moved but BFS path distance to goal did not decrease.
- **Success:** moved and path distance decreased → reset frustration to 0.
- **Frustration ≥ limit:** clear goal, reset limit, set one-shot farthest-endpoint pick, then PR1/PR2 re-pick.
- Sidestep without progress **counts as failed** (growling / pacing at door).

Do **not** apply explore frustration during memory chase or combat chase.

### Neutral player avoidance (PR4)

When neutral NPC is in explore (not fleeing):

- Add **player position** to `blocked_tiles` for goal pick and explore step selection (same as `_forbidden_tiles`; adjacent tiles remain valid).

---

## PR plan

| PR | Scope |
|----|-------|
| **PR1** | BFS reachable helper; weighted-random far goal pick; hands traversability stub; re-pick on unreachable goal; all alignments |
| **PR2** | `explore_frustration` counters; farthest-endpoint once on frustration re-pick |
| **PR3** | Explore-only BFS one-step toward goal; sidestep fallback when no progress |
| **PR4** | Remove PR10 shim; neutrals on shared explore path; neutral player-adjacent avoidance |

PR order: PR1 → PR2 → PR3 → PR4 → Acceptance.

---

## PR1 — Reachable explore goals

### Tests

- Wolf separated from room by closed door: goal never on far side of door.
- Weighted pick: farther tiles sampled more often (statistical or seeded fixture).
- Open door: goals on connected side remain valid.
- Aquatic entity: goals only on aquatic-reachable tiles.

---

## PR2 — Explore frustration

### Tests

- Blocked turns increment frustration; progress resets.
- At limit: goal cleared, next pick is farthest endpoint.
- Following picks resume weighted-random far selection.

---

## PR3 — BFS explore steps + sidestep

### Tests

- L-corridor: explore step follows shortest route, not greedy wrong branch.
- Blocked toward goal: sidestep taken when legal move exists.
- Zero legal moves: stand still; frustration increments.
- Chase/follow still use greedy (regression).

---

## PR4 — Retire PR10 shim + neutral avoidance

- Remove `recent_positions`, `_choose_neutral_explore_direction`, `_on_neutral_explore_moved`, wait-on-recent.
- Neutral explore uses PR1–PR3 path.
- Replace `tests/test_neutral_explore_antistuck.py` with reachable-goal / frustration / BFS-step coverage.
- Rabbit near player: no stall (player + adjacent blocked).

---

## Risk assessment

| Approach | Risk | In this module? |
|----------|------|-----------------|
| BFS reachable + weighted far goals | Low–medium | PR1 |
| Explore frustration + farthest re-pick | Low | PR2 |
| BFS one-step explore only | Low–medium | PR3 |
| Sidestep when blocked | Low | PR3 |
| Global pathfinding for all AI | **High** | **No** |
| Door-bias / prefer-behind heuristics | Medium (corner failures) | **No — dropped** |

---

## Manual acceptance scenario

1. Spawn/drive large evil pack down corridor toward player.
2. Player closes door in wolf faces; wait many turns.
3. **Pass:**
   - Wolves **linger at door** during frustration band (growl phase).
   - Rearmost wolf moves within **1–2 turns** once space exists behind.
   - Pack clears corridor within **~frustration band × pack depth** turns (reasonable, not lockstep).
   - Front wolves stop staring indefinitely after frustration re-pick.
4. **Regression:** pursuit momentum, neutral flee, good follow, player door open, combat unchanged.
5. **Neutral:** rabbits wander broader reachable areas; no freeze when player is adjacent.

---

## Related work

| Change | Relationship |
|--------|----------------|
| `fix-deferred-bugfixes` PR9 | Memory chase frustration + momentum — keep |
| `fix-deferred-bugfixes` PR10 | Shim — **superseded by PR1–PR4** |
| `fix-deferred-bugfixes` PR11 | Good–neutral swap — orthogonal |
| Future `hands` module | Door open on step for flagged entities |
| `todo` Performance | Separate module |