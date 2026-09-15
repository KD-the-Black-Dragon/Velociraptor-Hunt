# Proposal: Data-Driven NPC Definitions

## Why

NPC species, stats, spawn rules, and vore text are hardcoded in Python (`spawn.py`, `constants.py`, `vore_content.py`). Adding a creature requires code changes.

This change externalizes definitions to **`data/entities.json`** so new creatures are added by editing JSON. Alignment (`good` / `evil` / `neutral`) drives faction behavior via code profiles archetyped on knight, wolf, and rabbit — data stays minimal.

## What Changes

- **`data/entities.json`** — NPC trait definitions (identity, alignment, combat, spawn weight, mobility, evil vore text)
- **Alignment profiles in code** — evil = vore + digestion; good = ally follow; neutral = flee evil; movement blocking per alignment
- **Weight-based spawn** — no fixed per-species counts
- **Combat** — `accuracy`, `min_damage`, `max_damage` per entity
- **`abilities[]`** — optional modifier strings (`Range3`, …); unknown ignored
- **Item stubs** — `weapons.json`, `armor.json`, `potions.json`, `wands.json` (traits only; wiring later)
- **Ignore-unknown** — unimplemented traits/abilities log a warning, not a crash

## Out of Scope

- Implementing every stubbed item trait
- Ranged combat (`RangeN`) until ability registered
- Hot-reload mid-run
- XP, loot drops, resistances, senses (reserved or excluded per design)

## Capabilities

### New

- `npc-data` — external definitions, alignment profiles, spawn weights, ignore-unknown

### Modified

- `enhancements-3`, `dungeon`, `vore`, `digestion`, `core-roguelike` (combat damage model)

## Success Criteria

- Current four species reproducible from `entities.json` only
- New fifth species in JSON spawns with no Python edits (given known traits)
- `experience_points` in JSON → ignore warning; game runs
- Full pytest green after implementation

## Decisions (locked)

| # | Decision |
|---|----------|
| 1 | JSON |
| 2 | Weight-based spawn immediately |
| 3 | Trait catalog per `design.md` (no ✅/🔶/❌ tiers — user edited list directly) |
| 4 | Items: four separate JSON stubs |
| 5 | Vore narrative key: `id` |