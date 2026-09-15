# Manual testing — PR7 clock and ring

How to run: `python -m src.main`

## Happy path

- [ ] Footer shows **Clock** remaining (tenths, e.g. `80.0` counting down as you wait)
- [ ] Footer shows one of: **Hunter definitely winning** / **Close** / **Raptor definitely winning**
- [ ] Standing near the **center** pulls the ring toward you; hugging the **rim** does not
- [ ] A tiny lead stays **Close** (you cannot see a 1-point edge)
- [ ] If the clock hits 0.0 while you are **Hunter definitely winning**: time-over win, any key to menu
- [ ] If the clock hits 0.0 while **Close** or **Raptor definitely winning**: time-over loss (raptor holds the ring)
- [ ] Tranq win still works if you drop the raptor before the clock

## Edges

- [ ] Targeting (F) does not burn the clock until you fire
- [ ] Gait toggle (R/S) does not burn the clock
- [ ] Esc still leaves before time-over

## Pointer

`openspec/changes/velociraptor-hunt/tasks.md` (PR7).
