# Design: Dungeon Enhancement

## Proposed architecture

```text
map_gen.py
  ├─ Tile enum + tile_props (walkable_by, transparent, glyph)
  ├─ generate_dungeon() — mixed carve + water + stairs + validate
  └─ validate_land_connectivity() — BFS from enter_xy; stairs reachability

components.py
  └─ Mobility(GROUND | FLY | AQUATIC)

engine.py
  ├─ floor_depth: int  (starts 1; cap 1000)
  ├─ new_game()        → depth 1, full reset
  ├─ descend_floor()   → depth++, regen map, respawn, keep player state
  └─ handle Shift+PERIOD on STAIRS_DOWN tile → descend_floor()

movement.py / ai.py / combat.py / vore.py / spawn.py / fov.py / render.py
  └─ consult Mobility + tile_props instead of Tile.FLOOR-only checks
```

**Descent key (`>`):** `KeyDown` with `Modifier.SHIFT` + `KeySym.PERIOD`, handled on any tile:

```text
if Engulfed:     no-op, no turn, log "Going deeper won't help you here!"
elif not on STAIRS_DOWN: no-op, no turn, log "There are no stairs here."
else:            descend_floor() — new map, depth++, good allies follow, respawn
```

**Stairs co-tile:** downstairs is a **tile flag**, not a blocking entity. Creatures and items may occupy the same tile as `>`; rendering draws `>` under or instead of floor glyph (design: render stairs glyph when tile is `STAIRS_DOWN`, entity glyph on top).

## Resolved decisions

| Topic | Decision |
|-------|----------|
| Land connectivity | Single global `FLOOR` (+ `STAIRS_DOWN`) component reachable from `enter_xy`; reject/regen on failure |
| Water role | Lakes, ponds, rivers in coherent shapes; may force detours; never isolates land |
| Water type | **Deep water only** — impassable to `GROUND`, transparent (FOV passes) |
| Water presence | Probabilistic per floor; when generated, features should be at least ~**5×5** tiles |
| Room variety | Chaotic mix: rectangular rooms, organic caves (CA/drunkard), wide (2–3) and narrow (1) corridors |
| Player mobility | Always **`GROUND`** in v1; future flight potion deferred |
| Flyer rules | Cross land **and** water; still **one creature per tile**; block/swap unchanged |
| Aquatic movement | **Water only**; never enter land tiles |
| Aquatic combat | **Shore bump** — melee from adjacent water tile to land target (and water↔water as normal adjacent) |
| Vore initiation | Adjacent regardless of target tile; predator does not leave its tile |
| Vore escape | Water escape tile valid only if prey is `AQUATIC` or `FLY`; walls, creatures, impassable terrain invalid; existing adjacent-then-random-nearby fallback preserved |
| Stairs down count | **Three** per floor, random land placement, each reachable from entrance |
| Descend input | **`Shift+.`** (`>`) on any tile; **`.`** unshifted remains **wait** (DCSS) |
| `>` while engulfed | **No-op**, no turn, log *"Going deeper won't help you here!"* (any tile) |
| `>` not on stairs | **No-op**, no turn, log *"There are no stairs here."* |
| `>` on stairs, not engulfed | Descend |
| Stairs up | **Out of scope** — descent only |
| Floor depth | Starts **1** on New Game; increment on descend; cap **1000** |
| Depth HUD | Show current depth on HUD (placement provisional until HUD redesign) |
| Descent state | Preserve player HP, inventory, name, prefs; fresh map clears vore/engulfed (descent impossible while engulfed anyway) |
| Good allies on descend | Any **Good** NPC with **LOS to player** at descent time **follows**: entity preserved, placed on new floor **as close as possible** to `enter_xy` (nearest valid land tiles; adjacency not required if blocked). **Neutral** and **evil** NPCs do not follow. Following knights are **not** re-spawned again on the new floor (deduct from fresh knight spawn count or skip duplicate spawns). |
| Debug **R** | **Unchanged** — still calls `new_game()` (resets depth to 1); do not special-case |
| Shark | Aquatic evil predator placeholder; **2** spawn in random water tiles if floor has any `DEEP_WATER`; skip aquatic spawns if no water |
| Existing spawns | Wolves/knights/rabbits/potions unchanged (land-only candidates) |
| Difficulty / loot | **Deferred** — depth tracked only for future modules |
| Regen attempts | Cap e.g. **50** seed retries; deterministic fallback chamber if all fail |

