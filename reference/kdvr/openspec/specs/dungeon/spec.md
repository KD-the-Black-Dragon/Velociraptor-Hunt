# dungeon Specification

## Purpose

The **dungeon** domain extends the core roguelike map with **varied procedural layouts**, **deep water**, **creature mobility** (ground / fly / aquatic), **guaranteed land connectivity**, **multi-floor descent**, and **floor depth tracking** for future spawn and loot modules.

Builds on `core-roguelike`. Map logic lives in `src/map_gen.py`; mobility in ECS components; descent in `src/engine.py`.

**Terminology:** defeated, stunned, digested — no kill/die/death.

## Requirements

### Requirement: Tile Types

The map SHALL support at least these static tile types:

| Tile | Movement (ground) | FOV |
|------|-------------------|-----|
| `WALL` | blocked | blocked |
| `FLOOR` | walkable | transparent |
| `DEEP_WATER` | blocked for ground | transparent |
| `STAIRS_DOWN` | walkable (like floor) | transparent |
| `DOOR_CLOSED` | blocked | blocked |
| `DOOR_OPEN` | walkable (like floor) | transparent |

Deep water SHALL be impassable to **ground** creatures. Deep water SHALL NOT block line of sight.

#### Scenario: Ground cannot enter deep water

- GIVEN a ground creature adjacent to a deep water tile
- WHEN it attempts to move into the water
- THEN the move fails
- AND a short message explains the water is impassable (optional log line)

#### Scenario: FOV passes through deep water

- GIVEN a wall does not block the line
- AND deep water lies between observer and target floor tiles
- WHEN field of view is computed
- THEN the target remains visible if the algorithm would otherwise see it

### Requirement: Creature Mobility

Each mobile entity SHALL have a **mobility** classification:

- **`GROUND`** — may traverse `FLOOR` and `STAIRS_DOWN` only
- **`FLY`** — may traverse `FLOOR`, `DEEP_WATER`, and `STAIRS_DOWN`; still subject to one-entity-per-tile blocking and swap rules
- **`AQUATIC`** — may traverse `DEEP_WATER` only; SHALL NOT enter land tiles
- **`STATIONARY`** — may **occupy** the same land tiles as `GROUND` at spawn, but SHALL NOT take voluntary movement steps (explore, chase, flee, erratic drift). May still bump-attack adjacent targets, use ranged abilities, vore, and summons. Knockback may relocate a stationary entity.

The player SHALL be **`GROUND`** in v1.

#### Scenario: Stationary turret holds position

- GIVEN an evil NPC with mobility `stationary` on a floor tile
- AND a visible player two tiles away
- WHEN the NPC acts
- THEN it does not change tile for chase or explore
- AND it may still attack when the player is adjacent or shoot when a ranged ability has line of sight

#### Scenario: Flyer crosses water

- GIVEN a flying creature on floor adjacent to deep water
- WHEN it moves into the water tile
- THEN the move succeeds if the tile is unoccupied

#### Scenario: Aquatic cannot enter land

- GIVEN an aquatic creature in deep water adjacent to floor
- WHEN it attempts to move onto the floor
- THEN the move fails

### Requirement: Aquatic Shore Combat

Aquatic creatures SHALL NOT move onto land. Aquatic creatures MAY perform **bump melee attacks** against targets on **adjacent** land tiles (orthogonally or diagonally adjacent), using the same bump-combat resolution as land creatures.

#### Scenario: Shark attacks knight on shore

- GIVEN a shark in deep water
- AND a knight on an adjacent floor tile
- WHEN the shark's AI chooses to attack the knight
- THEN the knight may take damage
- AND the shark remains on the water tile

### Requirement: Layout archetypes

Dungeon generation SHALL select a whole-floor **layout archetype** per floor:

| Archetype | Weight (default) |
|-----------|------------------|
| Boxy | 40% |
| Organic | 40% |
| Hybrid | 20% |

Debug **F4** cycles forced 100% boxy / organic / hybrid for QA. Depth does not affect archetype weights.

#### Scenario: Distinct silhouettes

- GIVEN floors generated with debug force modes
- WHEN the player explores
- THEN boxy floors read as rect rooms and varied corridors
- AND organic floors read as large open caverns with narrow choke connectors

### Requirement: Chaotic Mixed Map Generation

Dungeon generation SHALL produce varied floor silhouettes via the **layout archetype** system (boxy rect rooms, organic caverns, hybrid mixes) with corridors from approximately 1–3 tiles wide.

Generation SHALL be bounded by the map rectangle and SHALL produce at least one connected land region before water is applied.

#### Scenario: New floor has varied layout

- GIVEN a newly generated dungeon floor
- WHEN the player explores
- THEN both open areas and corridor-like passages exist
- AND the layout is not exclusively uniform rectangles with uniform 1-wide tunnels

