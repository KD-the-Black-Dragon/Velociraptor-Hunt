# Manual testing checklist — PR1 (Group P)

**How to run:** `python -m src.main`

## Happy path

- [ ] Start a new game; take several turns on floor 1 — turns feel responsive
- [ ] Let NPCs explore/wander out of sight; approach them later — they still path and chase sensibly
- [ ] Corner chase within a few tiles of the player (wolf loses LOS around a wall) still pursues last-known tile
- [ ] Door interaction / door spite still works if you slam a door on a wolf

## Edge / regression

- [ ] Busy-feeling floor (deeper or many spawns): still snappier than pre-PR1; no freezes
- [ ] Good allies still follow / rescue / explore as before
- [ ] Rest-until-healed (if used) does not hang or feel multi-second per rest tick

## Save/load

- [ ] Save and load mid-floor; AI continues without errors (new ephemeral fields are not saved)

## Performance note (headless, seed 42, post-PR1)

| Scenario | Before PR1 (approx) | After PR1 |
|----------|---------------------|-----------|
| `default` mean / p95 | 55–180 / 102–287 ms | **~71 / ~144 ms** (30 NPCs) |
| `explore_10` mean | ~221 ms | **~14 ms** |
| `explore_25` mean | ~540 ms | **~43 ms** |
| `scale_25` p95 | ~565 ms | **~66 ms** |

No intentional AI intelligence changes in PR1.
