# Design: Good NPC spawn quota

**Change id:** `good-npc-spawn-quota`

## Current behavior (baseline)

1. `compute_target_npc_count()` → density `target` for the floor.
2. `good_follower_reduction = min(len(followers), good_aligned_weight_at_depth(...))`.
3. `effective_target = max(0, target - good_follower_reduction)`.
4. `spawn_floor_population` draws **any** eligible alignment (good/evil/neutral) until `effective_target` is filled.

Goods are probabilistic. Followers only shrink total density budget.

## Target behavior

### Algorithm (per floor after player + followers are placed)

```
limit = difficulty.good_spawn_limit   # Easier 3; Normal/Hard/Nightmare 2
brought = count of good followers on this floor (same set already placed by descent)
eligible_goods = good-aligned definitions that pass depth/terrain/water eligibility
                 AND int(spawn.weight) > 0
                 AND a non-empty placement pool exists for their terrain

if eligible_goods is empty:
    good_to_spawn = 0                 # abandon; no infinite retry
elif brought >= limit:
    good_to_spawn = 0
else:
    good_to_spawn = limit - brought

# Placement pool for NEW goods only:
path_dist = BFS from player start, 8-dir, ground + closed doors walkable
good_tiles = spawn candidates with path_dist in [10, 15]

for i in 1..good_to_spawn:
    weighted pick among currently placeable eligible goods
    place only on good_tiles; remove tile from pool
    stop early if no placeable candidates remain

# Density pass (non-good only)
target = compute_target_npc_count(...)   # no follower reduction
spawn evil + neutral only until target (or attempts exhausted)
```

### New-good placement band (PR1 addendum)

| Rule | Value |
|------|--------|
| Metric | Player ground **path** steps (not Euclidean) |
| Directions | **8-way** (same as player movement) |
| Closed doors | Count as walkable steps (openable) |
| Items / runes | Do not affect path (tile geometry only) |
| Min steps | **10** (`GOOD_SPAWN_PATH_MIN`) |
| Max steps | **15** (`GOOD_SPAWN_PATH_MAX`) |
| Applies to | **Newly spawned** goods only (not descent followers) |
| Empty band | Place fewer goods; do not break the band |

### Eligibility “can any good spawn?”

Must be true **before** attempting the good pass:

- At least one **good** definition with `spawn.weight > 0`, depth window containing `floor_depth`, terrain rules satisfied for this map.
- After filtering by **available placement pools** (land candidates / water place pool), at least one definition still has a non-empty pool.

If goods exist in data but **no tiles** (e.g. water-only good on a dry map), treat as **cannot spawn** → `good_to_spawn = 0`.

### Weighted draws

Reuse existing `_weighted_choice` / `int(spawn.weight)` truncation. Draws are **independent** (same species may appear twice). Re-filter placeable list each draw so emptied terrain pools drop out.

### Cap semantics

| Brought goods | Limit 2 | New goods (if eligible) |
|---------------|---------|-------------------------|
| 0 | 2 | up to 2 |
| 1 | 2 | up to 1 |
| 2 | 2 | 0 |
| 3+ | 2 | 0 (`brought >= limit`) |

Same table with limit 3 on Easier.

**Who counts as “brought”:** the follower list already used for descent placement (good-aligned NPCs that followed). Do **not** re-scan for goods that somehow already exist mid-floor. Floor 1 / new game: `brought = 0`.

### Density interaction (resolved)

**Decision:** Good quota is a **separate guarantee pass**. Density `target` applies to **evil + neutral only**. Goods are **excluded** from the general weighted pool.

**Why not leave goods in density?**

- Quota already fills to `limit` when possible; extra random goods would break the cap.
- Leaving goods in the pool without a cap would reintroduce “allies all over the map.”

**Why not subtract goods from density target?**

- “Always spawn up to N goods” reads as a **reliable ally floor**, not as stealing hostile slots.
- Separating keeps density math simple and avoids double-counting followers.

**Obsolete:** `good_follower_reduction` and using `good_aligned_weight_at_depth` as a density cap. That helper MAY be removed or repurposed for “eligible good weight > 0” checks; prefer a clear `eligible_good_definitions(...)` helper.

