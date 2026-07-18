# Data file reference

Human-editable JSON under `data/`. Unknown top-level entity fields are ignored with a warning. Parsed fields not yet used by gameplay (e.g. `experience_points`) are stored silently.

**Ability tokens:** see `data/Readme.txt` for the exact strings the game loads and runs.

## Modding

Player mods live under `{user_data}/mods/<mod_folder>/` (not in the install tree). Each mod may include any subset of the JSON files documented below (same filenames and schemas as stock `data/`).

| Merge rule | Files |
|------------|--------|
| **By id** (later enabled mod wins) | `entities.json`, `weapons.json`, `armor.json`, `potions.json`, `wands.json`, `floor_runes.json`, `macguffins.json`, `names.json` (key = entity id) |
| **Whole file replace** | `dungeon_spawn.json`, `depth_scaling.json`, `global_tuning.json`, `depth_jump_start.json`, `npc_prefixes.json`, `rescue_gratitude.json`, `ui_layout.json` |

Core install data always loads first. Per-mod `mod.state` holds `E`/`D` and load order. UI: **Options → Mods**. Full player guide: `README.md` (**Modding**).

## `ui_layout.json`

Screen region geometry and layout presets for the UI overhaul. Loader: `src/ui/layout.py`.

### Top level

| Field | Type |
|-------|------|
| `schema_version` | int — must be `1` |
| `tile_px` | int — source tileset cell size in pixels (12 for `Alloy_curses_12x12.png`) |
| `tile_scale` | int — display scale multiplier (2 = ~2× glyph height via window pixel size) |
| `default_preset` | string — preset id used when none is selected |
| `presets` | object — named layout presets |

### `presets.<id>`

| Field | Type |
|-------|------|
| `root_cols` | int — root console width in character cells |
| `root_rows` | int — root console height in character cells |
| `regions` | object — named rectangles that tile the root without gaps or overlap |
| `map_viewport_tiles` | `{w, h}` — dungeon tiles visible at once; must match `regions.map_viewport` size |
| `message_log_lines` | int — visible log rows; must be ≤ `regions.message_log.h` |
| `sidebar` | object — see below |

### `presets.<id>.regions` (required keys)

| Key | Meaning |
|-----|---------|
| `map_viewport` | Camera-centered dungeon view |
| `sidebar` | Player status + nearby NPC list |
| `message_log` | Scrolling combat/event log |
| `status_corner` | Depth + player ailments/buffs |

Each region: `{x, y, w, h}` in character cells.

### `presets.<id>.sidebar`

| Field | Type |
|-------|------|
| `hp_bar_width` | int — player exact HP bar width; must fit `HP nn/nn [bar]` in sidebar |
| `npc_hp_bar_width` | int — NPC condition bar width (**PR11**, default 6); fill `#` count `0…6` via `round(6 * hp / max_hp)` |
| `max_evil` | int — max evil NPC **entries** in FOV across both columns (stock: 10) |
| `max_good` | int — max good NPC **entries** in FOV across both columns (stock: 4) |
| `evil_per_column` | int — max evil entries in the first column before spilling to column two (stock: 5) |
| `good_per_column` | int — max good entries in the first column before spilling to column two (stock: 2) |
| `player_top_pad` | int — blank rows above player name (**PR11**, default 1) |
| `player_bottom_pad` | int — blank rows after player HP before evil band (**PR11**, default 1) |
| `good_bottom_pad` | int — blank rows below good NPC band (**PR11**, default 2) |
| `rows_per_npc` | int — rows per NPC slot: name, bar, spacer (**PR11**, default 3) |

Stock presets: `standard` (57×34 map, 23-wide sidebar, 9-char player HP bar), `wide_sidebar` / **Wide** (44×34 map, 36-wide sidebar, 18-char player HP bar).

Window resize floor: **1360×768** design target; hard pixel minimum `1336×768` (one 24px cell below design width at 2× scale).

**PR11 geometry:** `status_corner.w` = 10, `message_log.w` = 70 (80-col root). Dynamic resize (**PR11**) recomputes `map_viewport` from window pixels while holding sidebar/message_log/status_corner floors from the active preset.

