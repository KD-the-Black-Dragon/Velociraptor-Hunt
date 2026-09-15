# Proposal: Dungeon Enhancement

## Why

The dungeon is a single floor of rectangular rooms and 1-tile corridors. There is no depth progression, no terrain variety, and no mobility beyond universal ground walking. Future spawn tables and loot scaling need a **floor depth** and richer maps (organic caves, lakes, rivers, stairs).

This module delivers chaotic mixed map generation, deep water, creature mobility (ground / fly / aquatic), guaranteed land connectivity, multi-floor descent, and a placeholder shark — without difficulty or loot scaling.

## What Changes

- **Tile model** — `FLOOR`, `WALL`, `DEEP_WATER`, `STAIRS_DOWN`; water is transparent but impassable to ground
- **Mobility** — `GROUND`, `FLY`, `AQUATIC` component; player is always `GROUND` (v1)
- **Map generation** — mixed boxes, organic caves, wide/narrow corridors; shaped lakes/ponds/rivers (probabilistic, ~5×5 minimum when water appears); reject/regen until all land is one component reachable from entrance
- **Stairs** — three `>` downstairs per floor, randomly placed, all reachable from entrance; stand on `>`, press **`Shift+.` (`>`)** to descend (DCSS-style); `.` remains wait
- **Floor depth** — `floor_depth` starting at 1 on New Game; increments on descent; cap 1000; shown on HUD
- **`>` key** — engulfed anywhere: no-op, log *"Going deeper won't help you here!"*; not on stairs: no-op, log *"There are no stairs here."*; on stairs: descend
- **Good ally follow** — Good NPCs in LOS follow downstairs; placed nearest valid tiles to entrance
- **Shark** — aquatic evil predator placeholder; spawn **2** in water when the floor has any deep water
- **Combat / vore** — aquatic shore bump-attacks only; flyers cross land and water; vore adjacent regardless of tile; escape respects mobility for water tiles
- **Out of scope** — difficulty scaling, loot scaling, stairs up, shallow water, player flight/swim

## Capabilities

### New

- `dungeon` — see `openspec/specs/dungeon/spec.md`

### Modified

- `core-roguelike` — multi-floor descent, tile types, mobility-aware movement
- `vore` — escape tile validity uses prey mobility (aquatic/fly may land on water)
- `enhancements-3` — spawn hooks for aquatic predators (shark)

## Success Criteria

- Normative spec scenarios covered by tests and manual checklist
- Full `pytest tests/` green
- No impassable isolated land; three reachable downstairs per floor
- Descent preserves player run state (HP, inventory, name, prefs); only map/NPCs/items refresh