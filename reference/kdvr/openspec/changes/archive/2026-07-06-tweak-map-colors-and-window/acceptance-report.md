# Acceptance Report: tweak-map-colors-and-window

**Date:** 2026-07-06  
**Scope:** Grey visible map tile palette; window persistence, first-launch sizing, fullscreen toggle (PR0–PR3).

## Automated verification

### Change gate

```bash
python -m pytest tests/test_map_tile_colors.py tests/test_window_state.py tests/test_settings_coordinator.py tests/test_settings_store_window.py tests/test_options_fullscreen.py tests/test_window_move_persist.py tests/test_ui_bootstrap.py -q
```

| Result | Count |
|--------|-------|
| **PASS** | **29** (change-scoped tests) |

### Full suite

```bash
python -m pytest tests/ -q --tb=no
```

| Result | Count |
|--------|-------|
| Passed | 1110 |
| Failed | 5 |
| Warnings | 111 |
| Duration | ~32m 27s |

**Failures (pre-existing, not introduced by this change):**

- `tests/test_dungeon_spawn_config.py::test_load_default_dungeon_spawn_json`
- `tests/test_npc_data_pr1.py::test_load_default_entities_json`
- `tests/test_npc_data_pr4.py::test_descend_with_follower_keeps_good_ally_on_new_floor`
- `tests/test_spawn_lazy_registry.py::test_import_spawn_does_not_load_registry`
- `tests/test_vore_engulfed.py::test_roaming_wolf_wanders_while_player_engulfed`

## Manual verification

- [x] PR1 map grey palette playtest sign-off (user)
- [x] PR2 window persistence, fullscreen, move-without-resize fix (user)
- [x] PR3 final acceptance sign-off (user)

## Requirement coverage

| PR | Delivered |
|----|-----------|
| PR0 | OpenSpec bootstrap (`proposal.md`, `design.md`, `tasks.md`, checklists) |
| PR1 | `LIGHT_FLOOR` / `LIGHT_WALL` / `LIGHT_DOOR` grey palette; `tests/test_map_tile_colors.py` |
| PR2 | `window` settings block; `WindowController`; `settings-coordinator` async persist; first-launch inset sizing; Options fullscreen row; `WindowMoved` + quit sync for position |
| PR3 | Live spec sync (`core-roguelike`, `ui-layout`, `main-menu`); README; archive |

## Spec updates

- `openspec/specs/core-roguelike/spec.md` — **Map Tile Colors** requirement
- `openspec/specs/ui-layout/spec.md` — **Window Persistence**, **Fullscreen Toggle**; dynamic resize move events
- `openspec/specs/main-menu/spec.md` — Options fullscreen row
- `README.md` — `settings.json` window block note

## Files touched (summary)

| Area | Path |
|------|------|
| Map colors | `src/systems/render.py` |
| Window state | `src/ui/window_state.py`, `src/ui/window_controller.py` |
| Settings | `src/settings_store.py`, `src/settings_coordinator.py` |
| Entry / options | `src/main.py`, `src/options_menu.py`, `src/app.py` |
| Tests | `tests/test_map_tile_colors.py`, `test_window_state.py`, `test_settings_coordinator.py`, `test_settings_store_window.py`, `test_options_fullscreen.py`, `test_window_move_persist.py`; `test_ui_bootstrap.py` updated |

## Non-goals confirmed

- Stairs/water/explored blue dimming unchanged
- No settings migration from old project-folder copies
- Minimum client floor 1360×768 unchanged