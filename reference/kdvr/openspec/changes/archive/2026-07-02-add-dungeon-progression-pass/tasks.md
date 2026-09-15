# Tasks: add-dungeon-progression-pass

One PR at a time. Check off when merged and playtested.

## PR0 — OpenSpec bootstrap

- [x] `proposal.md`, `design.md`, `tasks.md` in change folder
- [x] `testing-checklist-pr0.md` … `testing-checklist-pr5.md` stubs
- [x] `openspec/WORKFLOW.md` active change pointer updated
- [x] No gameplay code

## PR1 — Dungeon spawn config loader

- [x] `data/dungeon_spawn.json` + loader + `compute_target_npc_count()`
- [x] `tests/test_dungeon_spawn_config.py` (validation + tile distribution measurement)
- [x] `data/SCHEMA.md` updated
- [x] Targeted pytest for PR1

## PR2 — Density-driven NPC spawning

- [x] Rewrite `spawn_floor_population()` (filtered-union draws, `effective_target`, water placement pool)
- [x] `good_aligned_weight_at_depth()` in engine; remove knight coupling
- [x] Migrate stock-count tests to fixture/mechanical assertions
- [x] Production `src/` spawn call-site guard test
- [x] Targeted pytest for PR2
- [x] Manual playtest checklist PR2

## PR3 — Floor rune placement

- [x] `data/floor_runes.json` + loader
- [x] `FloorRune` component, `spawn_floor_rune()`, render, NPC blocking + player passthrough
- [x] Engine spawn hook (after items); **no activation hook**
- [x] `tests/test_floor_runes_pr3.py`
- [x] Targeted pytest for PR3
- [x] Manual playtest checklist PR3

## PR4 — Rune activation and progression

- [x] Ad-hoc: **3 runes per floor** (`RUNES_PER_FLOOR`); all glyphs **`0`**, color by effect
- [x] `PlayerProgression`, `apply_rune_effect()`, step-on handler
- [x] `effective_fighter()` integration, single-frame flash, log messages
- [x] `tests/test_floor_runes_pr4.py`; PR3 tests updated for 3 runes + glyph `0`
- [x] Targeted pytest for PR4
- [x] Manual playtest checklist PR4

## PR5 — Spec sync and acceptance

- [x] `openspec/specs/dungeon/spec.md`, `npc-data/spec.md`, new `floor-runes/spec.md`
- [x] `README.md`, `acceptance-report.md`
- [x] Archive to `openspec/changes/archive/2026-07-02-add-dungeon-progression-pass/`
- [x] Full `pytest tests/` (457 passed)
- [ ] Final manual playtest checklist