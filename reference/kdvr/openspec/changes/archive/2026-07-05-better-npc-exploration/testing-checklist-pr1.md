# Manual checklist — PR1 (reachable explore goals)

Run: `python -m src.main`

## Reachable goals (all alignments)

- [ ] Evil wolf with no quarry: wanders toward distant parts of the **connected** floor (not through closed doors).
- [ ] Good knight with no quarry: explore goals stay on reachable floor; no pathing intent through closed doors.
- [ ] Neutral rabbit (no evil visible): explores within connected region.

## Closed door

- [ ] Chase wolves to a door; close it while they explore after give-up.
- [ ] Wolves do not keep a wander target clearly on the far side of the door (no endless stare *because of unreachable goal*).

## Open door / connectivity

- [ ] Open door between rooms: NPCs on one side can pick explore goals in the connected room.

## Aquatic (if shark spawns on water floor)

- [ ] Aquatic NPC explore stays in water-connected regions (no shore goals).

## Regression

- [ ] Visible chase / follow / flee / memory pursuit unchanged.
- [ ] Pursuit momentum after LOS loss still works.
- [ ] Good–neutral corridor swap still works.