# npc-data Specification

## Purpose

**npc-data** externalizes NPC species definitions to **`data/entities.json`**. Alignment profiles in code derive faction behavior (evil vore, good follow, neutral flee). Spawn uses a **weight-based pool** with depth, terrain, and water gates. Combat uses **accuracy / evade / ac / damage range** from data.

**Terminology:** defeated, stunned, digested — no kill/die/death.

## Scope

### In scope

- `data/entities.json` loader and frozen `EntityRegistry`
- Alignment profiles (`good` / `evil` / `neutral`) — not repeated per entity
- `spawn_from_definition()` and `spawn_floor_population()`
- Combat hit check and damage range formulas
- Evil `vore_narratives`, `digestion_complete`, `digestion_player_modal`, optional `digest_time` keyed by entity `id`
- Ignore-unknown traits and abilities (warn once per session)
- Item JSON files — see `openspec/specs/inventory-items/spec.md` for gameplay wiring

### Out of scope
- Hot-reload mid-run
- Item `abilities[]` in weapon/armor JSON (see `inventory-items` spec)
- XP from `experience_points` (stored silently)

**NPC `abilities[]` runtime behavior** is specified in `openspec/specs/npc-abilities/spec.md`.

## Requirements

### Requirement: Entity data file

The game SHALL load NPC definitions from `data/entities.json` at startup. Each entity SHALL have the required traits documented in `data/SCHEMA.md`. Invalid required fields or bad enums SHALL fail load with a clear error.

#### Scenario: Stock four species load

- GIVEN the shipped `entities.json`
- WHEN the game starts
- THEN wolf, knight, rabbit, and shark definitions are available
- AND shark has `spawn.terrain` `water` and `spawn_requires_water` true

### Requirement: Optional placeholder marker

Entity definitions MAY include `"placeholder": true` (default false when omitted). The loader SHALL parse it into `EntityDefinition.placeholder` without treating it as an unknown trait. Placeholder status SHALL **not** change combat, AI, spawn eligibility, or vore systems — it is a content-authoring marker for unfinished species (see `data/SCHEMA.md` **Placeholder content checklist**). Stock shipped species need not set the field.

Stock roster growth (themed placeholders, mid/deep cast, and **good-aligned allies**) lives in `data/entities.json`; deprecated species SHALL use `spawn.weight: 0` rather than deleting ids when old saves may reference them (e.g. `giant_spider`).

Stock **good** allies are multi-species (not knight-only): staggered depth bands with rising rank titles (squire → knight → guard → warrior → warden → at-arms → champion), plus parallel specialist tracks (e.g. Path crossbow, Smite cleric). Good definitions use cyan presentation, non-empty `introduction` lines, and `names.json` pools keyed by entity id.

#### Scenario: Placeholder flag loads

- GIVEN a fixture entity with `"placeholder": true`
- WHEN the entity registry is parsed
- THEN `EntityDefinition.placeholder` is true
- AND no unknown-trait warning is raised for `placeholder`

### Requirement: Alignment profiles

Entity `alignment` SHALL select a code profile. Profiles SHALL NOT be duplicated in JSON.

| Alignment | Behavior |
|-----------|----------|
| `evil` | Hostile; `VoreCapable`; digestion; blocks movement |
| `good` | Ally faction; follows on descent; never vore |
| `neutral` | Flee evil; never vore |

`VoreCapable`, digestion, follow-on-descent, and blocks-movement SHALL NOT appear as entity data fields.

#### Scenario: Evil spawn is vore-capable without ability flags

- GIVEN an evil entity with empty `abilities`
- WHEN spawned from definition
- THEN `VoreCapable` is present
- AND `DigestionStats` is present when alignment digests

#### Scenario: Good spawn is never vore-capable

- GIVEN a good entity from data
- WHEN spawned
- THEN `VoreCapable` is absent

### Requirement: Ignore-unknown semantics

Unknown entity traits and abilities SHALL log a one-time warning per key and SHALL NOT crash. Parsed-but-unimplemented known traits (e.g. `experience_points`) SHALL be stored without warning.

