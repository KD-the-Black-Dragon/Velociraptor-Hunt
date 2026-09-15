# balance Specification

## Purpose

Data-driven **difficulty profiles** and **depth scaling** for NPC threat as floors descend. Player progression remains exploration-based (gear + floor runes); this domain scales **monsters**, not player XP.

Implementation: `data/depth_scaling.json`, `src/data/depth_scaling_config.py`, `src/data/depth_scaling_loader.py`, bake in `src/spawn.py` (`spawn_from_definition`).

**Balance simulator:** headless trajectory runs use the same difficulty profiles; see `balance-simulator` spec for pinned test seeds and how to read sim CSV output.

**Terminology:** defeated / stunned / digested.

## Requirements

### Requirement: Depth scaling catalog loads

The game SHALL load `data/depth_scaling.json` at startup (whole-file mod replace). Schema version SHALL be `1`. Stock file SHALL define difficulties `easier`, `normal`, `hard`, `nightmare` with `default_difficulty_id` of `normal`.

#### Scenario: Stock config loads

- GIVEN the shipped `depth_scaling.json`
- WHEN the catalog is parsed
- THEN all four difficulties exist
- AND Normal is the default
- AND floor depth 1 yields zero depth-step bonuses (start_depth 1; steps 0)

### Requirement: Dual-integer depth schedule

For each integer combat/digestion-damage schedule the engine SHALL compute:

`steps = max(0, depth - start_depth)`  
`bonus = per_floor * steps + floor(steps / every_n_floors) * bank_amount`  
when `every_n_floors > 0`; bank term is 0 when `every_n_floors` is 0.

Float stats (`accuracy`, `evade`) SHALL use the same integer formula multiplied by schedule `unit` (default `0.01` for accuracy, `1.0` for evade).

#### Scenario: 1.25 average per step

- GIVEN `per_floor: 1`, `every_n_floors: 4`, `bank_amount: 1`, `start_depth: 1`
- WHEN depth is 5 (steps = 4)
- THEN integer bonus is 5

#### Scenario: Floor 1 has zero depth steps

- GIVEN `start_depth: 1` and any schedule
- WHEN depth is 1
- THEN steps are 0 and bonus is 0

### Requirement: Spawn-time bake

When materializing an NPC via `spawn_from_definition`, the engine SHALL resolve depth bonuses for the run difficulty (or config default) and **bake** them into `Fighter` (and `DigestionStats.damage_per_tick` when present). Bonuses SHALL apply only if the entity alignment is in the profile’s `apply_to_alignments`.

`digest_time` SHALL NOT be modified by depth scaling.

#### Scenario: Evil receives bonuses; good does not

- GIVEN a profile with `apply_to_alignments: ["evil"]` and non-zero AC schedule
- WHEN an evil and a good entity spawn at the same depth
- THEN only the evil entity’s AC includes the depth bonus

#### Scenario: Summons use current floor depth

- GIVEN the player is on floor depth D
- WHEN a summon ability spawns an entity
- THEN that entity bakes with `floor_depth=D` (not always 1)

### Requirement: Ranged scaling gate

Depth accuracy/damage offsets SHALL apply to ranged Fighter fields only when base definition `ranged_min_damage > 0` and `ranged_max_damage > 0`. Otherwise ranged fields copy the definition unchanged.

#### Scenario: Stock zero-ranged entity stays zero ranged

- GIVEN a definition with ranged min/max damage both 0 and non-zero melee damage depth bonuses
- WHEN the entity spawns at deep floor
- THEN ranged min/max damage remain 0

### Requirement: No digest_time scaling

Depth scaling JSON SHALL NOT expose `digest_time`. Digestion strike count remains base definition / alignment default only.

### Requirement: Options difficulty setting

The Options menu SHALL list difficulties from `depth_scaling.json` (`display_name` in file order). The player’s selection is stored in settings as `difficulty_id` and applies to the **next** New Game only (snapshot at run start). There is **no** in-run difficulty HUD.

#### Scenario: Cycle difficulty in Options

- GIVEN the Options screen
- WHEN the player highlights Difficulty and presses Left/Right
- THEN settings `difficulty_id` advances among Easier / Normal / Hard / Nightmare (stock)
- AND the choice is persisted for the next New Game

### Requirement: Run difficulty snapshot

On New Game the engine SHALL copy settings `difficulty_id` into the run and keep it for the run lifetime. Save/load SHALL persist `difficulty_id`. Unknown id on load SHALL fall back to `default_difficulty_id` with a notice.

### Requirement: Density and rune economy from profile

Each difficulty profile MAY set:

| Field | Effect |
|-------|--------|
| `density_multiplier` | Multiplies density-derived NPC target (still min/max/tile capped); applies to evil/neutral density pass |
| `runes_per_floor_override` | Overrides stock rune count for spawn **and** map feasibility budget |
| `rune_pieces_multiplier` | Integer ≥ 1; multiplies pieces needed for a full rune bonus (1 = no extra multiplier) |
| `prefix_spawn` | Chance curve for floor-population NPC prefixes (e.g. Elite) |
| `spawn_ai_freeze` | One-shot distant freeze so far NPCs do not all path to the player at once (see below) |
| `good_spawn_limit` | Cap on good allies per floor (followers count first; then weighted new goods). Omit → **2**. Stock: Easier **3**, Normal/Hard/Nightmare **2** |
| `good_ranged_shots` | Max Path/Smite magazine for **good** `RangeN`/`SmiteN` NPCs. Omit → **2**. Stock: **2** on all difficulties. MUST be ≥ 1 |
| `evil_ranged_shots` | Max Path/Smite magazine for **evil** (and neutral, if any) `RangeN`/`SmiteN` NPCs. Omit → **2**. Stock: **2** on easier/normal/hard; **3** on nightmare. MUST be ≥ 1 |

