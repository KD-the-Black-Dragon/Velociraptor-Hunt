# floor-runes Specification

## Purpose

**floor-runes** adds data-driven **permanent player progression** via step-on floor runes. Each floor spawns weighted-random runes from **`data/floor_runes.json`** after NPCs and items. The player absorbs a rune once by stepping on it; buffs persist for the run and compose with equipment via `effective_fighter()`.

**Terminology:** defeated, stunned, digested — no kill/die/death.

## Scope

### In scope

- `data/floor_runes.json` loader and frozen `FloorRuneRegistry`
- `FloorRune` entity component; `PlayerProgression` on player
- Placement: `runes_per_floor` from JSON (stock 3; `RUNES_PER_FLOOR` fallback) distinct tiles per floor, FLOOR-only, BFS path distance from entrance (macguffins reuse these helpers — see `macguffins` spec)
- NPC blocking (`BlocksMovement`); player passthrough onto rune tiles
- Step-on activation after item pickup on move; rune entity removed immediately
- One-frame localized screen flash (`RUNE_FLASH_RADIUS` around player)
- Effect types: `max_hp`, `accuracy`, `natural_ac`, `natural_evade`, `accuracy_damage`
- Descent preserves `PlayerProgression` and synced `Fighter.max_hp`

### Out of scope

- Rune inventory items or use-key activation
- NPC rune interaction
- Hot-reload mid-run
- Guaranteed specific rune types per floor

## Requirements

### Requirement: Rune catalog

The game SHALL load rune definitions from `data/floor_runes.json` at startup. Each rune SHALL have fields documented in `data/SCHEMA.md`. Glyph SHALL be exactly one character and MUST NOT be `#` (wall glyph). Stock data uses glyph **`0`** for all runes; **`fg`** color distinguishes effect type.

#### Scenario: Stock runes load

- GIVEN the shipped `floor_runes.json`
- WHEN the game starts
- THEN vitality, striking, ruin, and warding runes are available
- AND every stock rune has glyph `0`

### Requirement: Floor rune spawn

After `spawn_floor_population()` and `spawn_items()` on `new_game()` and `descend_floor()`, the game SHALL place **`runes_per_floor`** runes from `data/floor_runes.json` (stock: **3**; constant `RUNES_PER_FLOOR` is fallback when the field is omitted) on **distinct** tiles. Difficulty `runes_per_floor_override` SHALL win when set. Count **0** SHALL place no runes and SHALL not require eligible definitions.

Map generation feasibility and spread budget SHALL use the **same** count (plus macguffins) so placement and regen stay aligned.

Each rune SHALL be a weighted random draw among definitions where `min_depth ≤ floor_depth ≤ max_depth`.

Placement tile SHALL be:

- `FLOOR` only (not `STAIRS_DOWN`)
- Not `enter_xy`
- Not occupied by a `BlocksMovement` NPC entity (floor items do **not** block — player walks over them)
- **Every** rune: at least `MIN_PAIRWISE_SPREAD_BFS` (stock: **20**) BFS path steps from `enter_xy`; entrance distance SHALL NOT relax below 20
- First rune: prefer `RUNE_SPAWN_MIN_DISTANCE` (stock: **30**) from `enter_xy` when possible; MAY relax downward only to **20**
- Each subsequent rune: BFS ≥ **20** from **every** already-placed rune on `FLOOR` tiles; inter-rune distance SHALL NOT relax below 20
- No maximum distance from entrance

If placement cannot satisfy inter-rune spread after NPC/item spawn, floor initialization SHALL regenerate the map (see `dungeon` spec **Floor initialization loop**).

Spawn order: NPCs → items → runes → macguffins (`macguffins` spec). Runes exclude NPC tiles; macguffins additionally exclude rune tiles via cumulative `placed_positions`. Items remain valid candidates for rune placement.

#### Scenario: New game spawns stock runes_per_floor runes

- GIVEN a new game at depth 1 and stock `runes_per_floor: 3`
- WHEN floor initialization completes
- THEN exactly three floor rune entities exist
- AND each occupies a distinct tile

#### Scenario: Descent respawns runes

- GIVEN the player descends to a new floor and stock `runes_per_floor: 3`
- WHEN floor initialization completes
- THEN exactly three new floor runes exist on the new floor

#### Scenario: Zero runes_per_floor

- GIVEN `runes_per_floor: 0` (or difficulty override 0)
- WHEN a floor initializes
- THEN no floor rune entities exist

### Requirement: Player movement on rune tiles

NPCs SHALL NOT enter rune tiles (`BlocksMovement` on rune entity). The player SHALL be allowed to step onto a rune tile (movement passthrough exception).

#### Scenario: NPC blocked, player passes

- GIVEN a rune on a floor tile
- WHEN an NPC attempts to enter the tile
- THEN the move fails
- AND the player may move onto the tile

### Requirement: Step-on activation

After a successful player move and `pickup_all_items_at()`, the engine SHALL call `try_activate_floor_rune()` at the player's tile.

Activation SHALL apply only when the actor has the `Player` tag. Engulfed or stunned players cannot move onto tiles, so no special activation branch is required.

On activation:

1. `apply_rune_effect()` updates `PlayerProgression` (and syncs `Fighter.max_hp` / `hp` for `max_hp`)
2. Log message includes numeric bonus (e.g. *"+5 max HP"*)
3. `ScreenFlashState.pending` set for one localized flash tinted to rune `fg`
4. Rune entity cleared immediately