## `global_tuning.json`

Player base combat stats, natural regen cadence, vore hit/escape knobs, and floor loot placement caps. Whole-file mod replace.

Loader: `src/data/global_tuning_loader.py`. Gameplay still imports familiar names from `src.constants` (`PLAYER_MAX_HP`, `VORE_ESCAPE_BASE`, …); those resolve to this file.

### Top level

| Field | Type |
|-------|------|
| `schema_version` | int — must be `1` |
| `player` | object — base player combat |
| `regen` | object — natural HP regen |
| `vore` | object — engulfment rules |
| `loot` | object — floor item placement caps |

### `player`

| Field | Type | Stock | Meaning |
|-------|------|-------|---------|
| `max_hp` | int ≥ 1 | `30` | Starting / base max HP (runes add on top) |
| `accuracy` | number ≥ 0 | `1.5` | Base hit accuracy |
| `evade` | number ≥ 0 | `1` | Base evade (armor `evade_bonus` + rune `bonus_evade` stack on top via `effective_fighter`); continuous hit roll vs accuracy |
| `ac` | int ≥ 0 | `1` | Base AC (armor adds on top) |
| `min_damage` / `max_damage` | int ≥ 0 | `1` / `2` | Unarmed / base melee range; `min` ≤ `max` |

### `regen`

| Field | Type | Stock | Meaning |
|-------|------|-------|---------|
| `hp` | int ≥ 0 | `1` | HP restored per regen tick |
| `every_n_player_turns` | int ≥ 1 | `8` | Player + good/neutral regen period |
| `evil_every_n_player_turns` | int ≥ 1 | `12` | Evil NPC regen period |

### `vore`

| Field | Type | Stock | Meaning |
|-------|------|-------|---------|
| `hp_threshold` | number in `(0, 1]` | `0.5` | Prey eligible for vore at or below this HP fraction |
| `hit_min` / `hit_max` | number ≥ 0 | `0.25` / `1.0` | Vore hit chance at threshold vs 0 HP (`min` ≤ `max`) |
| `escape_base` | number ≥ 0 | `0.15` | Base struggle escape chance |
| `escape_per_fail` | number ≥ 0 | `0.05` | Added per failed struggle |
| `struggle_damage` | int ≥ 0 | `2` | Damage to predator per struggle |

### `loot`

| Field | Type | Stock | Meaning |
|-------|------|-------|---------|
| `max_floor_item_placements` | int ≥ 0 | `5` | Cap on weighted gear placements per floor |
| `min_floor_potions` | int ≥ 0 | `1` | Reserved / legacy floor potion floor (per-potion `spawn_min` in `potions.json` is primary) |

---

## `dungeon_spawn.json`

Controls **how many NPCs** spawn per floor (density), not **which** species (`entities.json` weights).

### Top level

| Field | Type |
|-------|------|
| `schema_version` | int — must be `1` |
| `defaults` | object — fallback density settings |
| `depth_bands` | array — depth ranges with optional overrides |

### `defaults` and band overrides

Bands inherit omitted fields from `defaults`. First matching band (`min_depth ≤ floor_depth ≤ max_depth`) wins; else `defaults` apply.

| Field | Type | Meaning |
|-------|------|---------|
| `density_pct` | number ≥ 0 | Fraction of valid spawn tiles used as NPC target (e.g. `0.012` = 1.2%) |
| `density_variance` | number in `[0, 1)` | Per-floor jitter: multiplier `uniform(1 - v, 1 + v)` |
| `min_npcs` | int ≥ 0 | Floor target never below this (still capped by valid tiles) |
| `max_npcs` | int ≥ `min_npcs` or `null` | Upper clamp; `null` = no cap |

### `depth_bands[]`

| Field | Type |
|-------|------|
| `min_depth` | int — inclusive |
| `max_depth` | int — inclusive |
| `density_pct` | optional override |
| `density_variance` | optional override |
| `min_npcs` | optional override |
| `max_npcs` | optional override |

