# Manual testing — PR4 last-known + sound glyphs; 400 AUT clock

How to run: `python -m src.main`

## Happy path

- [ ] Clock starts near **400.0** (not 80)
- [ ] Spot the raptor: bright `r`. Turn away: a **dimmer `r`** stays on the last tile you saw
- [ ] Look at it again: dim mark is gone; only the live `r`
- [ ] It leaves a tile you can still see: dim `r` on that empty tile **clears**
- [ ] If you never saw it, no leftover `r` on empty tiles
- [ ] Movement / rain / wind clues are a **`?`** on the map (same glyph for real and fake)
- [ ] Bottom line does **not** say “Movement N”, “Rain in the canopy”, or “Wind from the …”

## Edges

- [ ] Last-known is not drawn on top of you (`@`)
- [ ] Win bask still shows the live tranquilized `r`
- [ ] Right panel and Ctrl-sidestep still work
- [ ] Adjacent+seen swallow still works (PR3)

## Pointer

`openspec/changes/hunt-deferred/tasks.md` (PR4).
