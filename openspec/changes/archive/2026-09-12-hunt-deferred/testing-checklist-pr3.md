# Manual testing — PR3 adjacency + raptor FOV

How to run: `python -m src.main`

## Happy path

- [ ] If the raptor steps next to you **and is looking at you**, swallow starts on that action (no extra bite)
- [ ] If you walk onto a tile next to it **in front of its eyes**, swallow starts on your step
- [ ] If you are next to it **behind it** (it is not looking at you), you can still act (aim, shoot, step away)
- [ ] If it **turns** to face you while you are already adjacent, swallow starts on that turn
- [ ] Swallow still uses front / side / behind lines from the actual angle
- [ ] Enter → belly → digest still works

## Edges

- [ ] Diagonal adjacent (Chebyshev 1) counts the same as cardinal
- [ ] Range 2 shotgun/revolver snapshot is still possible; range 1 in its FOV is already lost
- [ ] Ctrl+4/6 and the right panel still work
- [ ] Tranq win path unchanged

## Pointer

`openspec/changes/hunt-deferred/tasks.md` (PR3).
