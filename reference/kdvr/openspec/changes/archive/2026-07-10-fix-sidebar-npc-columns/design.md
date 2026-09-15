# Design notes: Sidebar NPC columns (retrospective)

This change shipped without a upfront design doc. This file records what was built and why, for archive reference.

## Problems addressed

1. **Overflow regression** — `+# evil` / `+# good` lines disappeared before individual NPC rows were dropped at shorter sidebar heights.
2. **Two-column layout** — More than five evil (or two good) NPCs in FOV needed a second column with per-column name truncation.
3. **Wide preset** — Options **Wide** layout had to apply reliably on New Game, Load Game, and live resize while on menu/options.
4. **Column 2 dead bands** — At specific window heights (~817–838px and ~888–911px client height), column 2 stayed empty while horizontal space remained unused.
5. **Maximized window + UI Layout toggle** — Toggling UI Layout while maximized over a small stored windowed size resized the console to the stored size, leaving a blank band at the bottom and shifting menus upward.

## Architecture

### Band planner (`src/ui/sidebar_npc_layout.py`)

- **`BandLayout`** — Planned column count, display/overflow counts, rows used, truncate flag, per-column entry counts, and `interleaved_fill` when row-parallel packing is active.
- **`plan_band`** — Plans one alignment band (evil or good) within a row budget; compares single-column vs two-column fits.
- **`resolve_npc_bands`** — Plans good band first, evil in remaining space, then replans good if evil consumed more than initially assumed. Returns `good_band_top` for draw clipping.
- **Column-first fill** — Default when vertical space allows filling column 0 to cap before column 1 (per spec).
- **Interleaved fill** — When vertical row budget is tight, entries alternate col0/col1 per row slot so both columns populate before shrinking to one column. Fixes dead-band heights where column-first shrink drained col1 entirely.

### Drawing (`src/ui/sidebar.py`)

- Uses `column_geometry`, `entry_slot` (respecting `interleaved_fill`), and clips evil entries above `good_band_top`.
- Overflow summary lines always reserved when entries are cut.

### Layout data (`data/ui_layout.json`)

- **Wide** preset: sidebar **36** cells wide (was 32), map viewport **44** (was 48). HP bar width adjusted for wide sidebar.

### Preset application (`src/app.py`)

- **New Game** — `_layout_for_run` uses `settings.ui_preset`.
- **Load Game** — Resolves layout from `settings.ui_preset`, not save snapshot (save may still record preset for diagnostics).
- **Options UI Layout toggle** — `reload_baseline_from_settings()` + `resize_app_console` using **live** SDL client pixels (`client_pixels_from_context`), not stored windowed size when maximized.

### Window sizing (`src/ui/window_limits.py`)

- **`client_pixels_from_context`** — Read-only clamped client size from SDL; used when console must match actual window without demaximizing or shrinking.

## Resolved decisions

| Topic | Decision |
|-------|----------|
| Fill order when height-limited | Interleaved row pairs before single-column fallback |
| Load Game layout | Always `settings.ui_preset`; ignore save snapshot |
| Maximized + preset toggle | Console sized from live `window.size`, not persisted `client_width`/`client_height` |
| Empty second column | Never reserve two-column mode when `col1_count == 0` |
| Evil/good vertical split | Good planned first; evil in remainder; good replanned if needed |

## Key files

| Area | Path |
|------|------|
| Band planner | `src/ui/sidebar_npc_layout.py` |
| Sidebar draw | `src/ui/sidebar.py` |
| Layout JSON | `data/ui_layout.json` |
| App preset/resize | `src/app.py` |
| Live client pixels | `src/ui/window_limits.py` |
| Spec | `openspec/specs/ui-layout/spec.md` |
| Tests | `tests/test_sidebar_npc_layout.py`, `tests/test_ui_sidebar.py`, `tests/test_ui_preset_apply.py`, `tests/test_window_limits.py` |

## PR slices (as shipped)

| PR | Summary |
|----|---------|
| PR1 | Two-column bands, overflow preservation, Wide baseline refresh, core tests |
| PR2 | Interleaved parallel fill at tight heights (dead-band fix) |
| PR3 | UI preset toggle uses live maximized client size |