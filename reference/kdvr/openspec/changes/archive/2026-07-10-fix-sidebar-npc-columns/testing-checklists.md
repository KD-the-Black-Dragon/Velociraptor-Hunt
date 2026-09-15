# Manual testing — fix-sidebar-npc-columns

Consolidated checklist for the ad-hoc change session. All items signed off by designer.

## Run

`python -m src.main`

## Sidebar columns and overflow

- [x] Many evil NPCs in FOV (>5) — two columns with truncated names
- [x] Good NPCs bottom-anchored; evil below player; no vertical overlap
- [x] Overflow `+# evil` / `+# good` always visible when entries are cut
- [x] Resize window slowly — overflow updates before rows drop
- [x] Dead-band heights (~817–838px, ~888–911px) — column 2 populated, not empty

## Wide / Standard preset

- [x] Options → UI Layout → Wide — sidebar wider on next New Game
- [x] Load Game uses **current** layout preset from settings, not save snapshot
- [x] Standard ↔ Wide toggle on menu/options refreshes live layout

## Maximized window edge case

- [x] Windowed at small size, then maximize
- [x] Options → toggle UI Layout — menus do not jump upward
- [x] Main menu and gameplay fill window; no blank band at bottom
- [x] Un-maximize restores stored windowed size