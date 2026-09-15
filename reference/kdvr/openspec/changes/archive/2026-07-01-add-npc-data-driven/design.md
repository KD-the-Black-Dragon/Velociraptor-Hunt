# Design: Data-Driven NPC Definitions

| Field | Value |
|-------|-------|
| **Status** | Approved trait catalog (2026-07-01) |
| **Change** | `openspec/changes/add-npc-data-driven/` |
| **Spec target** | `openspec/specs/npc-data/spec.md` |

---

## Overview

NPC species, stats, spawn weights, examine text, glyphs, and vore narratives move to **`data/entities.json`**. Items use separate stub files: `weapons.json`, `armor.json`, `potions.json`, `wands.json`.

Code loads JSON at startup, builds a registry, and spawns entities through one generic factory. **Unknown traits and abilities are ignored** with a one-time warning per key.

**Format:** JSON. **Spawn:** weight-based pool immediately (no fixed `spawn.count`). **Vore narrative lookup key:** entity `id`.

---

## Alignment profiles (code — not per-entity data)

`wolf`, `knight`, and `rabbit` are **archetypes** that define the standard behavior for their alignment. Every entity inherits its alignment’s profile; data does not repeat these rules.

| Alignment | Archetype | Code-derived behavior |
|-----------|-----------|------------------------|
| `evil` | wolf | Hostile to player; vore-capable; digestion; `BlocksMovement` per evil standard |
| `good` | knight | Aids player faction; follows on descent; never vore; `BlocksMovement` per good standard |
| `neutral` | rabbit | Flee-from-evil AI; never vore; `BlocksMovement` per neutral standard |

**Removed from entity data:** `VoreCapable`, `Digestion`, `follows_on_descent`, `blocks_movement`, `hostile_to_player`, `hostile_to`, `can_vore_player`, `can_vore_npc` — all implied by `alignment`.

**Evil-only data:** `vore_narratives` and optional `digestion_damage_per_tick` (default **3** from wolf archetype when omitted).

**Shark** is `evil` → wolf profile + aquatic mobility + water spawn gates from its own traits.

---

## Entity trait schema (final)

### Required

| Trait | Type | Notes |
|-------|------|-------|
| `id` | string | Stable key; vore narrative lookup |
| `display_name` | string | Log / examine species label |
| `glyph` | string (1 char) | Tile character |
| `fg` | [r, g, b] | Glyph color 0–255 |
| `alignment` | `good` \| `evil` \| `neutral` | Drives entire faction profile |
| `mobility` | `ground` \| `fly` \| `aquatic` | Tile traversal |
| `max_hp` | int | |
| `evade` | int | Dodge — `uniform(0, evade)` subtracted from attacker's `accuracy` on hit check |
| `ac` | int | Mitigation — `uniform(0, ac)` subtracted from rolled damage when hit lands |
| `accuracy` | number | Attacker base hit value before evade roll |
| `min_damage` | int | Inclusive damage roll floor (before AC mitigation) |
| `max_damage` | int | Inclusive damage roll ceiling (before AC mitigation) |
| `spawn.weight` | number | Relative weight in floor pool |
| `spawn.min_depth` | int | Inclusive |
| `spawn.max_depth` | int | Inclusive |

### Optional

| Trait | Type | Notes |
|-------|------|-------|
| `examine` | string | `ExamineDescription`; placeholder OK |
| `proper_name` | string \| null | If non-null, **every** spawn gets this `ProperName` |
| `spawn.terrain` | `land` \| `water` | Default `land` |
| `spawn_requires_water` | bool | Floor must have deep water (shark pattern) |
| `digestion_damage_per_tick` | int | Evil only; default 3 |
| `experience_points` | int | Stored; gameplay ignores until XP exists |
| `vore_narratives` | object | Evil; each type maps to **variant array** (random pick) |
| `digestion_complete` | object | Evil; `{ "OV": ["{predator} ..."], ... }` NPC digest log |
| `digestion_player_modal` | object | Evil; per-type variant arrays of phase lines (random variant) |
| `abilities` | string[] | Extra modifiers — see below |

### Abilities (modifier array)

Abilities are **optional deviations** from the alignment default. Code registers handlers; unknown entries are ignored.

Examples (implement when needed):

| ID | Meaning |
|----|---------|
| `Range2` … `Range9` | Ranged attack at Chebyshev distance N |
| `Fast` | Extra action rate (future) |

No need to enumerate every future deviation in the schema — only document the registry pattern.

### Reserved (valid JSON, ignored until implemented)

| Trait | Notes |
|-------|-------|

| `hd` | Hit dice / threat rating |
| `scale_with_depth` | Stat scaling |
| `loot_table` | Reference external loot |
| `drop_chance` | |
| `gold_min` / `gold_max` | |
| `guaranteed_drops` | |
| `spawn.min_distance` | Override global spawn distance |
| `spawn.group_size` | Pack spawn |
| `spawn_chance` | Per-floor gate before weighting |
| `speed` | |
| `attacks_per_turn` | |
| `ai_profile` | Override alignment default (rare) |
| `vore_narrative_types` | Subset filter when not using full `vore_narratives` |

