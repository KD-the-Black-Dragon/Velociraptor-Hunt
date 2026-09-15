# Tasks: Data-Driven NPC Definitions

Trait catalog approved 2026-07-01. Check off as completed.

## PR 1: Loaders, schema, alignment profiles

- [x] `data/entities.json` + `data/SCHEMA.md`
- [x] Stub `data/weapons.json`, `armor.json`, `potions.json`, `wands.json`
- [x] `entity_loader.py`, `alignment_profiles.py`, `abilities.py` shell
- [x] Ignore-unknown + required-field validation tests
- [x] `testing-checklist-pr1.md`

## PR 2: Combat range + generic spawn

- [x] Combat: `accuracy`, `evade`, `ac`, `min_damage`, `max_damage` per spec formulas (retire `Fighter.power` / `Fighter.defense`)
- [x] `spawn_from_definition()` + weight-based `spawn_floor_population()`
- [x] Remove per-species spawn functions and species constants
- [x] Tests for spawn parity / weighting
- [x] `testing-checklist-pr2.md`

## PR 3: Evil vore from data

- [x] `vore_narratives` in JSON; load-time index by `id`
- [x] Evil alignment auto-applies vore + digestion (no ability flags in data)
- [x] Remove `vore_content.py` hardcode and wolf fallback
- [x] `testing-checklist-pr3.md`

## PR 4: Terrain, depth, followers

- [x] `spawn.terrain`, `spawn_requires_water`, depth filters
- [x] Good follower deduction from weighted good pool
- [x] `testing-checklist-pr4.md`

## PR 5: Spec and acceptance

- [x] `openspec/specs/npc-data/spec.md`
- [x] Cross-spec updates; README modding section
- [x] `testing-checklists.md`, `acceptance-report.md`, archive