**Net population:** floors with goods tend to have roughly `density_target + good_to_spawn` NPCs (slightly higher than today when goods used to consume density slots). Acceptable for ally reliability.

### Difficulty data

Add optional int on each difficulty profile in `data/depth_scaling.json`:

```json
"good_spawn_limit": 2
```

| Difficulty | Stock value |
|------------|-------------|
| easier | **3** |
| normal | **2** |
| hard | **2** |
| nightmare | **2** |

**Loader rules:**

- Type: int, **>= 0** (0 = never spawn new goods via quota).
- Omitted → default **2** (Normal baseline) so mods that whole-file-replace profiles without the key still behave sensibly.
- Wire through `DifficultyProfile` → `spawn_floor_population` / floor init via existing `difficulty_id`.

Not placed in `dungeon_spawn.json` (that file is density-only and not difficulty-keyed). Difficulty already owns spawn economy knobs (`density_multiplier`, freeze, prefixes).

### Placement

- Same candidate tiles as today (`valid_spawn_tiles`, water fallback pool).
- Prefer **not** to spawn on follower tiles (pools already exclude occupied tiles if spawn path removes/filters occupied — match existing occupation rules used by density spawn).
- Spawn order: **goods pass first**, then density pass, so goods claim tiles before hostiles fill the map. (Order is mostly fairness; document it.)

### Performance

- One eligibility scan for goods (O(species)); at most `limit` weighted draws (limit ≤ 3 stock).
- Density pass filters out goods once (list partition or alignment check in eligible builder). Negligible vs map gen.

### Save compatibility

- Additive optional JSON field; old saves unaffected (spawn is not stored as a formula).
- No save format bump.

### Mods

- Whole-file `depth_scaling.json` replace: mods should include `good_spawn_limit` or accept default 2.
- Entity mods that add goods automatically participate via alignment + weight + depth.

## Resolved decisions

| # | Decision | Choice |
|---|----------|--------|
| 1 | Cap check | `brought >= limit` → no new goods |
| 2 | No eligible goods | Spawn 0 goods; no retry loops |
| 3 | Stock limits | Easier 3; Normal/Hard/Nightmare 2 |
| 4 | Density pool | Evil + neutral only; goods excluded |
| 5 | Follower density reduction | Remove |
| 6 | Data home | `depth_scaling.json` per difficulty `good_spawn_limit` |
| 7 | Default if omitted | 2 |
| 8 | Duplicate species | Allowed (independent weighted draws) |
| 9 | Pass order | Goods quota first, then density |
| 10 | New-good path band | 10–15 player steps (8-dir, closed doors walkable) |
| 11 | Follower descent buff | Per-instance stack: +5 max/cur HP, +1 melee min/max, +1 ranged min/max, +0.03 accuracy; once per descend; not on archetype |

## Open questions

None blocking. Designer can override density interaction or Hard/Nightmare limits before PR1.

## Spec touchpoints (on land)

| Spec | Change |
|------|--------|
| `npc-data/spec.md` | Replace density+follower-deduction good rules with quota algorithm |
| `dungeon/spec.md` | Descent followers still place; spawn section points at quota not budget reduction |
| `balance/spec.md` | Document `good_spawn_limit` on difficulty profiles |
| `data/SCHEMA.md` | Field docs + defaults |

## Implementation sketch

| Area | Notes |
|------|--------|
| `src/data/depth_scaling_config.py` | `DifficultyProfile.good_spawn_limit: int = 2` |
| `src/data/depth_scaling_loader.py` | Parse/validate optional int ≥ 0 |
| `data/depth_scaling.json` | Set values per difficulty |
| `src/spawn.py` | `spawn_good_quota(...)`; partition eligible defs; drop `good_follower_reduction` from density path |
| `src/engine_floor.py` | Pass follower **count** (or list length) into spawn; stop computing weight-based reduction |
| Tests | Isolated fixtures: no goods depth; 0/1/2+/3 brought; Easier limit 3; goods absent from density-only draws |

## PR plan

| PR | Scope |
|----|--------|
| **PR1** | Data + loader + core spawn algorithm + unit tests + SCHEMA/spec updates |
| **PR2** | Manual playtest sign-off, checklist, archive (no full pytest unless requested) |
