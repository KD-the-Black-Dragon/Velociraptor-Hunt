# Tasks: add-ui-overhaul

One PR at a time. Check off when merged and playtested.

## PR0 — OpenSpec bootstrap

- [x] `proposal.md`, `design.md`, `tasks.md` in change folder
- [x] `testing-checklist-pr0.md` … `testing-checklist-pr11.md` stubs
- [x] `openspec/WORKFLOW.md` active change pointer updated
- [x] User sign-off on open layout decisions
- [x] No gameplay code (PR0 complete after user approves plan)

## PR1 — Layout config loader

- [x] `data/ui_layout.json` with `standard` (+ stub `wide_sidebar`) presets
- [x] `src/ui/layout.py` — `UILayout`, `load_ui_layout()`, camera clamp
- [x] `tests/test_ui_layout.py` — validation, tiling, camera edge cases
- [x] `data/SCHEMA.md` entry for ui_layout
- [x] Targeted pytest for PR1

## PR2 — Tile scale + root console sizing

- [x] `main.py` passes `tile_scale` from layout to `tcod.context.new`
- [x] Root `Console` dimensions from active preset
- [x] `SettingsStore.ui_preset` read (default only; no UI toggle yet)
- [x] Targeted pytest for PR2
- [x] Manual playtest checklist PR2

## PR3 — Region sub-console infrastructure

- [x] `src/ui/regions.py` — region rects, sub-console blit helpers
- [x] `Engine.render()` draws into regions (map still full dungeon, camera 0,0)
- [x] `tests/ui_test_helpers.py` for layout-aware consoles
- [x] Targeted pytest for PR3
- [ ] Manual playtest checklist PR3

## PR4 — Camera viewport

- [x] `UILayout.camera_origin()` wired into map rendering
- [x] Camera on entities, flash, engulfed overlay, examine cursor, evoke target
- [x] `tests/test_ui_camera.py`
- [x] Targeted pytest for PR4
- [ ] Manual playtest checklist PR4

## PR5 — Message log panel (8 lines)

- [x] `render_message_log()` in dedicated region; 8 visible lines from config
- [x] Remove message loop from legacy `render_hud()` path
- [x] Migrate HUD-row tests to message_log region
- [x] Targeted pytest for PR5
- [ ] Manual playtest checklist PR5

## PR6 — Sidebar player block

- [x] `render_sidebar_player()` — name, HP, bar only (no ailment flags)
- [x] Sidebar region background + player block only
- [x] Targeted pytest for PR6
- [ ] Manual playtest checklist PR6

## PR7 — Sidebar NPC list

- [x] `render_sidebar_npcs()` — FOV filter, evil/neutral/good bands, caps, overflow
- [x] `tests/test_ui_sidebar.py`
- [x] Targeted pytest for PR7
- [ ] Manual playtest checklist PR7

## PR8 — Status corner panel

- [x] `render_status_corner()` — depth, stunned, engulfed; extensible effect rows
- [x] Delete bottom status line (name/HP/depth) from `render_hud()` or remove `render_hud()` entirely
- [x] Targeted pytest for PR8
- [ ] Manual playtest checklist PR8

## PR9 — Layout presets in Options

- [x] Options menu row to cycle `ui_preset`
- [x] Persist in `{user_data}/settings.json`; apply on new `Engine` / new game
- [x] Targeted pytest for PR9
- [ ] Manual playtest checklist PR9

## PR10 — Menu / modal layout pass

- [x] Main menu, name entry, options, quit confirm at new scale
- [x] Modals centered on map viewport sub-console *(superseded by PR11 item 3)*
- [x] Targeted pytest for PR10
- [ ] Manual playtest checklist PR10

## PR11 — UI visualization polish (ad-hoc)

### 1 — Dynamic window resize (grow + shrink)

- [x] `WINDOWRESIZED` handler in `main.py`
- [x] `src/ui/dynamic_layout.py` — resolve root cells from pixels; map viewport flex; chrome floors from preset
- [x] Propagate live `UILayout` to `App` / `Engine` / `RegionBundle` on resize
- [x] `tests/test_ui_dynamic_layout.py`

### 2 — Sidebar two-line NPC entries + spacing

- [x] Name row + bar-only row below per NPC; blank row between entities
- [x] Player: 1-row top pad, name, HP line, 1-row gap before evil band
- [x] Good band: 2-row bottom pad above panel edge
- [x] JSON: `player_top_pad`, `player_bottom_pad`, `good_bottom_pad`, `rows_per_npc`
- [x] Update `tests/test_ui_sidebar.py`

### 3 — Modals centered on root console

- [x] Revert gameplay modals to root-console centering
- [x] Quit confirm centered on root console
- [x] Keep map-sub-console cursors for examine / evoke target
- [x] Update `tests/test_ui_modals.py`

### 4 — Standard player HP bar clip fix

- [x] Shorten `standard` preset `hp_bar_width` to 18
- [x] Separate `npc_hp_bar_width` from player bar in JSON + loader

### 5 — Sidebar padding (see item 2)

- [x] Covered by padding fields + render band math

### 6 — Status corner +2 cells wide

- [x] `status_corner.w` 10; `message_log.w` 70; both presets
- [x] Layout tests updated

### 7 — NPC coarse ~6-wide condition estimate

- [x] `npc_condition_bar()` — all fill counts 0–6 reachable
- [x] Player keeps exact HP + full bar
- [x] Unit tests for fill counts

### 8 — Quit confirm: bare Shift no error

- [x] Ignore modifier-only keys in `handle_quit_confirm_event`
- [x] `tests/test_flow_pr4.py` coverage

### PR11 wrap-up

- [x] `data/SCHEMA.md` sidebar + dynamic layout notes (prior PR11 design pass)
- [x] Targeted pytest for PR11
- [x] Manual playtest checklist PR11

## PR12 — Spec sync and acceptance

- [x] `openspec/specs/ui-layout/spec.md`; update `core-roguelike`, `main-menu`
- [x] `README.md`, `acceptance-report.md`
- [x] Archive to `openspec/changes/archive/YYYY-MM-DD-add-ui-overhaul/`
- [x] Full `pytest tests/`
- [x] Final manual playtest checklist

## PR13 — Fullscreen toggle (stretch)

- [ ] Fullscreen toggle in Options (off by default); persist in `{user_data}/settings.json`
- [ ] Targeted pytest + manual checklist PR13
- [ ] *(Dynamic resize is PR11, not PR13)*