#### Scenario: Mystery trait warns once

- GIVEN an entity JSON object with an unrecognized top-level field
- WHEN the registry loads
- THEN a warning is emitted
- AND the game continues

### Requirement: Density-driven floor spawn

`spawn.weight` SHALL be **relative draw probability only**, not an implicit species count. **Non-good** NPC count per floor SHALL come from `data/dungeon_spawn.json` via `compute_target_npc_count()` (evil + neutral only). Good allies use a separate **quota** (see **Good spawn quota**).

`spawn_floor_population()` SHALL:

1. Count valid spawn tiles and compute density `target` from density config + RNG variance + difficulty `density_multiplier`
2. Run the **good spawn quota** pass (followers count first; weighted new goods up to difficulty `good_spawn_limit`)
3. Filter **non-good** definitions by `spawn.min_depth ≤ floor_depth ≤ spawn.max_depth`, terrain, `spawn.weight > 0`, `spawn_requires_water` when the map has no deep water, and **`spawn.requires_vore_types`** against the run’s `VoreContentPreferences` (see **Spawn vore-type requirements**)
4. Build a **filtered union** of eligible land and water non-good definitions that still have placement candidates
5. Perform `target` independent weighted draws among evil/neutral only (`int(spawn.weight)` truncation); reject and retry when a drawn terrain pool is empty
6. Spawn only at `new_game()` and `descend_floor()` — no mid-level respawn

The code SHALL NOT enforce minimum or maximum counts per species `id` within density draws. The good quota is a **faction-wide** cap, not a per-species min/max. Filtering out gated species SHALL NOT reduce `target`; remaining eligible species fill the draws.

#### Scenario: Weight affects probability not quota

- GIVEN a fixture registry with wolf weight 6 and rabbit weight 6 at depth 1
- WHEN many independent spawns are simulated on a large candidate map
- THEN wolf and rabbit counts vary with RNG
- AND neither species has a hardcoded floor count in production code

#### Scenario: Aquatic eligibility on water maps

- GIVEN a floor with deep water and aquatic definitions in the registry
- WHEN spawn draws include water terrain
- THEN aquatic NPCs may appear on water tiles
- AND aquatic count is not guaranteed per floor

#### Scenario: Depth gate

- GIVEN an entity with `spawn.min_depth` 5
- WHEN `floor_depth` is 4
- THEN that entity is not eligible for draws

### Requirement: Spawn vore-type requirements

Optional `spawn.requires_vore_types` (string array) is the species’ **vore capability** list when non-empty. It SHALL gate whether a definition is a spawn **candidate**. Semantics:

| JSON value | Effect |
|------------|--------|
| Missing, `null`, or `[]` | Unrestricted |
| After ignoring unrecognized tokens, empty set | Unrestricted |
| One or more of `OV` / `CV` / `AV` | **OR**: eligible iff at least one recognized listed type is enabled in the run’s vore content prefs (non-empty intersection) |

Unrecognized tokens SHALL be ignored (no load failure). A present value that is not an array or `null` SHALL be a load error.

Stock shipped entities SHALL use `"requires_vore_types": []` (documentation; unrestricted).

The same eligibility check SHALL apply to **all definition-based materialization** (`spawn_from_definition` / `spawn_entity_by_id`: floor population, good quota, arena, NPC summons, alliance potion). When prefs are not met, creation SHALL NOT occur (`None` / skip). **Save/load restore** SHALL NOT despawn existing NPCs via this gate.

Prefs source: the run snapshot `VoreContentPreferences` (see `vore` / `main-menu` specs).

When non-empty, the same capability list SHALL also constrain **initiation**: a living predator may only attempt types in (its narrative types ∩ capability ∩ run prefs). Empty capability remains unrestricted for attempts. Lookup is by `SpeciesId` → definition (including save-restored NPCs). When that attempt pool is empty, initiation SHALL use the prefs-immune internal type `GENERIC` with hardcoded minimal copy (see `vore` spec; likely unreachable in normal play given New Game prefs snapshot + this spawn OR gate).

