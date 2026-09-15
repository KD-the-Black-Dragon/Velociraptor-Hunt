# Manual testing — PR2 paddock / tank / FOV / AUT

How to run: `python -m src.main`

## Happy path

- [ ] New Hunt → name → weapon → a **circular** jungle (corners are wall, interior is round)
- [ ] Trees (`T`), long grass (`,`), bushes (`%`), and open (`.`) all appear
- [ ] Numpad **8** / **Y** / Up walks **forward** in the facing you have, not screen-north
- [ ] **4** / **6** turn 90° in place; **7** / **9** turn 45°
- [ ] Shift+**4** / Shift+**6** sidestep without turning
- [ ] **2** / **N** backpedal
- [ ] **H** / numpad **5** / **.** wait; status AUT counts in tenths (`1.0`, `2.0`, …)
- [ ] Vision is a **cone** in front of you; terrain behind you is dim
- [ ] Trees/grass/bushes block what you can see through
- [ ] Walking into a tree does nothing (no AUT bump)
- [ ] Esc still returns to the menu

## Edges

- [ ] Keyboard fallback: Y/N/T/U/G/J and arrows match the numpad tank map
- [ ] Status line shows facing (N/NE/E/…) and AUT
- [ ] Camera follows you on the large paddock
- [ ] Hard border: you cannot leave the circle

## Pointer

`openspec/changes/velociraptor-hunt/tasks.md` (PR2).
