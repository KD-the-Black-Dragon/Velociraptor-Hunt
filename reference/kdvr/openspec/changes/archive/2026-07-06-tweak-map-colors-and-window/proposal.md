# Proposal: Map Colors & Window Handling

**Status:** Approved for design review — OpenSpec bootstrap.

## Why

Two small quality-of-life issues affect every launch:

1. **Map palette** — Visible floor, walls, and doors use a gold/yellow/brown palette that reads as dated and noisy. The user wants neutral greys while keeping stairs, water, and explored-memory (blue-tint) dimming unchanged.
2. **Window sizing** — The game opens at the fixed design client size (1360×768), which on some desktops exceeds the usable area once the OS title bar and taskbar are accounted for. There is no persistence of size, position, maximized state, or fullscreen preference. A deferred **PR13** fullscreen toggle from `add-ui-overhaul` was never implemented.

## What

| Area | Deliverable |
|------|-------------|
| Map colors | Visible **floor** → dark grey; visible **walls** and **doors** → mid grey; explored-only (`DARK_*`) colors unchanged |
| Window persistence | Save client size, screen position, maximized flag, and fullscreen preference to `{user_data}/settings.json` on every resize (background worker, not main thread) |
| First launch | When no saved window state exists: windowed default; client size = primary display minus **48 px per edge**, clamped to ≥ 1360×768 |
| Maximized restore | If the user closed while maximized, next launch opens maximized |
| Fullscreen | Options row **Fullscreen: Off \| On**; borderless desktop fullscreen; immediate toggle; session restore on exit (see design.md) |
| Minimum size | Existing 1360×768 client floor unchanged |

## Out of scope (v1)

- Changing stairs, water, or explored-memory tile colors
- Exclusive fullscreen / display-mode switching
- Multi-monitor display picker (always primary display for first-launch sizing)
- Migrating or deleting old project-folder `data/settings.json`
- Revisiting minimum supported resolution (1366×768 complaints deferred)
- Window position validation when monitor layout changes between sessions (best-effort restore)

## Capabilities

### Modified

- `core-roguelike` — visible map tile color requirements (floor/wall/door)
- `ui-layout` — startup window sizing, resize persistence, minimum client floor
- `main-menu` — Options fullscreen row

### Code touchpoints (by PR)

- `src/systems/render.py` — tile color constants (PR1)
- `src/settings_store.py` — `window` settings block (PR2)
- `src/ui/window_state.py` (new) — sizing, restore, session snapshot (PR2)
- `src/settings_coordinator.py` (new) — background settings writer (PR2)
- `src/main.py`, `src/ui/window_limits.py` — startup/resize hooks (PR2)
- `src/options_menu.py`, `src/app.py` — fullscreen toggle wiring (PR2)

## User decisions (final)

| Topic | Choice |
|-------|--------|
| Color scope | Visible floor/wall/door only; stairs & water unchanged; explored blue tint unchanged |
| Grey values | Sensible RGB constants; tweak integers later if needed |
| Persist fields | Client size, position, maximized, fullscreen preference |
| Persist timing | Every resize event; background worker thread |
| Maximized on exit | Restore maximized on next launch |
| First-launch size | Full display minus 48 px/edge; clamp to minimum |
| Fullscreen mode | Borderless desktop fullscreen |
| Exit fullscreen | Restore session pre-toggle state (windowed or maximized) |
| Fullscreen vs maximized | Fullscreen overrides; exiting fullscreen returns to last non-fullscreen mode |
| Options label | `Fullscreen: Off \| On` |
| Change packaging | One change `tweak-map-colors-and-window`; PR1 colors, PR2 window |

## PR order

1. **PR0** — OpenSpec bootstrap (this folder, WORKFLOW pointer, checklist stubs)
2. **PR1** — Grey visible map tile colors
3. **PR2** — Window persistence, first-launch sizing, maximized restore, fullscreen toggle
4. **PR3** — Live spec sync, README note, acceptance

## Success criteria

- Visible floor/walls/doors render grey; stairs/water/explored dimming unchanged
- Second launch restores prior window size, position, and maximized state
- First launch on a large monitor opens slightly inset from display bounds
- Window never shrinks below 1360×768 client area
- Fullscreen toggles immediately; exiting returns to prior windowed/maximized session state
- Targeted pytest per PR; full `pytest tests/` green on PR3