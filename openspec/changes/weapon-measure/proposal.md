# Proposal: weapon-measure

## Problem

Gladiavore’s arena loop is playable, but weapons are still mostly damage/accuracy bags. Measure-first combat (gladius in-fighting vs out-fighting, spear wants distance, DCSS-like attack delay) cannot ship until weapons declare **how** they fight at each range.

## Solution

Open OpenSpec change **`weapon-measure`**: data model + resolution for **attack delay** and **per-band effectiveness**, with seed archetypes (sword, spear, heavy, short blade). No new player command keys in this change.

## Scope

### In

- JSON weapon fields for delay + range-band effectiveness
- Shared geometry helper (distance / knight-as-band-2 where rules say so)
- Basic attack resolution uses delay + band
- Seed content for current career match weapons
- Tests + live spec touch

### Out

- Footwork, ctrl+dir intent UI, feint presentation polish (player-combat-commands)
- Ready-actions rebind (5 / `d`)
- AI personality fuzzy logic
- Full shop/armory content explosion

## Dependencies

- **Requires:** foundation match combat / AUT
- **Blocks:** player-combat-commands attack PRs; ai-personality-fuzzy measure fitness

## Program

See `openspec/changes/battle-pace-program/ROADMAP.md` (module **BP-W**).

## Success

Designer can feel spear-at-hug vs sword-at-hug difference when both attack; all knobs in JSON; no wasted scope on AI/keys.