Bands must not overlap. Loader: `src/data/dungeon_spawn_loader.py`; target count: `compute_target_npc_count()` in `src/data/dungeon_spawn_config.py`.

## `depth_jump_start.json`

Tuning for the secret **Ctrl+G** depth-jump new-game flow (`src/depth_jump_loadout.py`).

### Top level

| Field | Type | Stock | Meaning |
|-------|------|-------|---------|
| `schema_version` | int | `1` | |
| `max_target_depth` | int ≥ 1 | `20` | Valid depth-entry upper bound |
| `throwable_stack_count` | int ≥ 0 | `5` | Stack size for strongest eligible throwable |
| `potion_count` | int ≥ 0 | `3` | Weighted-random potion grants at loot depth |
| `wand_count` | int ≥ 0 | `3` | Weighted-random wand grants at loot depth |
| `simulated_runes_min_numerator` | int ≥ 0 | `2` | Per prior floor: low = `ceil(runes_per_floor × num/den)` |
| `simulated_runes_min_denominator` | int ≥ 1 | `3` | Denominator for simulated rune floor fraction |

Loader: `src/data/depth_jump_start_loader.py`. Simulated rune count also uses `engine.runes_per_floor()` (difficulty-aware).

## `depth_scaling.json`

Named **difficulty profiles** and dual-integer **depth schedules** for NPC combat (and digestion damage). Bonuses bake into `Fighter` / `DigestionStats` at spawn inside `spawn_from_definition()`. Stock profiles (Easier/Normal/Hard/Nightmare) ship with real curves; see shipped `depth_scaling.json`.

Loader: `src/data/depth_scaling_loader.py`. Math: `src/data/depth_scaling_config.py`.

### Top level

| Field | Type |
|-------|------|
| `schema_version` | int — must be `1` |
| `default_difficulty_id` | string — must exist under `difficulties` (stock: `normal`) |
| `difficulties` | object — map of difficulty id → profile |

### `difficulties.<id>`

| Field | Type | Meaning |
|-------|------|---------|
| `display_name` | string | Options / Past Runs label |
| `apply_to_alignments` | string[] | e.g. `["evil"]` — only these alignments receive depth bonuses |
| `stats` | object | map of stat key → dual-int schedule (omit or `{}` = no bonuses) |
| `density_multiplier` | number ≥ 0 | optional; reserved for PR1b (not applied in PR1) |
| `runes_per_floor_override` | int ≥ 0 or null | optional; reserved for PR1b |
| `rune_pieces_multiplier` | int ≥ 1 | optional; whole numbers only; reserved for PR1b |
| `prefix_spawn` | object | optional; Elite/prefix chance curve |
| `spawn_ai_freeze` | object | optional; one-shot distant spawn freeze (anti-swarm) |

### Dual-int schedule (`stats.<key>`)

| Field | Type | Default | Meaning |
|-------|------|---------|---------|
| `per_floor` | int | `0` | Whole units per depth step after `start_depth` |
| `every_n_floors` | int ≥ 0 | `0` | Zelda bank period; `0` = bank off |
| `bank_amount` | int | `1` | Units when bank completes |
| `start_depth` | int ≥ 1 | `1` | Depth steps = `max(0, depth - start_depth)` (floor 1 → 0 steps) |
| `unit` | number | `0.01` for `accuracy`; `1.0` for `evade` | Multiply dual-int result for float stats |

**Formula:** `bonus = per_floor * steps + floor(steps / every_n_floors) * bank_amount` (bank term 0 if `every_n_floors` is 0).

**Example (avg +1.25 per step):** `per_floor: 1`, `every_n_floors: 4`, `bank_amount: 1` → after 4 steps, bonus = 5.

### Stat keys

| Key | Notes |
|-----|-------|
| `max_hp`, `ac`, `min_damage`, `max_damage` | Integer dual-int |
| `accuracy`, `evade` | Dual-int × `unit` → float |
| `digestion_damage_per_tick` | Integer dual-int; **not** `digest_time` |