### Connectivity validation

```text
generate attempt
  carve land + water + 3 stairs
  land_tiles = FLOOR | STAIRS_DOWN
  BFS(enter_xy) over land_tiles → count == |land_tiles|?
  for each stair: stair in BFS visited?
  if fail → retry with new seed offset
```

Water tiles are **not** part of the land BFS. Rivers/lakes sit inside or beside land without partitioning it.

### Map generation (sketch)

1. **Base land** — roll per-region style: rect room, blob room (random walk fill), or cavern (cellular automata); connect with 1–3 wide L/tunnel paths.
2. **Water pass** (probabilistic) — pick 0–N feature sites in large enclosed floor areas; flood-fill **lake** blobs (min ~5×5); carve **river** paths between lakes or from lake to room interior using biased random walk / A* on floor tiles, then paint `DEEP_WATER`.
3. **Stairs** — choose 3 random floor tiles from BFS-reachable set (not `enter_xy`); mark `STAIRS_DOWN`.
4. **Validate** — land component + stair reachability; else regen.

### Good ally follow (descent)

```text
before clearing world:
  followers = [e for e in Good NPCs if can_see(player, e)]
descend_floor():
  snapshot follower components (Fighter, Stunned, etc.)
  regen map + spawn evil/neutral/potions/sharks
  place player at enter_xy
  for each follower: nearest-free-tile BFS from enter_xy (mobility-aware, exclude player)
  spawn remaining knights up to (SPAWN_KNIGHT_COUNT - len(followers))
```

Engulfed good NPCs are excluded (not in a valid follow state). Predators holding prey are excluded or prey released — **exclude engulfed prey and holding predators** from follow set.

## Mobility matrix

| Tile | GROUND | FLY | AQUATIC |
|------|--------|-----|---------|
| WALL | no | no | no |
| FLOOR | yes | yes | no |
| DEEP_WATER | no | yes | yes |
| STAIRS_DOWN | yes | yes | no |

`STAIRS_DOWN` is traversable like floor for ground/fly; aquatic creatures do not use stairs (cannot enter land).

## Shark placeholder (v1)

| Field | Value |
|-------|-------|
| Display name | shark |
| Glyph | `s` (CP437-safe) |
| Alignment | evil |
| Mobility | AQUATIC |
| HP / power / defense | TBD constants (~wolf-tier) |
| Vore | `VoreCapable` + OV/CV/AV narratives (placeholder, same as wolf) |
| Digestion | `DigestionStats(damage_per_tick=3)` |
| Spawn | 2 tiles in `DEEP_WATER`, away from player if possible |

## PR plan

| PR | Scope |
|----|--------|
| 1 | Tile model, `Mobility` component, mobility-aware movement/FOV/render; player `GROUND` |
| 2 | Mixed map gen, shaped water, connectivity regen, three downstairs, `enter_xy` |
| 3 | `floor_depth`, descend on `>`, engulfed block, good-ally follow, HUD depth |
| 4 | Aquatic shore combat, mobility-aware AI/pathing, shark spawn, vore escape mobility |
| 5 | Spec acceptance, `core-roguelike`/`vore` updates, README, archive |

## Code touchpoints

| Area | File(s) |
|------|---------|
| Tiles / generation | `src/map_gen.py` |
| Mobility component | `src/components.py` |
| Movement | `src/systems/movement.py` |
| FOV | `src/systems/fov.py` |
| Render | `src/systems/render.py` |
| AI / pathing | `src/systems/ai.py` |
| Combat bump | `src/systems/combat.py` |
| Vore escape | `src/systems/vore.py` |
| Spawn | `src/spawn.py` |
| Engine / depth | `src/engine.py` |
| Descend key | `src/input_handlers.py`, `src/engine.py` |
| Constants | `src/constants.py` |
| HUD depth | `src/systems/render.py` |

## Supersedes

- `core-roguelike` single-floor map requirement → multi-floor with depth
- `GameMap.is_walkable()` naive floor check → mobility-aware traversal API