# Manual testing — PR4 raptor body

How to run: `python -m src.main`

## Happy path

- [ ] There is **one** `r` on the paddock (or none visible until you look the right way)
- [ ] The raptor is **not** drawn when it is outside your cone / behind trees
- [ ] When you can see it, the footer shows **Raptor N/NE/E/…** matching its facing
- [ ] That facing line **disappears** when you look away
- [ ] Waiting (`.`) lets the raptor act: it turns or steps; it does not teleport onto you from across the map
- [ ] You cannot walk through the raptor; it cannot walk through you
- [ ] Esc still leaves

## Edges

- [ ] Raptor uses tank facing (you can see it looking the wrong way)
- [ ] It may look at you if it has eyes-on; it should not spin to your tile if it cannot see you
- [ ] PR3 gait/aim still work

## Pointer

`openspec/changes/velociraptor-hunt/tasks.md` (PR4).
