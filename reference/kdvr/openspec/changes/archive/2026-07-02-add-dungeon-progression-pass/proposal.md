# Proposal: Dungeon Progression Pass

## Why

Floor difficulty today is **flat**: NPC count equals the **sum of spawn weights** (stock ~17 land + 2 sharks), not map size or depth. That bakes in **implicit species quotas** (6 wolves, 5 knights, etc.) and couples follower deduction to `knight` weight. There is no permanent in-run progression beyond equipment. Players need **depth-scaled density**, **species-agnostic spawning**, and **explorable floor runes** that grant lasting power.

## What Changes

### Density-driven NPC spawning

- New **`data/dungeon_spawn.json`** — average NPC density per depth band, with per-floor variance
- Spawn flow: generate map → count valid tiles → compute target → **`effective_target` independent weighted draws** from `entities.json`
- **No per-species minimums or maximums**; unified land+water pool (aquatic NPCs compete for slots — not additive guarantees)
- **Good follower deduction** species-agnostic: `effective_target = max(0, target - good_reduction)` — total count drops, no backfill
- Aquatic placement fallback when water is near entrance; reject-and-retry on empty terrain pools
- One-time spawn at `new_game()` / `descend_floor()` only

### Floor runes

- New **`data/floor_runes.json`** — weighted random rune types with depth gates
- **Three runes per floor** on distinct tiles, placed after NPCs and items, at least **30 movement steps** (BFS path distance on floor tiles) from entrance; no max distance; relaxes threshold one step at a time on cramped maps
- All runes use glyph **`0`** (numeral zero); **color** distinguishes effect type
- Step-on activation (player only): permanent max HP, accuracy/damage, or natural AC buff
- Single-frame screen flash; rune vanishes immediately; `PlayerProgression` composes with equipment

## Out of Scope

- Classic XP / character levels
- Mid-level monster respawn
- Guaranteed specific rune types or shark counts
- Item spawn rule overhaul (`spawn_min` potions unchanged)
- Stairs up, loot scaling, HUD combat-stat display

## Capabilities

### New

- `floor-runes` — catalog, placement, activation, permanent buffs

### Modified

- `dungeon` — density-driven spawn; remove fixed 6/5/6/2 and "exactly two sharks" requirements; depth difficulty via density
- `npc-data` — weight = probability only; remove stock parity scenarios; follower deduction semantics

## Success Criteria

- NPC count scales with map tiles and depth band config (fixture tests, not stock JSON counts)
- No code paths enforce per-species spawn quotas
- Three runes per floor on distinct tiles; player step-on applies buff once per rune; rune removed
- Good followers reduce total fresh spawns without knight coupling
- Full `pytest tests/` green on PR5

## Decisions (locked for v1)

| # | Decision |
|---|----------|
| 1 | Density from `dungeon_spawn.json`; gumball draws from `entities.json` |
| 2 | Unified land+water target (sharks probabilistic, not additive) |
| 3 | `effective_target` reduction for good followers — no backfill |
| 4 | `good_reduction` capped by total good-aligned weight at depth |
| 5 | One rune/floor; weighted random type; FLOOR tiles only; min **30** path steps from entrance with threshold relaxation fallback |
| 6 | Runes block NPC movement; player may step on to activate |
| 7 | Single-frame screen flash (current render loop) |
| 8 | Tests use fixtures — no assertions against stock JSON counts |