**Ranged:** melee accuracy/damage offsets apply to ranged fields only when base `ranged_min_damage > 0` **and** `ranged_max_damage > 0`.

**Who:** stock `apply_to_alignments: ["evil"]` — good/neutral do not scale unless listed.

### `prefix_spawn` (per difficulty)

Chance to apply one NPC prefix at floor spawn (not summons). Stock omits or zeros = never.

| Field | Type | Default | Meaning |
|-------|------|---------|---------|
| `base_chance_pct` | int ≥ 0 | `0` | Base percent chance |
| `chance_pct_per_depth_step` | int ≥ 0 | `0` | Added per depth step after `start_depth` |
| `max_chance_pct` | int ≥ 0 | `100` | Cap |
| `start_depth` | int ≥ 1 | `1` | Depth steps = `max(0, depth - start_depth)` |

`chance = min(max, base + per_step * steps)`; roll `0–99 < chance`.

### `spawn_ai_freeze` (per difficulty)

One-shot freeze for floor-spawned NPCs based on Chebyshev distance from the player at spawn. Higher freeze values are **gentler** (far packs wake later). Once freeze ends (timer, player proximity, or taking damage), that NPC never freezes again.

| Field | Type | Stock Normal | Meaning |
|-------|------|--------------|---------|
| `enabled` | bool | `true` | Master switch |
| `turns_per_chebyshev` | int ≥ 0 | `3` | Multiplier for excess distance |
| `distance_offset` | int ≥ 0 | `5` | Subtract from Chebyshev before multiply (near spawns unfrozen) |
| `max_turns` | int ≥ 0 | `64` | Cap on freeze duration |
| `proximity_unfreeze` | int ≥ 0 | `7` | If player Chebyshev ≤ this, freeze ends immediately |

`freeze_turns = min(max_turns, max(0, chebyshev - distance_offset) * turns_per_chebyshev)`.

## `npc_prefixes.json`

Dynamic name/stat modifiers (stock: **Elite**). Not separate entity ids. Whole-file mod replace.

Loader: `src/data/npc_prefix_loader.py`. Applied after depth bake in floor spawn only (`roll_prefix=True`).

### Top level

| Field | Type |
|-------|------|
| `schema_version` | int — must be `1` |
| `prefixes` | array |

### `prefixes[]`

| Field | Type | Meaning |
|-------|------|---------|
| `id` | string | Save id (`elite`) |
| `display_prefix` | string | Prepended to base name (`"Elite "`) |
| `apply_to_alignments` | string[] | e.g. `["evil"]` |
| `min_depth` / `max_depth` | int | Eligibility window |
| `weight` | int ≥ 0 | Weight among eligible prefixes when a roll succeeds |
| `stat_bonuses` | object | Flat additives: `max_hp`, `ac`, `evade` (number), `accuracy`, `ranged_accuracy`, `min_damage`, `max_damage`, `digestion_damage_per_tick` (omit = 0). `accuracy` affects melee and ranged (when species has ranged damage); `ranged_accuracy` affects ranged only. No `digest_time`. |
| `grant_abilities` | string[] | optional — ability tokens merged at apply time (e.g. `Slow`, `PreferVore`) |
| `requirements` | object | optional — entity-aware eligibility (see below) |

### `requirements` (per prefix)

All listed sub-conditions must pass. Omitted = no extra gate beyond alignment/depth/weight.

| Field | Type | Meaning |
|-------|------|---------|
| `ability_families` | string[] | Host must have ≥1 matching ability: family tokens `RangeN`, `SmiteN`, `RangedVoreN`, or exact fixed ids (`Slow`, `Hands`, …). |

**Roll model:** after the global prefix chance succeeds, build the candidate list (alignment + depth + requirements), then **one** weighted pick. Empty list → no prefix on that NPC.

Unknown prefix ids on load are soft-dropped (component cleared; display name restored from species).

## `floor_runes.json`

Three weighted-random floor runes per level (distinct tiles). All runes use glyph `0`; `fg` color distinguishes effect type. Placement and activation: `src/systems/floor_runes.py`.

### Top level

