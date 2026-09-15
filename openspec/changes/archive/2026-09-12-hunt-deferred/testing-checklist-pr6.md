# Manual testing — PR6 run fatigue

How to run: `python -m src.main`

## Happy path

- [ ] Press **R** (do not move): vision cone is the same as walking
- [ ] Run forward several steps: cone **shrinks** more with each step (up to a cap)
- [ ] Targeting (**F**) shows **out of breath** after run steps, not merely for being in run mode
- [ ] Wait / walk / sneak for a few turns: cone and shots recover
- [ ] Run still **clears aim**; Ctrl-sidestep / back while running still drop to walk

## Edges

- [ ] Toggle R then immediately F: no “out of breath” until you have actually run
- [ ] Mud prints, last-known, 400 clock, adjacent+seen swallow still work

## Pointer

`openspec/changes/hunt-deferred/tasks.md` (PR6).