#### Scenario: CV-only species excluded when CV disabled

- GIVEN a definition with `spawn.requires_vore_types: ["CV"]`
- AND the run has CV disabled
- WHEN floor eligibility is built
- THEN that definition is not a candidate
- AND density `target` is unchanged so other eligible species may fill the count

#### Scenario: Pair spawns when any listed type is enabled

- GIVEN `spawn.requires_vore_types: ["OV", "CV"]`
- AND the run enables OV but not CV
- WHEN spawn eligibility is checked
- THEN the definition is eligible

#### Scenario: Pair excluded when neither listed type is enabled

- GIVEN `spawn.requires_vore_types: ["CV", "AV"]`
- AND the run enables only OV
- WHEN spawn eligibility is checked
- THEN the definition is not eligible

#### Scenario: All three listed is effectively unrestricted for spawn

- GIVEN `spawn.requires_vore_types: ["OV", "CV", "AV"]`
- AND the run enables any one of those types
- WHEN spawn eligibility is checked
- THEN the definition is eligible (at least one pref is always on)

#### Scenario: Unknown tokens ignored

- GIVEN `spawn.requires_vore_types: ["CV", "nope"]`
- AND the run enables CV
- WHEN the definition is parsed and checked
- THEN the effective capability is `{CV}` only
- AND the species may spawn

#### Scenario: Capability restricts attempts when prefs allow more

- GIVEN a definition with `spawn.requires_vore_types: ["CV"]`
- AND the run enables OV, CV, and AV
- AND the species has spawned
- WHEN that predator initiates vore
- THEN only `CV` may be selected

### Requirement: Good spawn quota

When the player descends, good-aligned NPCs in line of sight follow (see `dungeon` spec). Fresh floor population SHALL apply a **good spawn quota** from the run difficulty profile field `good_spawn_limit` (omit → default **2**):

1. If **no** good-aligned definition is eligible to place on this floor (weight > 0, depth window, terrain/water gates, **`requires_vore_types`**, non-empty placement tiles), spawn **zero** new goods.
2. Let `brought` be the number of good followers already placed on this floor. If `brought >= good_spawn_limit`, spawn **zero** new goods.
3. Otherwise weighted-spawn new goods until `brought + new == good_spawn_limit` or placeable goods run out (independent weighted draws; duplicate species allowed).
4. **Placement band:** each **new** good SHALL be placed on a tile whose **player-path** distance from the player's floor start position is between **10 and 15** inclusive (8-directional steps). Path tiles SHALL treat **closed doors as walkable** (openable); items and runes do **not** block path length. Tiles outside this band SHALL NOT be used for new goods. If no band tiles remain, stop placing new goods early.
5. Density spawn SHALL **exclude** good-aligned definitions (quota owns good presence). Followers do **not** reduce the density target. Followers from descent are **not** re-placed by this band rule.

Stock limits: **Easier = 3**, **Normal / Hard / Nightmare = 2**.

`floor_depth` SHALL increment **before** spawning the new floor.

#### Scenario: Floor with no eligible goods

- GIVEN floor depth has no good species with weight > 0 in range
- WHEN the floor spawns
- THEN zero new goods are placed

#### Scenario: Quota with zero followers

- GIVEN eligible goods and `good_spawn_limit` 2
- AND zero followers
- WHEN the floor spawns
- THEN exactly 2 new goods are placed when tiles allow

#### Scenario: Followers count toward the cap

- GIVEN one good follower and limit 2
- WHEN the floor spawns
- THEN exactly 1 new good is placed (when eligible)

#### Scenario: At or over limit

- GIVEN two or more good followers and limit 2
- WHEN the floor spawns
- THEN zero new goods are placed

#### Scenario: Density never adds extra goods

- GIVEN the good quota is filled
- WHEN density weighted draws run
- THEN no good-aligned species is selected

### Requirement: Combat range model

`Fighter` SHALL use `accuracy`, `evade`, `ac`, `min_damage`, `max_damage`. `power` and `defense` are retired.

`accuracy` and `evade` SHALL be continuous numbers (floats). Hit chance is not restricted to discrete integer bands.