| Field | Type |
|-------|------|
| `schema_version` | int — must be `1` |
| `runes_per_floor` | int ≥ 0 — how many runes to place per floor (stock **3**); used by spawn **and** map feasibility. Omitted → `RUNES_PER_FLOOR` constant (3). **0** = no runes. Difficulty profiles may override via `runes_per_floor_override`. |
| `runes` | array |

### `runes[]`

| Field | Type |
|-------|------|
| `id` | string |
| `display_name` | string |
| `glyph` | string (1 char; must be `0` in stock data; must not be `#`) |
| `fg` | [r, g, b] |
| `examine` | string |
| `weight` | int > 0 |
| `min_depth` | int — inclusive |
| `max_depth` | int — inclusive |
| `effect` | object — see below |

### `effect` types (v1)

| `type` | Fields |
|--------|--------|
| `max_hp` | `amount` (int) |
| `accuracy` | `amount` (number) |
| `natural_ac` | `amount` (int) |
| `natural_evade` | `amount` (number) — permanent evade bonus bank |
| `accuracy_damage` | `accuracy`, `min_damage`, `max_damage` (zero a side to skip that bank) |

### `effect` piece fields (all types)

| Field | Type | Default | Meaning |
|-------|------|---------|---------|
| `pieces_per_bonus` | int ≥ 1 | `1` | Pieces needed for one full bonus unit (× difficulty `rune_pieces_multiplier`) |
| `pieces_granted` | int ≥ 1 | `1` | Pieces this rune awards on step-on |

Stock uses defaults (`1` / `1`) so every rune grants its full bonus immediately. `accuracy_damage` progresses **separable** banks (accuracy / min damage / max damage) for each non-zero sub-field.

## `macguffins.json`

Victory objects (macguffins): one instance per depth-eligible definition per floor (no weight). Step-on activation: `src/systems/macguffins.py` (PR2+).

### Top level

| Field | Type |
|-------|------|
| `schema_version` | int — must be `1` |
| `macguffins` | array |

### `macguffins[]`

| Field | Type |
|-------|------|
| `id` | string |
| `display_name` | string |
| `glyph` | string (1 char; must not be `#`) |
| `fg` | [r, g, b] |
| `examine` | string |
| `min_depth` | int — inclusive |
| `max_depth` | int — inclusive |
| `score` | int ≥ 0 — stored on past-run record; not displayed in v1 |

No `weight` field. Spawn is deterministic: at most one entity per eligible definition per floor.

## `entities.json`

### Required per entity

| Field | Type |
|-------|------|
| `id` | string |
| `display_name` | string |
| `glyph` | string (1 char) |
| `fg` | [r, g, b] |
| `alignment` | `good` \| `evil` \| `neutral` |
| `mobility` | `ground` \| `fly` \| `aquatic` \| `stationary` |
| `max_hp` | int |
| `evade` | number ≥ 0 (continuous; same scale family as accuracy) |
| `ac` | int |
| `accuracy` | number |
| `min_damage` | int |
| `max_damage` | int |
| `spawn.weight` | number ≥ 0 — **0** means never spawn (deprecated; keep id for old saves) |

Melee combat uses `accuracy`, `min_damage`, `max_damage`. Optional ranged counterparts (default to melee when omitted):

| Field | Type |
|-------|------|
| `ranged_accuracy` | number |
| `ranged_min_damage` | int |
| `ranged_max_damage` | int |

Used when entity has an implemented `SmiteN` ability (`ranged_*` also used by future `RangeN` Path ability).
| `spawn.min_depth` | int |
| `spawn.max_depth` | int |

### Optional

