# Tasks: add-debug-support

One PR at a time. Sequential order: **PR1 → PR2 → PR3 → PR4 → PR5**. Check off when merged and playtested.

## PR0 — OpenSpec bootstrap

- [x] `proposal.md`, `design.md`, `tasks.md` in change folder
- [x] `testing-checklist-pr0.md` … `testing-checklist-pr5.md` stubs
- [x] `openspec/WORKFLOW.md` active change pointer updated
- [x] User review of OpenSpec documents
- [x] No gameplay code

## PR1 — Debug paths, version, and session log core

- [x] `src/debug/paths.py` — `LOGS_DIR`, `crash_log_path()`, `session_log_path()`
- [x] `src/debug/version_info.py` — `GAME_VERSION` (metadata → `pyproject.toml` → `"dev"`)
- [x] `src/debug/session_log.py` — `SessionLogCoordinator`, `start_session()` / `log()` / `close()` / `flush()`
- [x] `src/debug/__init__.py`
- [x] `src/main.py` — `start_session()` at top; `close()` in `finally` only (**no crash handler, no milestones, no validation**)
- [x] `tests/test_session_log.py` — worker writes file; `log()` no-op before `start_session()`
- [x] Targeted pytest for PR1
- [ ] Deliver manual checklist (`testing-checklist-pr1.md`)

## PR2 — Friendly entities.json validation + lazy spawn

**Depends on PR1.**

- [x] `src/data/entity_validation.py` — `format_entity_load_error`, `format_json_decode_error`, `load_entities_user_facing`
- [x] Golden-file tests for every `EntityLoadError` raise template in `entity_loader.py`
- [x] `src/spawn.py` — full lazy registry (PEP 562 `__getattr__` + `_get_registry()`)
- [x] `src/debug/session_log.py` — `skip_quit_milestone()`, `should_log_quit_milestone()`, `reset_quit_milestone_state()` (tests)
- [x] `src/main.py` — remove top-level `from src.app import App`; validate before deferred import; `skip_quit_milestone(reason="startup_validation")` before `sys.exit(1)`
- [x] `tests/test_entity_validation.py`
- [x] `tests/test_spawn_lazy_registry.py` — `import src.spawn` does not read `entities.json`
- [x] `tests/test_entity_validation_startup.py` — tmp project copy subprocess; stderr format + no spurious `Quit`
- [x] `src/debug/startup_error.py` — dialog, append `{user_data}/logs/startup_error.log`, stderr via `report_startup_json_error`
- [x] Targeted pytest for PR2 (incl. `tests/test_startup_error.py`)
- [ ] Deliver manual checklist (`testing-checklist-pr2.md`) — incl. dialog + startup_error.log

## PR3 — Session milestone hooks

**Depends on PR1, PR2.** No `main.py` changes.

- [x] `GameEngine.run_seed` field; resolved in `_initialize_floor_new`
- [x] `initialize_floor(log_session_milestones: bool = True)` forwarding to `_initialize_floor_*`
- [x] Milestone hooks: `_start_new_game` (before `_enter_play`), `_load_saved_game`, `_return_to_menu`, floor init, `GameOverState.open()`, `_add_instance_to_inventory`, `RunStats.record_monster_defeated(defeated_entity=...)`
- [x] Debug R: `new_game(log_session_milestones=False)` + `Dungeon regenerated` log
- [x] Canonical new-game order: Started → Seed → Entered floor 1
- [x] `tests/test_session_log_milestones.py`
- [x] Targeted pytest for PR3
- [ ] Deliver manual checklist (`testing-checklist-pr3.md`)

## PR4 — Crash reports and modal context

**Depends on PR1, PR2.**

- [x] `src/debug/modal_snapshot.py` — `active_modal_label(app)` (broader than `modal_blocks_quit()`; no `macguffin_discovery` as modal)
- [x] `src/debug/context.py` — `build_crash_context()`
- [x] `src/debug/crash_report.py` — `install_crash_handler`, `register_app`, `register_ui`, sync `{user_data}/logs/crash.log`
- [x] `src/main.py` — excepthook install; `register_app` / `register_ui`; conditional `Quit` via `should_log_quit_milestone()`; `skip_quit_milestone(reason="crash")` on exception path
- [x] `tests/test_crash_report.py`, `tests/test_modal_snapshot.py`
- [x] Targeted pytest for PR4
- [ ] Deliver manual checklist (`testing-checklist-pr4.md`)

## PR5 — Spec sync, log guide, and acceptance

**Depends on PR1–PR4.**

- [x] Finalize `log-interpretation-guide.md` against shipped log format (field names, modal labels, milestone lines)
- [x] New `openspec/specs/debug-support/spec.md` — link to log guide; embed or reference interpretation sections
- [x] `README.md` — "Reporting bugs" pointer to `{user_data}/logs/` and log interpretation guide
- [x] `acceptance-report.md`
- [x] Archive to `openspec/changes/archive/YYYY-MM-DD-add-debug-support/` (include `log-interpretation-guide.md`)
- [x] Full `pytest tests/`
- [ ] Final manual playtest checklist (`testing-checklist-pr5.md`)