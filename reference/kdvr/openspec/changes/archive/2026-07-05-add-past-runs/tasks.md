# Tasks: Game Over Stats + Past Runs

**Status:** Accepted — archived 2026-07-05.

## PR1 — Run statistics + save round-trip

- [x] Add `RunStats` on `GameEngine` (monsters defeated, runes collected)
- [x] Increment at player-credited defeat sites (`_perform_attack`, `perform_wand_attack`, struggle defeat)
- [x] Increment `runes_collected` in `try_activate_floor_rune` on success
- [x] Persist `run_stats` in save snapshot (backward-compatible defaults)
- [x] Unit tests: increment rules, snapshot round-trip
- [x] Run targeted pytest for PR1
- [x] Deliver manual checklist (`testing-checklist-pr1.md`)

## PR2 — Ending model + Past Runs store

- [x] Add `GameOverEnding` + `format_game_over_ending()`
- [x] Refactor `GameOverState` (drop `score`/`digested_by`; add ending + stats + depth)
- [x] Implement `PastRunsStore` (`{user_data}/past_runs.json`, probe, append, cap 65535, sort helper)
- [x] Append record in `GameOverState.open()`; per-user path via `src/user_data.py`
- [x] Wire digestion game over to `ending_kind="digested"`
- [x] Unit tests: store, cap, sort order, formatter
- [x] Run targeted pytest for PR2
- [x] Deliver manual checklist (`testing-checklist-pr2.md`)

## PR3 — Game over modal stats

- [x] Update `render_game_over()` with monsters, runes, depth, formatted ending
- [x] Update engine render + digestion open call sites
- [x] Update/remove tests that reference `score` / `digested_by` params
- [x] Run targeted pytest for PR3
- [x] Deliver manual checklist (`testing-checklist-pr3.md`)

## PR4 — Past Runs menu screen

- [x] Rename menu option **High Scores** → **Past Runs**; `MenuAction.PAST_RUNS`
- [x] `build_menu_options(past_runs_available=...)`; probe on menu enter
- [x] Replace `STUB_SCORES` with scrollable `PAST_RUNS` phase (`past_runs_screen.py`)
- [x] Reuse log-overlay scroll keys + footer pattern
- [x] Tests: menu omission when empty, navigation, stub removal
- [x] Run targeted pytest for PR4
- [x] Deliver manual checklist (`testing-checklist-pr4.md`)

## PR5 — Specs + acceptance

- [x] Create `openspec/specs/past-runs/spec.md`
- [x] Update `openspec/specs/main-menu/spec.md` (Past Runs, gating, game over recap)
- [x] Update `openspec/specs/save-load/spec.md` (`run_stats`, coordinator wipe)
- [x] Run full pytest suite
- [x] Write `acceptance-report.md` and consolidate `testing-checklists.md`
- [x] Archive to `openspec/changes/archive/2026-07-05-add-past-runs/`
- [x] Update `openspec/WORKFLOW.md` active change pointer
- [x] Deliver manual checklist (`testing-checklist-pr5.md`)