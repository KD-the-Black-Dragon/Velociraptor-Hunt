# Manual testing — PR5 mud prints

How to run: `python -m src.main`

## Happy path

- [ ] **Mud** (`.` brown) vs **open grassland** (`'` green): two different open floors
- [ ] Walking on **mud** always leaves a `"` print, even in light rain
- [ ] Walking on **open grassland**, **long grass**, or **bush** leaves **no** print
- [ ] The raptor leaves prints on open ground the same way
- [ ] Prints fade on their own; a print made in **heavy** rain lasts longer than one made in **light** rain (wait through a rain cycle if you can stamp both)

## Edges

- [ ] Last-known dim `r` and sound `?` still work (PR4)
- [ ] Clock still ~400 AUT
- [ ] Ctrl-sidestep and adjacent+seen swallow still work

## Pointer

`openspec/changes/hunt-deferred/tasks.md` (PR5).
