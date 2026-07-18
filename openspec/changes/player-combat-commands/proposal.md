# Proposal: player-combat-commands

## Problem

The match is still fought like a classic roguelike: close to adjacent, bump, trade hits. Gladiavore needs **optimistic intent** controls, **footwork**, and **easy measure attacks** so the sport is Chivalry-like spacing in a tactical RPG shell.

## Solution

Open **`player-combat-commands`**: intent resolver (no wasted turns), footwork targeting (`f`), directed basic attacks (e.g. ctrl+dir), feint ladder at threat range. Uses **weapon-measure** for what each attack means at each band.

## Scope

### In

- Intent core: no-op invalid; Esc cancel targeting; cone/homing target pick
- Footwork: 2-straight or knight; AP + aggression; compound spam
- Directed basic attack; AUT = weapon attack delay
- Feint / false lunge at R3–4; R5+ no-op
- Help text / messages

### Out

- Momentum → emergency evade (→ `footwork-momentum`)
- AI (→ `ai-personality-fuzzy`)
- Ready-actions key semantics (→ `ready-actions`, integrate when both ship)
- Jump vault; full openings matrix; grapple fairness

## Dependencies

- **Hard for attack PRs:** `weapon-measure`
- **Recommended:** `ready-actions` before module acceptance
- **Blocks:** `footwork-momentum`, `ai-personality-fuzzy`

## Program

See `openspec/changes/battle-pace-program/ROADMAP.md` (module **BP-P**).
