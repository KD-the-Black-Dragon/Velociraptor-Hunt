# Tasks: Dungeon Enhancement

Implementation follows PR plan in [`design.md`](design.md). Check off as completed.

## PR 1: Tiles and mobility

- [x] `DEEP_WATER`, `STAIRS_DOWN` tile types; transparency rules (water passes FOV)
- [x] `Mobility` component (`GROUND`, `FLY`, `AQUATIC`); player `GROUND`
- [x] Mobility-aware `can_enter_tile` / movement / spawn candidate checks
- [x] Render water and stairs glyphs
- [x] Tests + `testing-checklist-pr1.md`

## PR 2: Map generation

- [x] Mixed generation: rects, organic caves, wide/narrow corridors
- [x] Shaped probabilistic water (lakes, ponds, rivers); ~5×5 minimum feature size
- [x] Land connectivity validation; reject/regen with retry cap
- [x] Three `STAIRS_DOWN` per floor, all reachable from entrance
- [x] Tests + `testing-checklist-pr2.md`

## PR 3: Floor depth and descent

- [x] `floor_depth` on engine (starts 1; cap 1000)
- [x] `Shift+.` (`>`) handled on any tile; `.` still wait
- [x] Engulfed anywhere: no-op, no turn, *"Going deeper won't help you here!"*
- [x] Not on downstairs: no-op, no turn, *"There are no stairs here."*
- [x] On downstairs, not engulfed: descend
- [x] Good NPCs in LOS follow; nearest valid placement to entrance; no duplicate knight spawns
- [x] Descent regens map/spawns; preserves player HP, inventory, name, prefs
- [x] HUD shows current depth
- [x] Tests + `testing-checklist-pr3.md`

## PR 4: Aquatic combat, AI, shark

- [x] Aquatic shore bump-attacks; aquatic cannot enter land
- [x] Flyer traversal over land and water; one creature per tile unchanged
- [x] Mobility-aware AI pathing and explore goals
- [x] Shark predator; spawn 2 in water when map has water
- [x] Vore escape: water tiles valid for `AQUATIC`/`FLY` prey only
- [x] Tests + `testing-checklist-pr4.md`

## PR 5: Spec and acceptance

- [x] Update `core-roguelike`, `vore`, `enhancements-3` spec notes
- [x] `testing-checklists.md`, `acceptance-report.md`
- [x] Update `README.md`
- [x] Archive change; full test suite green