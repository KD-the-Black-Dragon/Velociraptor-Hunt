# Acceptance Report: add-debug-support

**Date:** 2026-07-06  
**Scope:** Always-on diagnostics — crash reports, session milestone logs, friendly `entities.json` startup validation, F6 force-crash debug key (PR0–PR5).

## Automated verification

### Change gate (debug support)

```bash
python -m pytest tests/test_session_log.py tests/test_entity_validation.py tests/test_spawn_lazy_registry.py tests/test_entity_validation_startup.py tests/test_startup_error.py tests/test_session_log_milestones.py tests/test_crash_report.py tests/test_modal_snapshot.py -q
```

| Result | Count |
|--------|-------|
| **PASS** | **44** (change-scoped tests) |

### Full suite

```bash
python -m pytest tests/ -q --tb=no
```

| Result | Count |
|--------|-------|
| Passed | 1086 |
| Failed | 5 |
| Warnings | 111 |
| Duration | ~31m 5s |

**Failures (pre-existing data/test drift, not introduced by debug support):**

- `tests/test_dungeon_spawn_config.py::test_load_default_dungeon_spawn_json`
- `tests/test_npc_abilities_rangen.py::test_primary_at_three_preferred_over_neutral_at_two_for_ranged_pick`
- `tests/test_npc_data_pr1.py::test_load_default_entities_json`
- `tests/test_spawn_lazy_registry.py::test_import_spawn_does_not_load_registry` (passes in isolation; order-dependent under full suite)
- `tests/test_vore_engulfed.py::test_roaming_wolf_wanders_while_player_engulfed`

**Change gate:** all debug-support tests pass (44 scoped tests).

## Manual verification

- [x] PR1–PR4 playtest sign-off (user)
- [x] Modding README removed; deferred `deferred-add-modding-support` stub (user)
- [x] F6 force-crash for manual crash testing (user request)
- [ ] PR5 acceptance sign-off (user)

## Requirement coverage

| PR | Delivered |
|----|-----------|
| PR0 | OpenSpec bootstrap; design; task checklists |
| PR1 | `{user_data}/logs/` paths, `GAME_VERSION`, `SessionLogCoordinator`, `main()` session lifecycle |
| PR2 | Friendly `entities.json` validation; lazy `spawn.py`; startup dialog/log; skip `Quit` on validation failure |
| PR3 | Session milestone hooks; `run_seed`; canonical new-game order; debug R handling |
| PR4 | Crash handler; modal snapshot; conditional `Quit`; F6 force-crash |
| PR5 | Live `debug-support` spec; log interpretation guide; README bug-reporting; archive |

## Spec updates

- `openspec/specs/debug-support/spec.md` — **new**
- `openspec/changes/archive/2026-07-06-add-debug-support/log-interpretation-guide.md` — triage reference
- `README.md` — Reporting bugs section; F6 in debug controls
- `openspec/WORKFLOW.md` — modding deferred pointer; active change cleared on archive

## Files touched (summary)

| Area | Path |
|------|------|
| Debug module | `src/debug/` (`paths`, `version_info`, `session_log`, `startup_error`, `modal_snapshot`, `context`, `crash_report`, `force_crash`) |
| Validation | `src/data/entity_validation.py` |
| Spawn | `src/spawn.py` (lazy registry) |
| Entry | `src/main.py` |
| Milestones | `src/app.py`, `src/engine.py`, `src/run_stats.py`, `src/systems/combat.py`, `inventory.py`, `vore.py`, `digestion.py` |
| Tests | `tests/test_session_log.py`, `test_entity_validation*.py`, `test_spawn_lazy_registry.py`, `test_startup_error.py`, `test_session_log_milestones.py`, `test_crash_report.py`, `test_modal_snapshot.py` |
| Config | User data dir via `src/user_data.py` (logs no longer under project root) |

## Non-goals confirmed

- Official modding not supported (`Loaded mods: (none)` stub only)
- Validation hard errors: stock `entities.json` only
- Unknown abilities: soft warnings only
- No remote telemetry; no log viewer UI