| Field | Type |
|-------|------|
| `examine` | string |
| `proper_name` | string \| null |
| `experience_points` | int — stored; gameplay ignores until XP system exists |
| `spawn.terrain` | `land` \| `water` (default `land`) |
| `spawn_requires_water` | bool |
| `digestion_damage_per_tick` | int (evil; default 3) |
| `digest_time` | int ≥ 1 (evil; default 6) — strike ticks at 0 HP before digest completes; omit when 6 |
| `vore_narratives` | object — see below |
| `digestion_complete` | object — `{ "OV": ["{predator} ...", ...], ... }` |
| `digestion_player_modal` | object — per-type variant arrays (see below) |
| `npc_vore_hit` | object — on-screen NPC vore **hit** log lines per type (`OV` / `CV` / `AV`); optional `{predator}` / `{prey}` |
| `npc_vore_miss` | object — on-screen NPC vore **miss** log lines per type |
| `offscreen_vore` | object — `{ "OV": ["..."], "CV": [...], "AV": [...] }` atmospheric log when NPC vore **succeeds** off-screen (optional `{predator}` / `{prey}`) |
| `offscreen_digest` | object — per-type arrays when NPC digestion **completes** off-screen |
| `introduction` | string[] — good-ally introduction lines with `{name}` placeholder (runtime `ProperName` assignment; see ally-improvement) |
| `introduction_log_category` | optional string — log color category for introduction lines (see **Inline log color markup** below) |
| `abilities` | string[] — see **Ability tokens** below |
| `placeholder` | bool (default `false`) — content marker only; **no combat rules**. Use for unfinished / stub species (see **Placeholder content checklist** below). Prefer also marking `examine` with `[placeholder]`. |

### Placeholder content checklist

When adding a **placeholder** species (utilitarian vore text OK until full write-up):

| Item | Requirement |
|------|-------------|
| Schema | Full valid entity: combat, spawn, alignment, mobility, glyph, fg |
| Mark | `"placeholder": true` and/or `[placeholder]` in `examine` / display_name |
| Evil vore | At least **OV** attempt + success; other types may be short single-variant stubs |
| Digestion / offscreen / npc_vore | Prefer minimal one-line stubs for keys the game looks up; match existing evil completeness practice |
| Good | Non-empty `introduction` if they should introduce; else omit |
| `id` | Stable snake_case — do not rename casually (save soft-drop) |
| Stock ship | New fillers should use `spawn.weight: 0` until a content PR enables them |

Gameplay treats placeholders like any other entity (spawn weights, AI, combat, vore). No special combat path.

### `introduction` parse rules

| Input | Result |
|-------|--------|
| Field omitted | `None` — entity cannot introduce at runtime |
| `[]` or invalid entries | **Load error** |
| Non-empty `string[]` | Parsed tuple of lines |

### Inline log color markup

Narrative and log strings MAY include inline markup: `[[category]]colored text[[/]]`. Unknown `[[tags]]` are left literal. Closing tag: `[[/]]` resets to the message default category.

**Canonical categories** (use these names in data):

| Category | Typical color role |
|----------|-------------------|
| `routine` | Default / grey log text |
| `danger` | Threats, harm |
| `caution` | Warnings |
| `positive` | Beneficial events |
| `magical` | Magic / special effects |
| `speech` | Dialogue / speech |
| `rare` | Rare / notable events |

**Aliases** (resolved the same as the canonical name):

| Alias | Canonical |
|-------|-----------|
| `grey`, `gray` | `routine` |
| `red` | `danger` |
| `yellow` | `caution` |
| `green` | `positive` |
| `cyan` | `magical` |
| `white` | `speech` |
| `magenta` | `rare` |

Example: `[[speech]]Hello[[/]]` or `[[cyan]]sparkle[[/]]`. Names are case-insensitive.

---

## `names.json`

Runtime proper names for good allies (keyed by entity `id`).

| Field | Type |
|-------|------|
| `schema_version` | int — must be `1` |
| `names` | object — keys = entity ids; values = non-empty `string[]` |

Example: `"knight": ["Sir Aldric", "Sir Gareth"]`. Duplicates across entities are allowed at runtime.

---

## `rescue_gratitude.json`

Shared log lines when the **player** frees a **good** ally from engulfment.

| Field | Type |
|-------|------|
| `schema_version` | int — must be `1` |
| `lines` | non-empty `string[]` — templates with `{name}` placeholder |

### Ability tokens (`abilities[]`)

Implemented v1 tokens (see `openspec/specs/npc-abilities/spec.md`):

