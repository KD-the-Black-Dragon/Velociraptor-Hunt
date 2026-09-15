# Tasks: Save / Load System

**Status:** Active — design locked 2026-07-05.

## PR1 — Snapshot schema + round-trip restore

- [x] Define `save_format_version` 1 envelope + `run` payload schema
- [x] Implement `GameEngine` → `SaveSnapshot` (entity id assignment, component coverage)
- [x] Implement `GameEngine.from_snapshot()` (registry rebuild, entity remap, FOV refresh)
- [x] Unit tests: player, map explored, inventory, NPC AIState, Predator.prey, message log, progression
- [x] Run targeted pytest for PR1
- [x] Deliver manual checklist (`testing-checklist-pr1.md`) — N/A until file I/O; engine-only smoke via tests

## PR2 — Rotating file store

- [x] `SaveStore` in `{user_data}/saves/`: write, rotate (primary + 3 backups), `payload_sha256`
- [x] Per-user saves dir via `src/user_data.py` (post-archive: no longer `data/saves/` in project tree)
- [x] `probe()` and `load_best()` with corruption skip chain
- [x] `delete_all()` for slot wipe
- [x] Unit tests: rotation, corrupt primary fallback, probe, delete
- [x] Run targeted pytest for PR2
- [x] Deliver manual checklist (`testing-checklist-pr2.md`)

## PR3 — Background autosave coordinator

- [x] `SaveCoordinator` worker thread + coalescing queue
- [x] Stable-state gate (no save during blocking modals)
- [x] Triggers: every 15 player turns OR 30s; after `descend_floor()`; every turn while player `Engulfed`; initial save on PLAY enter
- [x] Integration hook in `GameEngine` post-turn
- [x] Unit/integration tests for gate + scheduling
- [x] Run targeted pytest for PR3
- [x] Deliver manual checklist (`testing-checklist-pr3.md`)

## PR4 — Menu + quit save

- [x] `SaveStore.probe()` on menu enter; omit Load Game from menu when no save (Option B)
- [x] Replace `STUB_LOAD` with real load → `PLAY`
- [x] New Game overwrite confirm modal (capital **Y**); delete saves only after name confirm + engine create
- [x] Ctrl+Q (idle gate) → quit modal + background save (even if quit canceled); **Y** → menu
- [x] Ctrl+S (idle gate) → main-thread save + "Game saved." message
- [x] Tests: menu enablement, overwrite flow, quit save
- [x] Run targeted pytest for PR4
- [x] Deliver manual checklist (`testing-checklist-pr4.md`)

## PR5 — Game Over wipe + specs

- [x] `game_over.open()` → `SaveStore.delete_all()` immediately
- [x] Create `openspec/specs/save-load/spec.md`
- [x] Update `openspec/specs/main-menu/spec.md` (Load Game, overwrite confirm)
- [x] Run targeted pytest for PR5
- [x] Deliver manual checklist (`testing-checklist-pr5.md`)

## Acceptance (after PR5 sign-off)

- [x] Write `acceptance-report.md` and consolidate `testing-checklists.md`
- [x] Run full pytest suite
- [x] Archive to `openspec/changes/archive/YYYY-MM-DD-add-save-load/`
- [x] Update `openspec/WORKFLOW.md` active change pointer
- [x] Update `openspec/changes/todo/spec.md` if any deferred items addressed (N/A — no deferred items addressed)