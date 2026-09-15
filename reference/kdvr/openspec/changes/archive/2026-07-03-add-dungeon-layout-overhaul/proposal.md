# Proposal: Dungeon Layout Overhaul

## Why

Dungeon floors still read as small rectangular rooms linked by long snake-corridors. Organic and cavern styles rarely dominate the layout. Stairs and floor runes often cluster within a handful of steps. There is no reject-and-retry discipline beyond basic land connectivity, and no door gameplay.

## What

1. **Sanity-checked regeneration** — Reject maps that are too small (absolute land-tile count, 3× stricter spawn-candidate bar), fail stair pairwise spread (BFS ≥ 20), or cannot host three pairwise-spread rune sites; debug-log discards to PowerShell; fallback is one giant room (not a tiny chamber).
2. **Layout archetypes** — Modular whole-floor generators: **boxy** (~40%), **organic** (~40%), **hybrid** (~20%). Debug force-100% modes to validate each style before shipping the split. Organic floors: 4–6 large open areas, narrow choke corridors, optional lakes in 1–2 rooms.
3. **Doors** — Closed (`+`) blocks movement and FOV; open (`-`) is walkable/transparent. Player opens by walking into a closed door (turn consumed, stays on near tile). Player closes with **Ctrl+C** + direction (diagonal OK); message if no open door. ~50% of corridor mouths get doors procedurally. NPCs cannot use doors.
4. **Rune placement fix** — Floor items no longer shrink the rune candidate pool; runes enforce ≥ 20 BFS steps between each other (no relax); full floor regen if placement fails after spawn.

## Out of scope

- Map size change (stay **80×44**)
- Depth-dependent layout scaling
- Locked doors, transparent doors, NPC door interaction
- Stairs up / ascending floors
- Shallow water

## Spec target

Extend `openspec/specs/dungeon/spec.md` (PR3). Resolve `openspec/changes/todo/spec.md` rune-cluster item.

## Design

`openspec/changes/add-dungeon-layout-overhaul/design.md`