| Token | Meaning |
|-------|---------|
| `Smite2` … `Smite9` | **Smite** targeting — LoS ranged at distance 2–N (ignores entities in between); log verb *smites* |
| `Range2` … `Range9` | **Path** targeting — beam at distance 2–N with ally blocking; log verb *shoots* |
| `SummonN <id>` | One-shot adjacent spawn (e.g. `Summon1 rabbit`) |
| `Coward` | Flee below 50% HP when threat visible |
| `Supercoward` | Flee at any HP when threat visible |
| `Erratic` | Move–attack–move sub-steps per turn |
| `Slow` | Skip every other player turn (odd `player_turn_count`) |
| `Fast` | Double action plan per world phase |
| `Knockback` | Push defender 1 tile on successful damage |
| `Lifedrain` | Heal attacker by damage dealt |
| `PreferVore` | When vore is otherwise legal, always attempt (skip decision roll) |
| `Wander` | Mindless drift — never target or chase; explore only (bump damage in passing) |
| `NoChase` | Evil only — chase visible quarry; give up immediately when quarry leaves LOS (no memory/momentum) |
| `Hands` | Bump closed doors to open (80%) or break to floor (20%); no move on bump; FOV-gated logs |
| `RangedVore2` … `RangedVore9` | Vore at Chebyshev distance 2–N with LOS; pull prey to predator tile on hit only |

Duplicate `SmiteN`, `RangeN`, or `RangedVoreN` on one entity each collapse to **max N** within that family at load. Unknown tokens warn and are dropped.

### `vore_narratives` shape

Each narrative type (`OV`, `CV`, `AV`) maps to an **array of variants**. The game picks **one variant at random** per attempt (respecting disabled types in options).

```json
"OV": [
  {
    "attempt": ["One or more modal lines for the attempt"],
    "success": ["Phase 1", "Phase 2", "..."]
  },
  {
    "attempt": ["Alternate attempt line"],
    "success": ["Alternate phase 1", "..."]
  }
]
```

A single variant may also be written as an object (shorthand for a one-element array).

### `digestion_player_modal` shape

Each narrative type maps to **variants**; one variant is chosen at random. Each variant has one or more **phases** shown in sequence (Enter advances).

```json
"OV": [
  {
    "phases": [
      "{predator}'s stomach churns around you.",
      "{predator} howls in triumph as it digests a great prize - you."
    ]
  },
  {
    "phases": ["{predator} rumbles with satisfaction as digestion finishes - you."]
  }
]
```

Shorthand: a string is one phase; a string array is one variant with multiple phases.

### Alignment (code — not in JSON)

- **evil** (wolf archetype): vore, digestion, evil movement blocking
- **good** (knight archetype): ally follow on descent, good movement blocking
- **neutral** (rabbit archetype): flee evil, neutral movement blocking

## Item spawn policy (stock)

- **Overlap:** `spawn_min_depth` / `spawn_max_depth` — weak gear rotates out on deep floors
- **Rarity:** weapons, armor, wands weight **1**; potions **3 / 2 / 1** (health / greater / power)
- **Cap:** at most **5** weighted floor placements per generation (`MAX_FLOOR_ITEM_PLACEMENTS`); health potion `spawn_min: 1` may add one more
- **Starter loadout:** dagger slot `a` wielded, robes slot `b` worn (not in JSON)
- **Catalog:** 12 weapons, 9 armor, 3 potions, 5 wands — see `openspec/specs/equipment-catalog/spec.md`

## `weapons.json`

### Required per weapon

| Field | Type |
|-------|------|
| `id` | string |
| `display_name` | string |
| `glyph` | string (1 char) |
| `fg` | [r, g, b] |
| `examine` | string |
| `min_damage` | int |
| `max_damage` | int |
| `accuracy_bonus` | number |
| `durability_max` | int |
| `spawn_weight` | number ≥ 0 — **0** means never spawn (deprecated) |
| `spawn_min_depth` | int |
| `spawn_max_depth` | int |

### Optional

