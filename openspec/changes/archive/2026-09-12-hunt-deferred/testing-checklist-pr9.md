# Manual testing — PR9 loss spectacle

How to run: `python -m src.main`

Let a raptor swallow you (adjacent **and** it can see you).

## Swallow → belly → digest → GAME OVER

- [ ] Swallow lines appear in an **opaque** centered box (map does not show through the text)
- [ ] Enter: paddock **hidden**; eight dark-red `#` around the **raptor’s tile**
- [ ] You (`@`) are in the middle of that ring
- [ ] Still / move / wait: about half the time the ring **slides** (camera stays put; the raptor walks)
- [ ] Background stays **full black**; only `@` and `#` get darker the longer you wait
- [ ] Digest and GAME OVER stay on the hidden/dark screen — the map does **not** pop back
- [ ] GAME OVER text is **centered** in the box
- [ ] Letters do not dismiss GAME OVER; Enter or Esc returns to the menu
- [ ] F1 still works in belly; Esc closes help without leaving the hunt

## Other endings (centered GAME OVER)

- [ ] Tranq: frozen bask map first, then Enter shows a **centered** results / GAME OVER box
- [ ] Time-over win or loss: **centered** GAME OVER box (not only top-of-map overlay)

## Edges

- [ ] Adjacent but **behind** the raptor still does not swallow
- [ ] Dart, aim, fatigue, prints, last-known, 400 clock still work on a hunt you don’t lose

## Pointer

`openspec/changes/hunt-deferred/tasks.md` (PR9).
