# Proposal: Better NPC Exploration

**Status:** Accepted — archived 2026-07-05 (Paradigm B).

**Discovered during:** `fix-deferred-bugfixes` PR9 playtest (wolf pack + closed door); PR10 playtest (neutral rabbits clustering / freezing near player).

## Why

After chase give-up, NPCs often **fail to disperse** sensibly:

1. **Explore goals are not reachable** — random terrain-legal tiles ignore doors and connectivity.
2. **Greedy explore steps** fail at junctions and do not follow corridors well.
3. **No explore frustration** — unreachable or blocked goals persist indefinitely.
4. **PR10 shim** (wait-on-recent) causes neutral freezes near the player.

## What

**Paradigm B — far landmark explore** (explore/wander only):

| PR | Deliverable |
|----|-------------|
| PR1 | BFS reachable goals; **weighted random** toward farther tiles; hands traversability stub |
| PR2 | Explore frustration (8–12); **farthest-endpoint goal once** on re-pick |
| PR3 | **BFS one-step** explore movement; **sidestep** when blocked toward goal |
| PR4 | Retire PR10 shim; neutral **player tile** avoidance; shared explore path |

**Unchanged:** greedy stepping for visible chase, follow, flee, memory pursuit, momentum.

## Out of scope

- Full A* / pathfinding for combat chase (separate change if ever needed).
- NPC door opening (`hands` ability behavior — stub only here).
- Performance throttling (`todo` Performance).
- Pursuit momentum changes (PR9 shipped).

## Related specs (update on acceptance)

- `openspec/specs/enhancements-3/spec.md` — explore / wander rules
- `openspec/specs/dungeon/spec.md` — door traversal

## Full design

`design.md` and PR checklist in `tasks.md`.