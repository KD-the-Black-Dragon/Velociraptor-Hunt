# Acceptance Report: add-save-load

**Date:** 2026-07-05  
**Scope:** Single-slot autosave with rotating backups, background coordinator, menu load/new-game overwrite, Ctrl+Q/S, game-over permadeath wipe, graceful save-failure handling (PR1–PR5)

## Automated verification

### Change gate (save/load)

```bash
python -m pytest tests/test_save_snapshot.py tests/test_save_store.py tests/test_save_coordinator.py tests/test_save_menu_pr4.py tests/test_save_game_over_pr5.py tests/test_save_write_failure.py -q
```

| Result | Count |
|--------|-------|
| **PASS** | **39** |

### Full suite

```bash
python -m pytest -q
```

| Result | Count |
|--------|-------|
| Passed | 875 |
| Failed | 31 |
| Warnings | 98 |
| Duration | ~28 min |

**Save/load regressions (fixed at acceptance):** `test_name_entry`, `test_options_menu`, `test_ui_preset_apply`, `test_acceptance::test_ac_quit_ctrl_q` — `App()` now probes real `{user_data}/saves/`; tests use `app_with_isolated_save(tmp_path)` helper. *(Post-archive: saves relocated to per-user data dir via `src/user_data.py`.)*

**Remaining failures (not introduced by this change):** spawn/wolf-count flakes (`iter_wolves` empty), stale JSON load assertions (`entities.json`, `dungeon_spawn.json`), vore modal/UI `StopIteration` flakes, erratic movement tie-breaks, ally rescue LOS tests, digestion combat-immunity flake. No failures in the save/load gate.

## Manual verification

- [x] PR1–PR5 playtest sign-off (user)
- [x] Save failure graceful handling sign-off (user — Notepad lock; no crash)
- [x] Final acceptance sign-off (2026-07-05)

## Requirement coverage

| PR | Delivered |
|----|-----------|
| PR1 | Snapshot schema v1; in-memory round-trip restore |
| PR2 | `SaveStore` rotation, SHA256, probe/load fallback, `delete_all` |
| PR3 | `SaveCoordinator` worker, idle gate, cadence triggers |
| PR4 | Menu probe, Load Game, overwrite confirm, Ctrl+Q/S |
| PR5 | Game over wipe; `save-load` + `main-menu` spec updates |

## Spec updates

- `openspec/specs/save-load/spec.md` — **new**
- `openspec/specs/main-menu/spec.md` — Load Game, overwrite, conditional menu, Ctrl+S, game-over wipe
- `openspec/specs/core-roguelike/spec.md` — save/load no longer out of scope

## Deferred / follow-up

- **Door spite — distant wolf should approach door** — `openspec/changes/todo/spec.md`
- **Performance throttling** — `openspec/changes/todo/spec.md`
- Stabilize wolf-count / vore-modal flakes in full suite (separate hygiene pass)

## Archive

`openspec/changes/archive/2026-07-05-add-save-load/`