See `npc-abilities` for magazine spend/reload AI. Player ranged is unaffected.

#### Scenario: Nightmare evil magazine is 3

- GIVEN a New Game on Nightmare and an evil `RangeN` spawn
- WHEN the NPC materializes
- THEN `RangedMagazine.maximum == 3` and `current == 3`

### Requirement: Spawn AI freeze (anti-swarm)

Each difficulty MAY define `spawn_ai_freeze`. When enabled, floor-spawned NPCs SHALL arm a one-shot freeze whose duration grows with Chebyshev distance from the player at spawn:

`turns = min(max_turns, max(0, chebyshev - distance_offset) * turns_per_chebyshev)`.

While frozen, the NPC SHALL skip AI visits. Freeze SHALL end permanently when any of: remaining turns expire; player Chebyshev ≤ `proximity_unfreeze`; the NPC takes positive combat damage. A given NPC SHALL NOT re-arm freeze after it ends. Higher freeze values (Easier) are intended to favor the player.

#### Scenario: Far spawn stays idle initially

- GIVEN Normal freeze config and an NPC spawned at Chebyshev 20 from the player
- WHEN several player turns pass without approaching or damaging that NPC
- THEN that NPC does not take AI actions for the computed freeze duration

#### Scenario: Proximity wakes freeze

- GIVEN a frozen NPC with remaining turns
- WHEN the player moves within `proximity_unfreeze`
- THEN the freeze ends and the NPC may act on that world phase

Stock Easier/Normal/Hard/Nightmare set real curves and economy (see shipped `depth_scaling.json`). Map gen and spawn both honor the run’s effective `runes_per_floor` (override or catalog default).

#### Scenario: Pieces multiplier 2

- GIVEN a run with `rune_pieces_multiplier: 2` and a warding (+1 AC) rune
- WHEN the player absorbs one warding rune
- THEN AC is unchanged and the log shows progress toward the bonus
- WHEN the player absorbs a second warding rune
- THEN AC increases by 1

### Requirement: Past Runs shows difficulty

Completed runs SHALL store difficulty id and display name. The Past Runs board stats line SHALL include the display name when present. Legacy records without difficulty SHALL omit the field.

### Requirement: NPC prefixes

The game SHALL load `data/npc_prefixes.json`. Floor population MAY roll one prefix per NPC after depth bake using difficulty `prefix_spawn` chance. Summons SHALL NOT roll prefixes.

**Roll model:** (1) global prefix chance roll; (2) build candidate list from prefixes eligible for alignment, depth window, `weight > 0`, and optional `requirements` for the host species; (3) if empty, spawn without a prefix; (4) else one weighted pick. No reroll loop.

Applied prefixes SHALL set `DisplayName` to `{display_prefix}{base}` (e.g. `Elite wolf`) and attach `NpcPrefix`. Flat `stat_bonuses` stack after depth bake. Optional `grant_abilities[]` SHALL merge with species `abilities[]` at apply time (parsed/collapsed per `npc-abilities` spec).

`stat_bonuses` keys: `max_hp`, `ac`, `evade`, `accuracy`, `ranged_accuracy`, `min_damage`, `max_damage`, `digestion_damage_per_tick`. `accuracy` affects melee and ranged (when species has ranged damage); `ranged_accuracy` affects ranged only.

`requirements.ability_families` (optional): host must have ≥1 matching ability — family tokens `RangeN`, `SmiteN`, `RangedVoreN`, or exact fixed ability ids.

Stock prefixes are **evil-only**. Stock ships: `elite`, `brute`, `berserk`, `veteran`, `starving`, `sniper`, `bloated` — shared weight pool; tune per-row `weight` in JSON. `sniper` requires `RangeN` on the host species.

Stock `prefix_spawn` is tuned per difficulty (Easier: none; Normal+: chance rises with depth).

Unknown prefix ids on load SHALL soft-drop (clear component; restore base display name from species). Baked stats and merged abilities from a removed prefix id are not reverted (legacy behavior).

#### Scenario: Forced elite name

- GIVEN an evil wolf definition and the stock `elite` prefix
- WHEN `apply_prefix_definition` runs
- THEN display name is `Elite wolf` (prefix + base `display_name`) and max HP / AC include elite flats

#### Scenario: Sniper excluded from melee host

- GIVEN floor spawn rolls a prefix for an evil rat without `RangeN`
- AND the only eligible prefix row is `sniper`
- WHEN candidate filtering runs
- THEN no prefix is applied

#### Scenario: Brute grants Slow

- GIVEN the stock `brute` prefix applied to an evil wolf
- WHEN spawn completes
- THEN the entity has `Slow` in `Abilities`

#### Scenario: Summons without prefix

- GIVEN `spawn_entity_by_id` / summons (default `roll_prefix=False`)
- WHEN an NPC is spawned
- THEN no random prefix is applied

## Out of scope

- XP / player leveling
- Mid-run difficulty change
- In-run difficulty HUD
- Loot austerity or regen rate by difficulty
- `digest_time` depth scaling

## Related

| Spec / doc | Relation |
|------------|----------|
| `npc-data/spec.md` | Entity base stats; placeholder flag; depth adds at spawn |
| `floor-runes/spec.md` | Piece banks; `runes_per_floor`; pieces × difficulty multiplier |
| `dungeon/spec.md` | Floor depth; spawn population |
| `past-runs/spec.md` | Difficulty on board |
| `main-menu/spec.md` | Options |
| `data/SCHEMA.md` | JSON schema for `depth_scaling.json` / `npc_prefixes.json` |
| `modding/spec.md` | Whole-file replace class |
| `balance-simulator/spec.md` | Headless hybrid analyzer; pinned seeds; CSV interpretation |