### Requirement: Shaped Deep Water Features

Deep water SHALL appear as **coherent features** — lakes, ponds, or rivers — not as scattered isolated water tiles. Water placement SHALL be **probabilistic** per floor. When a water feature is generated, it SHALL occupy at least approximately **5×5** tiles.

Water features MAY force **detours** along land routes but SHALL NOT partition land into unreachable components.

#### Scenario: Water feature has shape

- GIVEN a generated floor that includes deep water
- WHEN the water tiles are examined
- THEN they form at least one contiguous body or river-like path
- AND the body has at least 5×5 tiles

### Requirement: Map sanity regeneration

Generation SHALL reject and retry (up to `MAX_GEN_ATTEMPTS`, stock **50**) maps that fail any of:

- Land tile count below `MIN_LAND_TILE_COUNT` (stock **400**)
- Spawn candidates below `MIN_SPAWN_CANDIDATE_COUNT` (stock **30**)
- Disconnected land after layout, water, or doors
- Stairs unreachable or fewer than three placed
- Pairwise stair BFS distance below `MIN_PAIRWISE_SPREAD_BFS` (stock **20**)
- Fewer than three feasible rune-site tiles pairwise BFS ≥ 20 (geometry only, before entities)

Discard reasons SHALL be logged to stdout as `[map_gen] rejected attempt N: reason`. After all attempts fail, the generator SHALL fall back to one **giant inset room** with spread stairs.

### Requirement: Land Connectivity Validation

After generation, every **land** tile (`FLOOR`, `STAIRS_DOWN`, and `DOOR_OPEN`; `DOOR_CLOSED` counts as connected for topology because the player can open doors) SHALL belong to a **single connected component** reachable from the dungeon entrance (`enter_xy`) via cardinal/diagonal steps.

If validation fails, the generator SHALL **reject** the map and **regenerate** (with a bounded retry count and safe fallback).

#### Scenario: No isolated land

- GIVEN a generated dungeon floor
- WHEN land connectivity is checked from `enter_xy`
- THEN every land tile is reachable
- AND no enclosed unreachable floor exists

### Requirement: Downstairs Placement

Each generated floor SHALL place exactly **three** downstairs tiles (`STAIRS_DOWN`, rendered as `>`). Each downstairs tile SHALL be on land and SHALL be reachable from `enter_xy` via land tiles.

Pairwise BFS path distance between any two downstairs tiles SHALL be at least `MIN_PAIRWISE_SPREAD_BFS` (stock **20**) on land tiles. Placement SHALL use spread-aware selection, not uniform random sampling.

Downstairs tiles SHALL allow **co-occupancy**: creatures and items MAY stand on the same tile as a downstairs marker.

#### Scenario: Three reachable stairs

- GIVEN a generated dungeon floor
- WHEN downstairs tiles are counted
- THEN there are exactly three
- AND each is reachable from the entrance over land

### Requirement: Doors

Procedural generation SHALL place **closed** doors (`+` glyph) at valid **1-wide corridor mouths** at approximately 55% of candidates per floor (normal distribution clipped to 25–75%). Open doors (`-`) are walkable and transparent; closed doors block movement and FOV for all entities.

The **player** MAY open a closed door by walking into it (turn consumed, player stays on the near tile) and MAY close an adjacent open door with **`c`** then direction (8-way). NPCs SHALL NOT open or close doors.

#### Scenario: Player opens and closes a door

- GIVEN a closed door on an adjacent tile
- WHEN the player walks into it
- THEN the door opens, the turn is consumed, and the player does not enter the door tile
- WHEN the player presses `c` toward the open door with nothing blocking it
- THEN the door closes and the turn is consumed

### Requirement: Background floor prefetch

While the player is on the main menu or exploring a floor, the game SHALL prefetch the **next** floor's map geometry (`generate_dungeon` only) on a **background worker process** so gameplay input is not blocked by Python GIL contention during generation retries.

Prefetch SHALL start when entering the main menu and after each successful floor load (anticipating the next descent). Debug **F3** / **F4** toggles and return-to-menu SHALL cancel stale prefetch jobs.

Consuming a prefetched map (`new_game`, `descend_floor`, debug **R**) SHALL use the cached `GameMap` when generation parameters match; otherwise the engine SHALL fall back to synchronous generation without soft-locking.

Entity spawn, rune placement, and FOV init remain on the main thread after the map is adopted.

#### Scenario: Gameplay stays responsive during prefetch

- GIVEN the player is exploring a floor
- AND a background prefetch is generating the next floor (including reject-and-retry)
- WHEN the player moves
- THEN input remains responsive (no multi-second hitch from prefetch work)

### Requirement: Floor initialization loop

`new_game()`, `descend_floor()`, and debug **R** SHALL use a unified floor initialization path that:

1. Generates a validated map
2. Spawns the player (and descent followers when applicable), NPCs, and items
3. Places floor runes with inter-rune spread per `floor-runes` spec
4. On `RunePlacementError`, logs `[floor_init] rejected attempt N: rune_placement_failed` and regenerates (up to `MAX_GEN_ATTEMPTS`)
5. Falls back to best-effort placement with a warning if all attempts fail

#### Scenario: Rune failure triggers regen

- GIVEN rune placement would fail on a generated floor after entity spawn
- WHEN floor initialization runs
- THEN a new map is generated
- AND the player is not soft-locked

### Requirement: Floor Depth and Descent

The engine SHALL track **`floor_depth`**, starting at **1** on **New Game**. The player MAY descend without limit in v1 up to a cap of **1000**.

Pressing **`Shift+.`** (`>`) while unshifted **`.`** remains the **wait** action (DCSS-style binding). The `>` key SHALL be handled globally during gameplay (any tile). Resolution order:

1. If the player is **engulfed** — **no-op**, **no turn consumed**, log *"Going deeper won't help you here!"* (regardless of tile).
2. Else if the player is **not** on a `STAIRS_DOWN` tile — **no-op**, **no turn consumed**, log *"There are no stairs here."*
3. Else — **descend** (see below).

Successful descent SHALL:

- Increment `floor_depth` by 1 (unless at cap)
- Generate a **new** dungeon floor
- **Transfer** qualifying **Good** allies (see below) to the new floor near the player
- Respawn remaining monsters and items per current spawn rules (followers are not duplicated)
- Preserve player **HP**, **inventory** (slots, durability, charges, stack counts), **wielded/worn equip pointers**, **display name**, and **vore content prefs**
- Place the player at the new floor's `enter_xy`

**Stairs up** and returning to prior floor layouts are out of scope.

Debug key **R** behavior SHALL remain unchanged (full `new_game` reset including depth to 1).

#### Scenario: Descend from stairs

- GIVEN the player stands on a downstairs tile at depth 3
- WHEN the player presses `Shift+.`
- THEN a new floor generates
- AND `floor_depth` becomes 4
- AND the player appears at the new entrance

#### Scenario: Wait key unchanged

- GIVEN the player presses unshifted `.`
- WHEN no other handler consumes the key
- THEN the player waits (passes a turn)
- AND does not descend

#### Scenario: New game starts at depth 1

- GIVEN the player starts a new game from the main menu
- WHEN the first dungeon floor loads
- THEN `floor_depth` is 1

#### Scenario: Engulfed player cannot descend

- GIVEN the player is engulfed
- WHEN the player presses `Shift+.`
- THEN no new floor is generated
- AND no turn is consumed
- AND the message log reports *"Going deeper won't help you here!"*

#### Scenario: No stairs at current tile

- GIVEN the player is not engulfed
- AND the player is not on a downstairs tile
- WHEN the player presses `Shift+.`
- THEN no new floor is generated
- AND no turn is consumed
- AND the message log reports *"There are no stairs here."*

### Requirement: Good Allies Follow on Descent

When the player successfully descends, every **Good**-aligned NPC that had **line of sight to the player** at the moment of descent SHALL **follow** to the new floor. The engine SHALL preserve each follower's state (e.g. HP, stunned) and place them on the **nearest valid land tiles** to the new floor's entrance (`enter_xy`). Adjacency to the player is preferred but not required when tiles are blocked or space is constrained.

**Neutral** and **evil** NPCs SHALL NOT follow. Engulfed NPCs (prey inside a predator) SHALL NOT follow.

Fresh spawns on the new floor SHALL reduce the **total NPC target** by the number of good followers (capped at the sum of eligible good-aligned spawn weights at this depth), so followers are not duplicated as extra spawns. See `openspec/specs/npc-data/spec.md`.

#### Scenario: Visible knight follows downstairs

- GIVEN a knight with line of sight to the player
- AND the player descends from a downstairs tile
- WHEN the new floor loads
- THEN the knight appears on the new floor
- AND the knight is placed as close to the entrance as valid tiles allow

#### Scenario: Off-screen knight stays behind

- GIVEN a knight without line of sight to the player
- WHEN the player descends
- THEN that knight does not appear on the new floor

#### Scenario: Rabbit does not follow

- GIVEN a neutral rabbit with line of sight to the player
- WHEN the player descends
- THEN the rabbit does not appear on the new floor

### Requirement: Floor Depth Display

The HUD SHALL display the current **floor depth** during gameplay. Exact layout is provisional until a future HUD module.

#### Scenario: HUD shows depth

- GIVEN an in-progress game at depth 7
- WHEN the HUD renders
- THEN depth 7 is visible to the player

### Requirement: Density-driven floor population

