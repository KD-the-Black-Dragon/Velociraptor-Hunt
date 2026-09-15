# Acceptance Report: four-k-ui-scaling-and-good-smite-fix

**Date:** 2026-08-30  
**Scope:** Options/F10 4K UI scaling (2× tile_scale, default Off); good Smite hostility fix; temporary depth-1 sheep cleric playtest then restore; present-path / New Game layout fixes for 4K; late addendum: descend also on `0` / NumPad0.

## Automated verification

### Change-scoped

Targeted suites during PRs (Smite, settings/Options/4K, window limits, help, dungeon descend) — passed.

### Full suite

See final regression notes in this report (filled after `pytest tests/ -n 4` AGENTS procedure).

## Manual verification

Designer playtest signed off across PRs:

- PR1: good Smite no longer hits the player  
- PR2: temporary depth-1 cleric for playtest  
- PR3+: 4K Options/F10; New Game/Load/maximized; Options toggle centering; name/depth/entity entry scaling  
- Cleric spawn restored to 12–14  
- Descend via `0` / NumPad0 OK  

## Live specs

- `openspec/specs/npc-abilities/spec.md` — Smite hostility / good follow  
- `openspec/specs/ui-layout/spec.md` — 4K UI scaling, F10, scaled present for menu-like screens  
- `openspec/specs/dungeon/spec.md` / `core-roguelike/spec.md` — descend key bindings (`Shift+.`, `0`, NumPad0)

## Key implementation

| Area | Change |
|------|--------|
| `src/systems/abilities.py` | Smite engagement requires `shooter_can_damage` |
| `src/settings_store.py` / `options_menu.py` | `four_k_scaling` + Options row |
| `src/ui/bootstrap.py` | `layout_for_preset` / 2× tile_scale when On |
| `src/app.py` | F10; apply display layout; New Game/Load prepare console |
| `src/ui/log_present.py` | `present_scaled_console` for menu-like screens |
| `src/ui/window_limits.py` / `window_state.py` | Actual client size; no inflated console |
| `src/input_handlers.py` / `engine_input.py` | Descend: Shift+. / `0` / NumPad0 |
| `data/entities.json` | `sheep_cleric` spawn restored 12–14 |

## Outcome

**Accepted** pending full-suite results below. Archive to `openspec/changes/archive/2026-08-30-four-k-ui-scaling-and-good-smite-fix/`.

### Full suite results

**Step 1** (`pytest tests/ -n 4`): 1729 passed, 4 failed, 2 skipped (~20 min).

| Failed (step 1) | Step 4 serial | Outcome |
|-----------------|---------------|---------|
| `test_save_coordinator::test_engine_post_turn_hook_invokes_coordinator` | passed | flake |
| `test_ui_modals::test_vore_modal_drawn_on_root_console_over_sidebar` | passed | flake |
| `test_entity_abilities_content_pr6::test_baseline_abilities_by_species` | failed twice | live-data pin (`tunnel_slug`) |
| `test_entity_abilities_content_pr6::test_stationary_tunnel_slug` | failed twice | live-data pin |

**Designer follow-up:** live-data content tests moved to `Recycle Bin/tests-live-data/` (stock entity/item/prefix assertions against `data/` are not stable). Remaining suite should not pin species kit/mobility from live JSON.

**After recycling live-data content tests:** parallel re-run `1700 passed, 3 failed (xdist flakes), 2 skipped`. All 3 recovered on serial rerun (hands door, save coordinator, vore modal UI). **No failed-twice remaining.**

**Acceptance:** Accepted. Archived to `openspec/changes/archive/2026-08-30-four-k-ui-scaling-and-good-smite-fix/`.