| Field | Type |
|-------|------|
| `abilities` | string[] — ignored in v1 with warning |

## `armor.json`

### Required per armor

| Field | Type |
|-------|------|
| `id` | string |
| `display_name` | string |
| `glyph` | string (1 char) |
| `fg` | [r, g, b] |
| `examine` | string |
| `ac_bonus` | int |
| `evade_bonus` | number ≥ 0 — optional, default **0**; glancing / armor evade stacked in `effective_fighter` |
| `digestion_ac` | int |
| `durability_max` | int |
| `spawn_weight` | number ≥ 0 — **0** means never spawn (deprecated) |
| `spawn_min_depth` | int |
| `spawn_max_depth` | int |

## `potions.json`

### Required per potion

| Field | Type |
|-------|------|
| `id` | string |
| `display_name` | string |
| `glyph` | string (1 char) |
| `fg` | [r, g, b] |
| `examine` | string |
| `effect` | see **Potion effects** |
| `spawn_weight` | number ≥ 0 — **0** means never spawn (deprecated) |
| `spawn_min` | int — minimum count placed per floor after weighted spawn |
| `spawn_min_depth` | int |
| `spawn_max_depth` | int |

### Potion effects

| `effect` | Required extra fields | Notes |
|----------|----------------------|--------|
| `heal` | `heal_amount` ≥ 1 | Restore HP |
| `magic_mapping` | — | Mark all tiles explored; no free FOV |
| `haste` | `duration_turns` ≥ 1 | Extra player actions while active |
| `might` | `duration_turns` ≥ 1; optional `accuracy_bonus`, `min_damage_bonus`, `max_damage_bonus` | Temporary combat buff |
| `digestion_ward` | `duration_turns` ≥ 1 | Stock **potion of antacid**; nullifies dig damage + strikes |
| `teleport_delay` | `delay_min_turns` / `delay_max_turns` (default 3–5) | Delayed random land teleport; engulfs escape |
| `blink` | — | Free-cursor blink; only currently visible tiles; cancel free |
| `summon_ally` | — | Weighted good ally at current depth; place nearest free tile |

Optional fields default to 0 when omitted. Examine text should stay utilitarian and **number-free**; inspect may show heal amounts.

## `wands.json`

### Required per wand

| Field | Type |
|-------|------|
| `id` | string |
| `display_name` | string |
| `glyph` | string (1 char) |
| `fg` | [r, g, b] |
| `examine` | string |
| `effect` | `magic_missile` (v1) |
| `charges_max` | int |
| `charges_start` | int |
| `range` | int — Chebyshev distance |
| `min_damage` | int |
| `max_damage` | int |
| `accuracy` | number |
| `spawn_weight` | number ≥ 0 — **0** means never spawn (deprecated) |
| `spawn_min_depth` | int |
| `spawn_max_depth` | int |

## `throwables.json`

Consumed stackable Path ammo. No `range` field (player throws at any evil in LoS). Starter loadout: **5 rocks** in slot `c`.

### Required per throwable

| Field | Type |
|-------|------|
| `id` | string |
| `display_name` | string |
| `glyph` | string (1 char) |
| `fg` | [r, g, b] |
| `examine` | string |
| `min_damage` | int |
| `max_damage` | int |
| `accuracy_bonus` | number |
| `spawn_weight` | number ≥ 0 — **0** means never spawn (deprecated) |
| `spawn_min_depth` | int |
| `spawn_max_depth` | int |
| `spawn_stack_min` | int ≥ 1 — optional, default **1**; floor pile size low end |
| `spawn_stack_max` | int ≥ `spawn_stack_min` — optional, default `spawn_stack_min`; floor pile size high end (uniform inclusive) |

Stock throwables use **`spawn_stack_min` 3 / `spawn_stack_max` 4** so floor finds are packs, not single stones.

### Stock catalog (9 ids, depth 1–20)

`rock`, `brick`, `dart`, `throwing_knife`, `throwing_axe`, `shuriken`, `javelin`, `chakram`, `ceramic_pot` — depth windows and balance in `data/throwables.json`.