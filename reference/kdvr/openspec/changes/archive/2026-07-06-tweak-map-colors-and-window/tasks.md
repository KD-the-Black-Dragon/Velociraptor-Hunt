# Tasks: tweak-map-colors-and-window

One PR at a time. Sequential order: **PR0 → PR1 → PR2 → PR3**. Check off when merged and playtested.

## PR0 — OpenSpec bootstrap

- [x] `proposal.md`, `design.md`, `tasks.md` in change folder
- [x] `testing-checklist-pr0.md` … `testing-checklist-pr3.md` stubs
- [x] `openspec/WORKFLOW.md` active change pointer updated
- [x] User review of OpenSpec documents
- [x] No gameplay code

## PR1 — Grey visible map tile colors

- [x] `src/systems/render.py` — update `LIGHT_FLOOR`, `LIGHT_WALL`, `LIGHT_DOOR` only
- [x] `tests/test_map_tile_colors.py` — visible floor/wall/door RGB; stairs/water unchanged
- [x] Targeted pytest for PR1
- [x] Deliver manual checklist (`testing-checklist-pr1.md`)

## PR2 — Window persistence, first-launch sizing, fullscreen

**Depends on PR0 (docs). Independent of PR1 merge order (may merge after PR1).**

- [x] `src/ui/window_state.py` — `WindowPreferences`, `WindowSessionState`, display helpers, fullscreen toggle
- [x] `src/ui/window_controller.py` — startup/resize/fullscreen orchestration
- [x] `src/settings_coordinator.py` — background `settings-coordinator` worker (coalesced writes)
- [x] `src/settings_store.py` — `window` block load/save/validation
- [x] `src/main.py` — startup restore, resize enqueue, coordinator `close()` in `finally`
- [x] `src/options_menu.py` — `Fullscreen: Off | On` row
- [x] `src/app.py` — pass `context` for immediate fullscreen layout refresh
- [x] `tests/test_window_state.py`
- [x] `tests/test_settings_coordinator.py`
- [x] `tests/test_settings_store_window.py`
- [x] `tests/test_options_fullscreen.py`
- [x] Targeted pytest for PR2
- [x] Deliver manual checklist (`testing-checklist-pr2.md`)

## PR3 — Spec sync and acceptance

**Depends on PR1, PR2.**

- [x] Update `openspec/specs/core-roguelike/spec.md` — visible map tile colors
- [x] Update `openspec/specs/ui-layout/spec.md` — window persistence, first launch, fullscreen
- [x] Update `openspec/specs/main-menu/spec.md` — Options fullscreen row
- [x] `README.md` — brief window/settings note
- [x] `acceptance-report.md`
- [x] Archive to `openspec/changes/archive/2026-07-06-tweak-map-colors-and-window/`
- [x] Full `pytest tests/`
- [x] Final manual playtest checklist (`testing-checklist-pr3.md`)