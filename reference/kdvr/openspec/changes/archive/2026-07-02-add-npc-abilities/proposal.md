# Proposal: NPC Abilities

## Why

`entities.json` declares `abilities[]` but no runtime handlers exist. Evil AI is identical for every species regardless of data modifiers.

## What

- Ability parser + `Abilities` / `AbilityState` components
- Alignment-aware shared intent pipeline
- One ability per PR; wolf as manual playtest vehicle
- PR1: `Range2` with `ranged_*` stats and engagement AI

## Out of scope (this change)

- PR2+ abilities (Range3, Summon, Coward, …) until their PRs
- Item `abilities[]` handlers

## Spec target

`openspec/specs/npc-abilities/spec.md` (PR13)