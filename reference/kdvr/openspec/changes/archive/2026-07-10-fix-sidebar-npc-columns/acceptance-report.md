# Acceptance Report: fix-sidebar-npc-columns

**Date:** 2026-07-10  
**Scope:** Sidebar NPC two-column layout, overflow fix, Wide preset reliability, dead-band column fill, Load Game layout from settings, maximized-window UI Layout toggle (PR1–PR3). Ad-hoc session; retrospective `design.md` added at archive.

## Automated verification

### Change-scoped gate

```bash
python -m pytest tests/test_sidebar_npc_layout.py tests/test_ui_sidebar.py tests/test_ui_preset_apply.py tests/test_ui_layout.py tests/test_window_limits.py -n 6 -q
```

| Result | Count |
|--------|-------|
| **PASS** | **52** |

## Manual verification

- [x] PR1 — Two-column sidebar, overflow lines, Wide preset on New Game (user)
- [x] PR2 — Column 2 dead bands at ~817–838px and ~888–911px heights (user)
- [x] Load Game uses current layout preset, not save snapshot (user)
- [x] PR3 — UI Layout toggle while maximized over small windowed size (user)
- [x] Final stability sign-off (user)

## Requirement coverage

| Deliverable | Status |
|-------------|--------|
| Two-column evil/good bands with per-column caps | Shipped |
| Overflow summary always reserved when entries cut | Shipped |
| Name truncation only in two-column mode | Shipped |
| Parallel row-pair fill when vertically tight | Shipped |
| Wide preset applies on New Game / Load Game / options resize | Shipped |
| Load Game resolves layout from `settings.ui_preset` | Shipped |
| UI Layout toggle uses live client size when maximized | Shipped |

## Spec updates

- `openspec/specs/ui-layout/spec.md` — Sidebar NPC column rules (parallel row pairs); Load Game layout from settings; preset application behavior

## Out of scope (confirmed)

- Neutral NPC sidebar entries
- Numeric NPC HP in sidebar
- Player HP bar layout changes