# Manual testing — PR1 Ctrl sidestep

How to run: `python -m src.main`

## Happy path

- [ ] New Hunt → name → weapon → paddock
- [ ] **Ctrl+numpad 4** sidesteps left; **Ctrl+numpad 6** sidesteps right (facing stays put)
- [ ] Same with **NumLock on** and **NumLock off**
- [ ] Unshifted numpad **4** / **6** rotate 90° (NumLock on or off)
- [ ] **Shift+numpad 4/6** rotate (Shift is not sidestep)
- [ ] **Ctrl+G** / **Ctrl+J** / **Ctrl+Left** / **Ctrl+Right** sidestep

## Edges

- [ ] Main-keyboard **4** / **6** with Ctrl do **not** sidestep
- [ ] Run + Ctrl-sidestep still drops to walk
- [ ] F1 lists Ctrl+4 / Ctrl+6 sidestep (not Shift+4)
- [ ] Forward 8 / back 2 / 45° 7 and 9 still work
- [ ] Esc still leaves the hunt
- [ ] Ctrl+Q still opens quit confirm (not a tank command)

## Pointer

`openspec/changes/hunt-deferred/tasks.md` (PR1).
