# Manual testing — PR2 right-side hunt panel

How to run: `python -m src.main`

## Happy path

- [ ] New Hunt → name → weapon → paddock
- [ ] **Right side** of the map shows **Clock** (remaining AUT) and the three-state ring (Hunter definitely winning / Close / Raptor definitely winning)
- [ ] Bottom line does **not** show Clock or the ring string
- [ ] When the raptor is in sight, the panel shows:
  - **Velociraptor**
  - **Distance:** N
  - **Facing:** E (add **!** only if it is looking at you)
  - **State:** Standing, or Walking/Sneaking/Running plus a direction if it just stepped
- [ ] When the raptor is not in sight, that block is absent
- [ ] Press **F**: targeting factors and ammo appear in the **panel**; bottom line is not the factor dump
- [ ] Esc abort targeting; panel returns to clock/ring

## Edges

- [ ] Status line (name, weapon, gait, aim, rain, AUT) still on the second-to-last row
- [ ] F1 help still full-screen (no panel)
- [ ] Win bask / results / time-over still overlay the map; Enter or Esc dismisses
- [ ] Ctrl+4/6 sidestep still works (PR1)
- [ ] Camera still follows the hunter in the narrower map

## Pointer

`openspec/changes/hunt-deferred/tasks.md` (PR2).
