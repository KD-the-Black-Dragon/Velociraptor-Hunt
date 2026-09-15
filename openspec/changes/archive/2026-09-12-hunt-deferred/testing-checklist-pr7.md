# Manual testing — PR7 aim off-center

How to run: `python -m src.main`

Start a New Hunt. Treat this as a fresh pass (the rotate-while-aimed rule changed).

## Aim pick

- [ ] Press **A**: a yellow **X** reticle appears on a tile you can already see (along facing, or on the raptor if you see it)
- [ ] You **cannot** walk the reticle onto tiles outside the current cone, or onto yourself
- [ ] Esc / **D** during pick: no aim, cone unchanged
- [ ] Enter or **A** on a visible tile: Aim level 1, cone recenters on that point, longer/narrower
- [ ] Adjacent tiles go **dark** at aim 1 (you still see yourself)
- [ ] **A** again: Aim level 2, even longer/narrower; two rings around you are dark

## Yaw vs conventional turn

- [ ] While aimed, **Ctrl+7** / **Ctrl+9**: the cone nudges about **one-third** (most of what you saw is still there; a new strip appears on the turn side)
- [ ] Aim level stays 1 or 2 while Ctrl-yawing
- [ ] Panel **Facing** updates to the nearest N/NE/E/… as you yaw (aim west, yaw all the way to east: Facing walks around the compass)
- [ ] Unshifted **9** (45 right) while aimed: aim **cancels immediately**, cone and Facing snap to the **next 45° to the right** of the aim heading
- [ ] Unshifted **7** (45 left): same, next 45° to the left, aim gone
- [ ] Unshifted **6** / **4** (90): aim gone, two ticks that way from the aim heading
- [ ] After that snap, further unshifted turns are normal 45/90 (cone and facing stay together)
- [ ] **D** while still aimed: nearest 45°, not “next in a rotate direction”

## Fire

- [ ] **F** while facing north: you can blind-fire further north (fog/grass)
- [ ] **F** then point the reticle south (or otherwise off-facing): **Enter** does **not** fire; message **You must fire in the same direction you're facing.**; still in targeting; ammo unchanged
- [ ] Default fire line while aimed follows the aim heading if that heading is still generally the current facing

## Gait vs aim

- [ ] **R** or **Q** without moving: aim **stays**
- [ ] One run or quick **step**: aim drops and facing snaps to nearest 45°
- [ ] Walk / sneak steps keep aim (cone still follows the aim heading; body still steps on the 8-tick facing)

## Other

- [ ] You cannot use **A** as a fast-turn onto a `?` you cannot see

## Edges / regressions

- [ ] F1 help lists **A** pick, **Ctrl+7/9**, unshifted turn drops aim, and **D** snap
- [ ] Save / Continue Hunt keeps an off-center aim heading
- [ ] Fatigue, mud prints, last-known, 400 clock, adjacent+seen swallow still work

## Pointer

`openspec/changes/hunt-deferred/tasks.md` (PR7).