Hit check:

```text
# continuous uniform on [0, evade]; if evade <= 0, roll is 0
hit_value = attacker.accuracy - continuous_uniform(0, defender.evade)
hit lands when hit_value > 0
```

When `0 < accuracy < evade`, expected hit rate is `accuracy / evade`. When `accuracy >= evade > 0`, expected hit rate is 1. When `evade <= 0`, any `accuracy > 0` always hits.

Damage on hit:

```text
raw_damage = uniform_int(attacker.min_damage, attacker.max_damage)
final_damage = max(0, raw_damage - uniform_int(0, defender.ac))
```

Player combat defaults are data-driven via `data/global_tuning.json` (see balance / global tuning).

#### Scenario: Miss message grammar

- GIVEN the player misses
- WHEN the log reports the miss
- THEN text reads *"You miss …"* (not *"You misses …"*)

#### Scenario: NPC stats from JSON

- GIVEN a wolf spawned from definition at depth 1 with stock zero depth scaling
- WHEN combat resolves
- THEN `Fighter` fields match the wolf entry in `entities.json` (depth bonuses from `depth_scaling.json` are additive on top of base definition; see `balance` spec)

### Requirement: Vore narratives from data

Evil entities MAY define `vore_narratives` (per-type variant arrays), `digestion_complete`, `digestion_player_modal`, and NPC vore **log** objects keyed by narrative type (`OV`, `CV`, `AV`): `npc_vore_hit`, `npc_vore_miss`, `offscreen_vore`, `offscreen_digest`. Each log object uses the same shape as `digestion_complete` (`{ "OV": ["..."], ... }`). Legacy flat off-screen keys (`offscreen_ov`, etc.) are rejected at load. Lookup key SHALL be entity `id`. The game SHALL pick one variant at random per attempt (respecting disabled types in options). `npc_vore_hit` / `npc_vore_miss` are used for visible NPC-on-NPC vore; `offscreen_vore` / `offscreen_digest` when events resolve outside player FOV (see `vore` and `digestion` specs).

Hardcoded `src/vore_content.py` and wolf narrative fallback are removed.

#### Scenario: Shark uses shark text

- GIVEN a shark vore attempt
- WHEN the modal opens
- THEN attempt text references the shark (not wolf copy)

### Requirement: Generic spawn factory

Production spawn SHALL use `spawn_from_definition()` only. Per-species `_spawn_*` helpers and species spawn constants in `constants.py` are removed.

## Technical notes (non-normative)

- Loaders: `src/data/entity_loader.py`, `src/data/loaders.py`
- Registry: `src/data/entity_registry.py`
- Profiles: `src/data/alignment_profiles.py`
- Narrative index: `src/data/narrative_index.py` (keyed by `id`)
- Spawn: `src/spawn.py` — `spawn_floor_population()`, `spawn_entity_by_id()`, `spawn_from_definition(..., floor_depth=)`
- Spawn config: `src/data/dungeon_spawn_loader.py`, `compute_target_npc_count()` in `src/data/dungeon_spawn_config.py`
- Depth scaling: `src/data/depth_scaling_loader.py` — bake at spawn (`balance` spec)
- Spawn: `eligible_good_definitions()`, `good_spawn_count_to_place()` in `src/spawn.py`
- Tests: `tests/test_npc_data_pr1.py` … `tests/test_npc_data_pr4.py`, `tests/test_spawn_density_pr2.py`, `tests/test_dungeon_spawn_config.py`

## Related specs

| Spec | Relationship |
|------|----------------|
| `enhancements-3/spec.md` | Faction NPC behaviors |
| `dungeon/spec.md` | Water floors, descent, follower placement, density spawn |
| `floor-runes/spec.md` | Independent of NPC spawn |
| `vore/spec.md` | Player vore modals; narratives from data |
| `digestion/spec.md` | Digestion lines from data index |
| `inventory-items/spec.md` | Item JSON gameplay |
| `core-roguelike/spec.md` | Bump combat uses new `Fighter` fields |