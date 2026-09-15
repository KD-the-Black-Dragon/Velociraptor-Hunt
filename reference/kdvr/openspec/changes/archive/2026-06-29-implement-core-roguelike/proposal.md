# Proposal: Implement Core Roguelike

## Why

KD's Vore Roguelike has a written behavioral contract in [`openspec/specs/core-roguelike/spec.md`](../specs/core-roguelike/spec.md) but no runnable code. This change delivers the first playable vertical slice: a single-floor dungeon the player can explore, fight in, and recover from being stunned — establishing the foundation that future vore modules attach to without rewriting core systems.

## What Changes

Greenfield implementation of the v1 core game:

- Python project scaffold with libtcod window and game loop
- Procedural room-and-corridor dungeon generation
- Player movement (8-direction, corner-cutting rule) and libtcod FOV
- ASCII rendering with explored-tile memory and HUD (HP, stunned state, message log)
- 3–5 chase-AI monsters with post-player turns
- Bump combat with defeated monsters and stunned (not digested) player at 0 HP
- Health potions on the floor, 26-slot `a`–`z` inventory, letter-key use
- Lightweight ECS architecture with documented vore extension hooks

No vore attacks, digestion, save/load, or multi-floor content.

## Capabilities

### New Capabilities

- `core-roguelike` (implementation): Brings the existing spec from documentation to a runnable game. The main spec already exists; this change implements it rather than altering requirements.

### Modified Capabilities

- None. Requirements are already defined in `openspec/specs/core-roguelike/spec.md`. No delta spec needed unless implementation reveals a spec correction.

## Impact

**New files**

- `pyproject.toml` — dependencies (`libtcod`, `numpy`) and entry point
- `src/` — engine, map generation, components, systems, `main.py`

**Dependencies**

- Python 3.11+
- libtcod 16.x

**Out of scope**

- `openspec/specs/vore/` domain
- Automated test suite (manual acceptance criteria only for v1)
- Asset pipeline beyond built-in tilemap font

## Success Criteria

All nine acceptance criteria in the core spec are manually demonstrable in one play session. Window title or HUD branding reads **KD's Vore Roguelike**. Log messages use *defeated* / *stunned* terminology, never *kill* / *die*.