#### Scenario: Vitality rune increases HP

- GIVEN the player steps onto a vitality rune
- WHEN activation resolves
- THEN `PlayerProgression.bonus_max_hp` increases
- AND HUD max HP increases by the same amount
- AND current HP increases by the same amount (capped at new max)
- AND the rune entity is removed

#### Scenario: Rune cannot re-trigger

- GIVEN the player activated a rune
- WHEN the player remains on or returns to that tile
- THEN no second activation occurs

### Requirement: Permanent progression and combat

`PlayerProgression` SHALL hold authoritative permanent bonuses: `bonus_max_hp`, `bonus_accuracy`, `bonus_min_damage`, `bonus_max_damage`, `bonus_ac`.

`effective_fighter()` SHALL add progression bonuses to equipment-derived combat stats. Only `apply_rune_effect()` SHALL mutate `PlayerProgression` and sync `Fighter.max_hp` for HP effects.

#### Scenario: Bonuses persist after descent

- GIVEN the player absorbed a rune on floor 1
- WHEN the player descends to floor 2
- THEN progression bonuses remain
- AND combat uses the buffed stats

### Requirement: Status corner HUD

The status corner SHALL display permanent rune bonuses from `PlayerProgression` while the player has non-zero bonuses.

- `bonus_max_hp > 0` SHALL appear on its own row as `HP +N` in **green**.
- `bonus_accuracy > 0` SHALL appear on its own row as `Acc +value` in **yellow**.
- `bonus_min_damage` / `bonus_max_damage` SHALL appear on its own row as `Dam +N` (or `Dam +min-max` when unequal) in **red**.
- `bonus_ac > 0` SHALL appear on its own row as `AC +N` in **cyan**.
- Only non-zero bonuses are shown; each row is clipped to corner width.
- Rows SHALL appear after depth and ailment rows (stun, engulfed).

#### Scenario: Vitality rune shows HP row

- GIVEN the player absorbed a vitality rune (+5 max HP)
- WHEN the HUD renders
- THEN the status corner includes `HP +5` in green

#### Scenario: Combat runes show separate labeled rows

- GIVEN the player has accuracy and AC rune bonuses
- WHEN the HUD renders
- THEN the status corner includes `Acc +value` (yellow) and `AC +N` (cyan) on separate rows

### Requirement: Examine precedence

Floor runes SHALL expose `ExamineDescription`. Examine precedence: `Fighter` → `Item` → `ExamineDescription`. Co-tile exclusion at spawn prevents fighter/item overlap in normal play.

## Effect types (v1)

| `type` | Behavior |
|--------|----------|
| `max_hp` | `bonus_max_hp += amount`; sync `Fighter.max_hp` and heal by `amount` |
| `accuracy` | `bonus_accuracy += amount` |
| `natural_ac` | `bonus_ac += amount` |
| `natural_evade` | `bonus_evade += amount` |
| `accuracy_damage` | Adds to **separable** piece banks for each non-zero sub-field (`accuracy`, `min_damage`, `max_damage`) |

### Requirement: Piece / threshold progression

Each effect MAY declare `pieces_per_bonus` (default **1**) and `pieces_granted` (default **1**). Effective need for a bank is `pieces_per_bonus ×` run difficulty `rune_pieces_multiplier` (also ≥ 1).

`PlayerProgression` holds piece banks (`pieces_*`, `pieces_need_*`, sticky `*_need_frozen`). **Partial pieces never affect combat**; only completed `bonus_*` enter `effective_fighter()`.

- First grant freezes that bank’s `pieces_need_*` for the run.
- Status corner MAY show compact `AC +1 2/4` (completed + partial).
- Stock data uses defaults so behavior matches pre-piece runes.

#### Scenario: Four pieces for +1 AC

- GIVEN a warding effect with `pieces_per_bonus: 4`
- WHEN the player absorbs three wardings
- THEN `bonus_ac` is unchanged
- WHEN the player absorbs a fourth
- THEN `bonus_ac` increases by 1

#### Scenario: Damage-only accuracy_damage

- GIVEN `accuracy: 0`, `min_damage: 1`, `max_damage: 1`
- WHEN pieces progress
- THEN only min/max damage banks move (not the accuracy bank)

## Technical notes (non-normative)

- Loader: `src/data/floor_rune_loader.py`, registry: `src/data/floor_rune_registry.py`
- Systems: `src/systems/floor_runes.py`
- Constants: `RUNES_PER_FLOOR`, `RUNE_SPAWN_MIN_DISTANCE`, `RUNE_FLASH_RADIUS` in `src/constants.py`
- Tests: `tests/test_floor_runes_pr3.py`, `tests/test_floor_runes_pr4.py`, `tests/test_floor_runes_pieces_pr2.py`

## Related specs

| Spec | Relationship |
|------|----------------|
| `dungeon/spec.md` | Spawn order; floor init on descent |
| `macguffins/spec.md` | Shared BFS placement; spawn after runes |
| `inventory-items/spec.md` | `effective_fighter()` composes with equipment |
| `npc-data/spec.md` | Independent of NPC spawn density |

## Acceptance criteria

1. `runes_per_floor` (stock 3) runes per floor on distinct exploratory tiles; glyph `0`, color by effect.
2. Player step-on activates once; NPCs blocked; log shows numeric bonus; brief local flash.
3. HP and combat buffs persist across floors.
4. `tests/test_floor_runes_pr3.py` and `tests/test_floor_runes_pr4.py` green.