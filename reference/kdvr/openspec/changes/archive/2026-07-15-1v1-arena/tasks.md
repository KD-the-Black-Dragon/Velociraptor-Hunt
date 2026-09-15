# Tasks: 1v1 arena

**Change:** `1v1-arena`  
**Design:** `design.md` (approved 2026-07-15)

---

## PR1 — Interactive arena (Ctrl+B)

- [x] Add `src/arena_map.py` — `build_arena_map` (1×10 hall, walls, aquatic water tile)
- [x] Add `src/arena.py` — `initialize_arena` (map, spawn player/enemy, loadout, flags)
- [x] Add `src/entity_entry.py` — typed id entry, three-column evil id list (display-only), validation messages
- [x] Add `is_ctrl_b` in `src/menu.py`; wire `AppPhase.ENTITY_ENTRY` in `src/app.py`
- [x] Engine flags: `arena_mode`, `arena_enemy_id`, `arena_victory_active`; `floor_depth = spawn.min_depth`
- [x] Save isolation: skip autosave / writes when `arena_mode`; Ctrl+S no-op with `"Game saved."` message
- [x] Victory: freeze on enemy defeat, modal `You have defeated the {name}!`, Enter → main menu
- [x] Defeat: normal digestion game-over recap → main menu; `level_warped=true` skips Past Runs
- [x] Add `openspec/specs/1v1-arena/spec.md` (interactive requirements; bot deferred to PR2 section stub OK)
- [x] Tests: entity entry validation, map spawn positions, loadout depth, save no-op, victory hook, past-runs skip
- [x] `testing-checklist-pr1.md` + manual checklist in chat

---

## PR2 — Headless arena bot + spec completion

- [x] Add `src/sim/arena_policy.py` — bump visible evil, else move right; no consumables
- [x] Add `src/sim/arena_runner.py` — single trial loop (1000 turn cap, win/draw detection)
- [x] Add `src/sim/arena_batch.py` — batch aggregation + CSV formatting
- [x] Add `tools/sim_arena.py` — 10 trials × all Evil ids, `--difficulty`, `--seed`, mods honored
- [x] CSV: `enemy_id`, `min_spawn_depth`, `player_wins`, `enemy_wins`, `player_win_hp_remaining`, `enemy_win_hp_remaining`; blank line between entities; seed in output
- [x] Complete `openspec/specs/1v1-arena/spec.md` bot requirements
- [x] Tests: policy navigation, trial outcomes, draw handling, CSV row shape
- [x] `testing-checklist-pr2.md` + manual checklist in chat

---

## Final acceptance (after PR2 sign-off)

- [x] Full `pytest tests/` per AGENTS.md procedure
- [x] `testing-checklists.md`, `acceptance-report.md`
- [x] Archive to `openspec/changes/archive/2026-07-15-1v1-arena/`
- [x] Update `AGENTS.md` active change pointer

---

## Current PR

**Archived** — 2026-07-15.