NPC count per floor SHALL be driven by **`data/dungeon_spawn.json`**, not by the sum of `entities.json` spawn weights.

On `new_game()` and `descend_floor()` only:

1. Count valid spawn tiles (distance-filtered land + water candidates)
2. Resolve density band for `floor_depth` and compute `target` with variance (`compute_target_npc_count()`)
3. Apply `effective_target = max(0, target - good_follower_reduction)` (see `npc-data` spec)
4. Perform `effective_target` independent weighted draws from eligible `entities.json` definitions (unified land + water pool)
5. Place each draw on a random valid tile for its terrain; reject and retry when a terrain pool is empty

Aquatic NPCs compete for the same `effective_target` slots as land NPCs — sharks are **not** guaranteed on water floors. When no deep water exists, aquatic definitions with `spawn_requires_water` SHALL NOT be eligible.

Floor items SHALL spawn from item JSON per `inventory-items` spec. Floor runes SHALL spawn after items per `floor-runes` spec.

#### Scenario: Population scales with map size

- GIVEN two generated floors at the same depth with different valid spawn tile counts
- WHEN NPCs spawn with the same RNG seed for density variance
- THEN the floor with more valid tiles tends toward a higher NPC count

#### Scenario: Deeper band increases density

- GIVEN `dungeon_spawn.json` depth bands
- WHEN comparing median NPC targets at depth 1 vs depth 10
- THEN depth 10 uses a higher `density_pct` band

#### Scenario: Aquatic draws require water map

- GIVEN a floor with no deep water
- WHEN monsters spawn
- THEN no aquatic NPCs appear

#### Scenario: One-time spawn per floor

- GIVEN an in-progress floor
- WHEN monsters are defeated during play
- THEN no mid-level respawn occurs

### Requirement: Vore and Escape With Mobility

Vore initiation SHALL remain **adjacent** regardless of the target's underlying tile (predator does not move onto the target's tile to begin vore).

When resolving engulf escape placement, a **deep water** tile SHALL be a valid escape destination only if the prey entity is **`AQUATIC`** or **`FLY`**. For **`GROUND`** prey, water tiles SHALL be invalid escape destinations.

Invalid escape destinations (walls, occupied tiles, impassable terrain for the prey) SHALL retain the existing fallback: try intended direction, then adjacent valid tiles, then random nearby valid tile.

#### Scenario: Ground prey cannot escape into water

- GIVEN a ground player engulfed
- AND the chosen escape direction is deep water
- WHEN escape resolves
- THEN the player is not placed on the water tile
- AND fallback placement rules apply

#### Scenario: Aquatic prey may escape into water

- GIVEN an aquatic prey engulfed (future or NPC)
- AND an adjacent deep water tile is free
- WHEN escape succeeds toward that tile
- THEN the prey may be placed on the water tile

## Out of Scope (this module)

- Classic XP / character levels
- Loot value scaling by depth
- Stairs up / ascending to previous floors
- Shallow water
- Player flight or swim items
- Mid-level monster respawn
- Guaranteed per-species spawn quotas

## Supersedes

| Spec | Change |
|------|--------|
| `core-roguelike/spec.md` | Single floor → multi-floor descent; procedural map variety; tile types beyond wall/floor |
| `vore/spec.md` | Escape validity uses prey mobility for water tiles |
| `enhancements-3/spec.md` | Aquatic predators; Good allies may follow player on descent |
| `npc-data/spec.md` | Density-driven spawn; species-agnostic follower deduction |
| `floor-runes/spec.md` | Floor rune spawn after items; step-on progression |

## Acceptance Criteria

1. Maps mix room/cavern/corridor styles; water appears as shaped features when rolled.
2. All land reachable from entrance; three reachable downstairs per floor.
3. Ground blocked by water; FOV passes water; flyers cross water; aquatic water-only with shore attacks.
4. `Shift+.` (`>`): engulfed → *"Going deeper won't help you here!"*; off stairs → *"There are no stairs here."*; on stairs → descend; `.` still waits; HUD shows depth.
5. Good allies in LOS follow downstairs near entrance; neutrals/evil do not.
6. NPC count density-driven from `dungeon_spawn.json`; no fixed 6/5/6/2 parity; aquatic NPCs probabilistic on water floors.
7. Three floor runes per floor; pairwise BFS ≥ 20 between runes; floor items do not block rune candidates; step-on activation per `floor-runes` spec.
8. Doors at corridor mouths; player open/close; NPCs blocked by closed doors.
9. Layout archetypes (boxy / organic / hybrid); map sanity regeneration with debug logging.
10. Background floor prefetch on menu + post-floor; process-isolated worker; sync fallback on miss.
11. Vore escape respects mobility for water tiles.
12. Full `pytest tests/` green; prior acceptance tests still pass.