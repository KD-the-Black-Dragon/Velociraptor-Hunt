# Acceptance Report: add-ui-overhaul

**Date:** 2026-07-02  
**Scope:** Region-based UI, camera viewport, sidebar, message log, status corner, layout presets, dynamic resize

## Automated verification

```bash
python -m pytest tests/ -q
```

**Last run:** 550 passed, 0 failed (2026-07-02)

| Area | Tests | Result |
|------|-------|--------|
| Layout loader | `test_ui_layout.py`, `test_ui_bootstrap.py` | PASS |
| Regions + camera | `test_ui_regions.py`, `test_ui_camera.py` | PASS |
| Message log | `test_ui_message_log.py` | PASS |
| Sidebar | `test_ui_sidebar.py` | PASS |
| Status corner | `test_ui_status_corner.py` | PASS |
| Presets + apply | `test_ui_preset_apply.py`, `test_options_menu.py` | PASS |
| Dynamic resize + window floor | `test_ui_dynamic_layout.py`, `test_ui_window_limits.py` | PASS |
| Modals | `test_ui_modals.py` | PASS |
| Menu anchoring | `test_main_menu.py` | PASS |
| Flow / regression | `test_flow_pr4.py`, `test_acceptance.py`, full suite | PASS |

## Manual verification

- [x] User playtest sign-off PR2–PR11 (incremental)
- [x] PR11 polish: resize floor, Wide preset, menu block anchoring
- [x] Consolidated checklist: `testing-checklists.md`
- [x] Final manual acceptance sign-off (2026-07-02)

## Requirement coverage (highlights)

| Requirement | Verified by |
|-------------|-------------|
| JSON layout presets | `test_ui_layout.py`, `data/ui_layout.json` |
| 2× tile scale | `test_ui_bootstrap.py`, manual PR2 |
| Region blit pipeline | `test_ui_regions.py`, `test_dungeon_pr3.py` |
| Camera viewport | `test_ui_camera.py` |
| 8-line message log | `test_ui_message_log.py` |
| Sidebar player + NPCs | `test_ui_sidebar.py` |
| Status corner depth/ailments | `test_ui_status_corner.py` |
| Options UI Layout preset | `test_options_menu.py`, `test_ui_preset_apply.py` |
| Dynamic resize + 1360×768 floor | `test_ui_dynamic_layout.py`, `test_ui_window_limits.py` |
| Root-console modals | `test_ui_modals.py` |
| Menu title/options block anchor | `test_main_menu.py` |
| Quit confirm bare Shift | `test_flow_pr4.py` |

## Spec updates

- `openspec/specs/ui-layout/spec.md` — **new** live spec
- `openspec/specs/core-roguelike/spec.md` — playfield UI, sidebar, status corner
- `openspec/specs/main-menu/spec.md` — scale, UI Layout row, menu anchoring
- `README.md` — playfield layout, modding `ui_layout.json`
- `data/SCHEMA.md` — updated during PR1/PR11

## Ad-hoc changes folded in (post-PR11)

- **Standard / Wide rebalance** — Standard 57×34 map / 23 sidebar / 9-char player bar; Wide 48×32 / 18-char bar
- **Preset apply on Options toggle** — baseline reload + `sync_layout_for_console`
- **Window minimum enforcement** — SDL `min_size` + force client size on sub-minimum resize
- **Menu block-anchored centering** — title banner and options share one horizontal anchor per width

## Verdict

**add-ui-overhaul: ACCEPTED**