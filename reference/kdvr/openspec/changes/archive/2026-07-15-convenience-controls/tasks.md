# Tasks: convenience-controls

**Status:** Accepted — archived 2026-07-15  
**Spec target:** `openspec/specs/convenience-controls/spec.md`

---

## PR1 — Autoexplore + shared infrastructure

**Auth:** user authorized 2026-07-15.

- [x] Extract `src/systems/danger_interrupts.py`; refactor `rest.py` (behavior-preserving)
- [x] Extract `src/systems/player_navigation.py`; thin `src/sim/navigation.py` re-export
- [x] Implement `src/systems/autoexplore.py` (session, planner, frame advance)
- [x] Wire `GameEngine` / `engine_turn` / `app` / `main.run_loop` (mirror rest)
- [x] Add `` ` `` handler in `engine_input.py`
- [x] Messages: `autoexplore_start`, `autoexplore_complete`, `autoexplore_engulfed`, `autoexplore_enemy_in_sight`, `autoexplore_too_injured`
- [x] Help overlay row for autoexplore
- [x] `modal_snapshot` label `"autoexplore"`
- [x] `openspec/specs/convenience-controls/spec.md` — autoexplore requirements + scenarios
- [x] `tests/test_autoexplore.py`
- [x] Run targeted tests: `pytest tests/test_autoexplore.py tests/test_rest_until_healed.py -v` — **28 passed**
- [x] Post manual checklist PR1 in chat; wait for designer sign-off

---

## PR2 — Force-attack

**Auth:** user authorized 2026-07-15 (after PR1 sign-off).

- [x] `try_force_attack` in `src/systems/combat.py`
- [x] `is_ctrl_direction` in `input_handlers.py` + gameplay handler
- [x] Message: `attack_empty_air`
- [x] Help overlay row for Ctrl+direction
- [x] Spec delta — force-attack requirements + scenarios
- [x] `tests/test_force_attack.py`
- [x] Run targeted tests: `pytest tests/test_force_attack.py -v` — **7 passed**
- [x] Post manual checklist PR2 in chat; wait for designer sign-off

---

## Final acceptance (after PR2 sign-off)

**Auth:** PR2 sign-off 2026-07-15.

- [x] `testing-checklists.md` + `acceptance-report.md` in change folder
- [x] Archive to `openspec/changes/archive/2026-07-15-convenience-controls/`
- [x] Update `AGENTS.md` current change pointer
- [x] Full suite per `AGENTS.md` procedure (4 workers) — 1667 pass; 18 pre-existing failed-twice