### Explicitly excluded (do not put in schema docs)

`hostile_to_player`, `hostile_to`, `levitation`, `phasing`, `crit_*`, `regen_*`, `damage_type`, `level`, depth bonuses, `vore_hp_threshold`, `can_vore_player`, `can_vore_npc`, resistances/immunities/vulnerabilities/status/corpse, senses/AI sleep flags, defeat/spawn messages, `tile_set`, `mod_source`, `tags`, `VoreCapable`, `Digestion`, `blocks_movement`, `follows_on_descent`.

---

## Combat model change

Today: `damage = max(0, attacker.power - defender.defense)` using `Fighter.power` and `Fighter.defense`. The old `defense` field is **retired**.

**Target model (PR 2):**

```
hit_value   = attacker.accuracy - uniform(0, defender.evade)
hit lands   = hit_value > 0   # exact threshold TBD (e.g. > 0 or roll vs %)

raw_damage  = uniform(attacker.min_damage, attacker.max_damage)
final_damage = max(0, raw_damage - uniform(0, defender.ac))
```

**Stat roles:**

| Stat | Role | Example archetype |
|------|------|-------------------|
| `evade` | Reduces chance to be hit | Butterfly — high evade, low AC |
| `ac` | Reduces damage when hit lands | Stone golem — low evade, high AC |

`accuracy`, `min_damage`, and `max_damage` live on the **attacker**. `evade` and `ac` live on the **defender**.

Initial migration values (tunable in JSON):

| Species | evade | ac | accuracy | min_damage | max_damage |
|---------|-------|-----|----------|------------|------------|
| wolf | 2 | 2 | 1.0 | 6 | 6 |
| shark | 2 | 2 | 1.0 | 6 | 6 |
| knight | 1 | 3 | 1.0 | 3 | 3 |
| rabbit | 4 | 0 | 1.0 | 0 | 0 |

Knight: lower evade, higher AC (armored). Rabbit: higher evade, no AC (small target). PR 2 will rescale `accuracy` if needed so the formula behaves well with integer evade dice.

---

## Spawn algorithm (weight-based)

1. Filter definitions: `min_depth ≤ floor_depth ≤ max_depth`
2. Gate: `spawn_requires_water`, `spawn.terrain` vs map
3. Build weighted pool: each definition appears `floor(weight)` times (fractional weights: treat as probability or multiply weights by LCM — detail in PR 2)
4. Shuffle pool; place on valid tiles until exhausted
5. Good followers from descent reduce **good-aligned** weight draws, not a hardcoded knight count

---

## File layout

```
data/
  entities.json      # NPC definitions
  weapons.json       # stub
  armor.json         # stub
  potions.json       # stub
  wands.json         # stub
  SCHEMA.md          # human-readable field reference
```

Loaders are separate modules; items are **not** wired in v1 (stub files only).

### Item trait summary (approved)

**Weapons:** `id`, `display_name`, `glyph`, `fg`, `examine`, `min_damage`, `max_damage`, `accuracy_bonus`, `durability_max`, `spawn_weight`, `spawn_min_depth`, `spawn_max_depth`, `abilities`

**Armor:** `id`, `display_name`, `glyph`, `fg`, `examine`, `ac_bonus`, `durability_max`, spawn fields, `abilities`

**Potions:** `id`, `display_name`, `glyph`, `fg`, `examine`, `effect`, `heal_amount`, `spawn_weight`, `spawn_min` (floor minimum count), depth spawn fields, `abilities`

**Wands:** `id`, `display_name`, `glyph`, `fg`, `examine`, `effect`, `charges_max`, `charges_start`, `range`, `min_damage`, `max_damage`, `accuracy`, spawn fields, `abilities`

---

## Ignore-unknown semantics

```
Unknown trait 'experience_points' on 'wolf' — ignored (not implemented)
Unknown ability 'Range5' on 'goblin' — ignored (not implemented)
```

Warn once per `(trait_or_ability_name)` per session. Invalid **required** field or bad enum → fail load with clear error.

---

## Code architecture

```
data/*.json
    ↓
src/data/loaders.py          # entities + item files
src/data/entity_registry.py  # frozen EntityDefinition
src/data/alignment_profiles.py  # good/evil/neutral from archetypes
src/data/abilities.py        # modifier registry
src/spawn.py                 # spawn_floor_population()
```

Delete: per-species `_spawn_*` in `spawn.py`, species constants in `constants.py`, hardcoded `NARRATIVE_PACKS` in `vore_content.py` (replaced by load-time index keyed by `id`).

---

## PR plan

| PR | Scope |
|----|-------|
| 1 | JSON loaders, entity schema, alignment profiles, ignore-unknown, stub item files |
| 2 | Combat: accuracy + damage range; generic spawn factory; weight pool |
| 3 | Vore narratives in JSON; evil auto vore/digest; remove wolf fallback |
| 4 | Water/depth/terrain spawn gates; good follower weight deduction |
| 5 | `npc-data` spec, README modding, acceptance, archive |