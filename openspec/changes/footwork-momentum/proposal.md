# Proposal: footwork-momentum

## Problem

Footwork (Chivalry-style lurch) and emergency evade (reaction modal dodge) must couple: after lunging west, dodging east should be very hard; same-direction evade should work.

## Solution

Open **`footwork-momentum`**: short-lived directional momentum from footwork that modifies reaction-modal evade success.

## Scope

### In

- Momentum vector/tags on footwork resolve
- Evade modifiers by direction relationship
- JSON duration and magnitudes
- Tests

### Out

- Redesign of all reaction options
- New footwork shapes
- AI-only momentum (AI reads same rules when BP-A ships)

## Dependencies

- **Hard:** `player-combat-commands` footwork (P2+)
- **Hard:** foundation reaction modal dodge
- **Preferred before:** deep AI playtest of evade-aware foes

## Program

See `openspec/changes/battle-pace-program/ROADMAP.md` (module **BP-M**).
