# Tasks: Good NPC spawn quota

**Change id:** `good-npc-spawn-quota`

## PR1 — Data, spawn algorithm, tests, specs

- [x] **PR1** — Implement good spawn quota
  - [x] Add `good_spawn_limit` to `DifficultyProfile` + loader (int ≥ 0; omit → default 2)
  - [x] Stock `data/depth_scaling.json`: easier **3**, normal/hard/nightmare **2**
  - [x] SCHEMA + `balance` / `npc-data` / `dungeon` live specs
  - [x] `spawn_floor_population` (or helper):
    - [x] Resolve limit from difficulty
    - [x] Eligible-goods gate (weight, depth, terrain/pools) — 0 if none
    - [x] `brought = len(followers)`; if `brought >= limit` skip new goods
    - [x] Else weighted-spawn `limit - brought` goods
    - [x] Density pass: evil+neutral only; **no** `good_follower_reduction`
  - [x] `engine_floor.spawn_floor_population_and_runes`: pass follower count; remove weight-cap reduction
  - [x] Remove/repurpose `good_aligned_weight_at_depth` density use
  - [x] Targeted tests (fixtures, not live balance numbers):
    - [x] No eligible good → 0 new goods
    - [x] 0 / 1 / ≥limit brought
    - [x] Easier limit 3
    - [x] Density draws never pick good when under/at quota path
  - [x] Manual checklist file `testing-checklist-pr1.md`

## PR2 — Accept / archive

- [x] **PR2** — Designer playtest sign-off
  - [x] Checklist complete
  - [x] Archive change; update `AGENTS.md` pointer

---

**Do not implement any PR until the designer explicitly authorizes that PR.**
