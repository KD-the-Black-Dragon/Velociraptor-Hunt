# Manual testing — PR8 visible dart

How to run: `python -m src.main`

## Happy path

- [ ] **F** on a visible raptor, Enter: a cyan `*` flies tile-by-tile along the line, then the hit/miss/tranq result appears (it must be on screen before the result; not an instant resolve)
- [ ] You cannot walk, turn, yaw, or change gait while the dart is in the air
- [ ] Clock does not tick during the flight
- [ ] After it lands, AUT spends as a fire turn and the raptor may act
- [ ] Blind fire into fog (along facing): the dart still flies the line, then miss / tree / lucky hit
- [ ] A tree on the line: dart stops on the tree, then the slam message

## Edges

- [ ] Tranq still goes to bask after the dart arrives (not before)
- [ ] Wrong-facing fire still refuses immediately (no dart, no ammo)
- [ ] Esc during flight leaves the hunt (dart resolves first so the save is consistent)
- [ ] Aim, fatigue, prints, last-known, 400 clock, adjacent+seen swallow still work

## Pointer

`openspec/changes/hunt-deferred/tasks.md` (PR8).
