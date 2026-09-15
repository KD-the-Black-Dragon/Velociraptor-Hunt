# Proposal: More entity abilities

## Summary

Expand NPC mechanical identity via a small set of new **ability tokens** plus one new **mobility** value. Shortlist locked after designer review (2026-07-11).

## Approved scope

| Deliverable | Type |
|-------------|------|
| `Hands` | Ability — open closed doors on step (finish stub) |
| `Wander` | Ability — mindless drift; no targeting (spore / living fire) |
| `NoChase` | Ability — evil: chase visible quarry only; no memory/momentum pursuit |
| `PreferVore` | Ability — 100% vore attempt when otherwise legal |
| `RangedVoreN` | Ability — vore at distance 2–9; pull prey on hit only |
| `stationary` | **Mobility** — no voluntary movement |

## Deferred

- **Thorns** — tracked in `openspec/changes/todo/spec.md` for a later pass.

## Motivation

- Placeholder species and existing roster entries need behavior beyond stats + vore text.
- Shared tokens preserve data-driven design and modding.
- `Hands` stub and mobility field already anticipate part of this work.

## Out of scope

- Item `abilities[]` on equipment (warn-only today).
- Thorns and other vetoed brainstorm items (may return in future brainstorms).
- Erratic + ranged combo (unchanged incompatible).

## Success criteria

- Each approved token/mobility has load-time validation, behavioral spec, tests, and at least one species assignment (content PR).
- No regression for entities keeping prior `abilities: []` and existing mobility values.

## References

- Design: `design.md`
- Live: `openspec/specs/npc-abilities/spec.md`, `openspec/specs/dungeon/spec.md`
- Origin: `openspec/changes/todo/spec.md` (item opened 2026-07-11)