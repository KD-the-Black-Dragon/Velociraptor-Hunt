# Tasks: Start at depth (secret menu)

**Change:** `add-depth-jump-start`

## PR1 — Secret depth-jump new game

- [x] Add `data/depth_jump_start.json` + loader + `SCHEMA.md` section
- [x] Extract or share item strength / eligibility helpers (data-driven pools)
- [x] Implement `build_depth_jump_loadout` (gear, consumables, simulated runes)
- [x] Add `initialize_floor_new_at_depth` / `new_game(start_depth=...)`
- [x] Add `depth_entry.py` UI (validation message, Escape cancel)
- [x] Wire Ctrl+G on main menu → name → depth → overwrite → play
- [x] Add `openspec/specs/depth-jump-start/spec.md` (behavioral requirements)
- [x] Tests: loadout builder, depth entry, menu chord, edge cases
- [x] `testing-checklist-pr1.md` + manual checklist in chat

## Final acceptance (after PR1 sign-off)

- [x] Full `pytest tests/` per AGENTS.md procedure
- [x] `testing-checklists.md`, `acceptance-report.md`
- [x] Archive to `openspec/changes/archive/2026-07-12-add-depth-jump-start/`
- [x] Update modding spec for `depth_jump_start.json` if shipped as replace file