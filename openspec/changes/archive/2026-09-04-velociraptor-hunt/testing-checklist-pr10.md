# Manual testing — PR10 stats, help, leftover HUD

How to run: `python -m src.main`

## Happy path

- [ ] Main menu **Stats** shows locked totals (games, tranquilized, digested, time wins/losses) and per-weapon shot lines even at zero
- [ ] Finish a hunt by **tranquilizing** → Stats: games +1, tranquilized +1, that weapon’s shots moved
- [ ] Finish a hunt by **digest** → Times digested +1
- [ ] Finish a hunt by **time-over win** / **time-over loss** → the matching time-over line +1
- [ ] Esc **out of a hunt in progress** does **not** add a game, but shots you already fired still show
- [ ] In the paddock, **F1** or **?** opens help (tank, gait, aim, fire). **Esc** closes help and you are still in the hunt
- [ ] Help also works in the **belly**
- [ ] Bottom line is **Clock** / ring / raptor facing when seen — **no** “8 fwd / Shift+4/6” legend
- [ ] Stats survives quitting the app and opening it again

## Edges

- [ ] Targeting **F** still works; F1 during targeting opens help instead of firing
- [ ] Letter keys still do not dismiss win / time-over / digest (Enter or Esc only)
- [ ] PR9 raptor mind still feels the same; rain, clock, fire unchanged

## Pointer

`openspec/changes/velociraptor-hunt/tasks.md` (PR10).
