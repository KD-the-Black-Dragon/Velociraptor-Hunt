# Acceptance Report: add-past-runs

**Date:** 2026-07-05  
**Scope:** Run statistics, game over recap stats, past-runs persistence, Past Runs menu screen (PR1–PR5). Playtest format tweak: two-line list layout (no column headers).

## Automated verification

### Change gate (past-runs)

```bash
python -m pytest tests/test_run_stats.py tests/test_game_over_ending.py tests/test_past_runs_store.py tests/test_past_runs_menu_pr4.py tests/test_save_game_over_pr5.py tests/test_main_menu.py tests/test_flow_pr4.py tests/test_save_menu_pr4.py -q
```

| Result | Count |
|--------|-------|
| **PASS** | **76** |

### Full suite

```bash
python -m pytest -q
```

| Result | Count |
|--------|-------|
| Passed | 932 |
| Failed | 4 |
| Warnings | 103 |
| Duration | ~29 min |

**Failures (pre-existing, not introduced by this change):**

- `test_dungeon_pr3.py::test_followers_reduce_fresh_knight_spawns`
- `test_dungeon_spawn_config.py::test_load_default_dungeon_spawn_json`
- `test_npc_data_pr1.py::test_load_default_entities_json`
- `test_vore_engulfed.py::test_roaming_wolf_wanders_while_player_engulfed`

No failures in the past-runs gate.

## Manual verification

- [x] PR1–PR4 playtest sign-off (user)
- [x] Past Runs two-line format sign-off (user)
- [x] PR5 acceptance sign-off (2026-07-05)

## Requirement coverage

| PR | Delivered |
|----|-----------|
| PR1 | `RunStats`; player-credited defeats + rune counter; save snapshot |
| PR2 | `GameOverEnding`; `PastRunsStore`; append on game over; cap 65535 |
| PR3 | Game over modal: monsters, runes, depth |
| PR4 | Past Runs menu gating; scrollable screen |
| PR5 | Live specs; acceptance; archive |

## Spec updates

- `openspec/specs/past-runs/spec.md` — **new**
- `openspec/specs/main-menu/spec.md` — Past Runs, recap stats, gating
- `openspec/specs/save-load/spec.md` — `run_stats` in snapshot; coordinator wipe before delete

## Deferred / follow-up

- Macguffin / boss victory endings (future module; same game over hook)
- Stabilize full-suite flakes listed above (separate hygiene pass)

## Archive

`openspec/changes/archive/2026-07-05-add-past-runs/`