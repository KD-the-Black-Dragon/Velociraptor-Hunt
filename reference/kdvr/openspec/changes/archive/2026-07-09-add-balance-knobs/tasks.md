# Tasks: add-balance-knobs

**Active PR:** *(none — change accepted and archived 2026-07-09)*  
**Rule:** One PR at a time.

Full design: `design.md`. Package summary: `proposal.md`.

---

## PR0 — OpenSpec scaffolding

- [x] `proposal.md`, `design.md`, `tasks.md`
- [x] AGENTS.md **Current change pointer** → `add-balance-knobs`
- [x] Designer decisions: evil-only; no follower re-bake; content tune in-change
- [x] Design: difficulty presets; dual-int; no digest_time scale; separable Acc/Dam; XP out
- [x] Design: Options-only difficulty; Easy–Nightmare; density+rune economy; separate min/max
- [x] Design: NPC prefixes / Elite; Past Runs difficulty; reject loot austerity, regen-by-diff, in-run HUD
- [x] Designer authorizes coding (PR1)

---

## PR1 — Depth scaling (dual-int) + difficulty data model

- [x] `data/depth_scaling.json` with easy/normal/hard/nightmare; Normal all-zero; evil-only
- [x] Dual-int schedule: `per_floor`, `every_n_floors`, `bank_amount`, `start_depth`; accuracy `unit`
- [x] Stats: max_hp, ac, evade, accuracy, min_damage, max_damage (separate), **digestion_damage_per_tick** — not digest_time
- [x] Bake in `spawn_from_definition`; summon path with `floor_depth`
- [x] Followers: no re-bake; ranged gate
- [x] Loader + SCHEMA + whole-file mod layer; balance/npc-data specs
- [x] Fixture tests (incl. 1.25-style dual-int) — 17 passed
- [ ] Manual playtest Normal = current feel

---

## PR1b — Options difficulty + snapshot + density/rune economy + Past Runs

- [x] Options: list/cycle Easy / Normal / Hard / Nightmare from JSON
- [x] New Game snapshots Options `difficulty_id` (immutable mid-run)
- [x] Save/load + unknown id → default + notice
- [x] Apply `density_multiplier` at spawn count
- [x] Apply `runes_per_floor_override` + **integer** `rune_pieces_multiplier` (≥ 1)
- [x] **Past Runs:** persist difficulty on record; **show on board** (not in-run HUD)
- [ ] Manual playtest all four difficulties + Past Runs column

---

## PR2 — Piece-based floor runes (separable Acc/Dam)

- [x] `pieces_per_bonus` / `pieces_granted` (default 1)
- [x] Banks: max_hp, accuracy, ac, min_damage, max_damage
- [x] `accuracy_damage` splits into active sub-field banks
- [x] Sticky `need_frozen`; runtime log; status HUD; save keys
- [x] Fixture tests; floor-runes spec
- [ ] Manual playtest pieces=1 = current feel
- [x] Past Runs order: difficulty before depth (`Nightmare - Depth 1`)

---

## PR3 — Data-driven `runes_per_floor`

- [x] Top-level field; spawn + map_gen feasibility single source
- [x] `0` behavior defined; spec de-hardcode “exactly three”
- [x] Tests count 0 and ≠3
- [ ] Manual playtest stock still 3 runes

---

## PR4 — NPC prefix system + stock Elite

- [x] `data/npc_prefixes.json` + loader/registry; SCHEMA
- [x] `NpcPrefix` component; DisplayName = `{display_prefix}{base}`
- [x] Spawn: depth bake → prefix roll → flat `stat_bonuses`
- [x] Per-difficulty `prefix_spawn` chance (0 on Normal until PR5)
- [x] Floor population only (no random prefix on summons v1)
- [x] Save: prefix id; unknown id soft-drop
- [x] Tests: Elite name, bonuses, soft-drop, no summon elite
- [ ] Manual playtest (stock chance 0; optional force chance in JSON)

---

## PR4b — Placeholder field + docs only

- [x] Optional `placeholder: bool`; SCHEMA checklist
- [x] No new positive-weight stock species
- [x] Fixture-only tests
- [ ] Manual: stock still five species / no feel change

---

## PR5 — Designer tuning (required in this change)

- [x] Easy–Nightmare curves (steepen descent; protect floor 1)
- [x] Density + rune economy + **elite/prefix_spawn** per difficulty
- [x] Elite flat bonuses (stock elite unchanged; chance enabled by difficulty)
- [x] Warding `pieces_per_bonus: 2` (milder early AC leaps)
- [x] 4 placeholder fillers: cave_rat, giant_spider, kobold, tunnel_slug
- [x] Manual playtest all difficulties; confirm Past Runs difficulty
- [x] Tests still fixture-pinned (no live deep-floor oracles)

---

## PR6 — Acceptance + archive

- [x] Acceptance + checklists; full suite `-n 6`
- [x] Archive; clear AGENTS pointer

---

## Out of scope / rejected

- [ ] ~~XP / kill-leveling~~
- [ ] ~~digest_time depth scaling~~
- [ ] ~~Loot austerity by difficulty~~
- [ ] ~~Natural regen rate by difficulty~~
- [ ] ~~In-run difficulty HUD~~
- [ ] ~~bands schedule mode~~
- [ ] ~~Per-entity depth multipliers~~ (unless later)
