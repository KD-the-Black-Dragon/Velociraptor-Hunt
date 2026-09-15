# Manual testing — PR3 gait and aim stances

How to run: `python -m src.main`

## Happy path

- [ ] Status shows **walk** and **hip** on a fresh hunt
- [ ] **R** goes to run (one press from walk or sneak). **R** again returns to walk
- [ ] **S** goes to sneak (one press from walk or run). **S** again returns to walk
- [ ] Run does **not** spend AUT by itself
- [ ] While running, vision cone is shorter
- [ ] **A** raises aim (status **aim**); **A** again is **deep**; a third **A** does nothing extra
- [ ] Aiming lengthens and narrows the cone
- [ ] **D** stand down dumps all aim in one press
- [ ] **R** while aiming clears aim and starts running
- [ ] Walk or sneak does **not** drop aim
- [ ] While running, backpedal or Shift-sidestep drops you to **walk** and then steps
- [ ] Sneak can still backpedal and sidestep

## Edges

- [ ] **D** with no aim is a no-op
- [ ] Esc still leaves the hunt
- [ ] PR2 tank keys still work

## Pointer

`openspec/changes/velociraptor-hunt/tasks.md` (PR3).
