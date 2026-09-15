# Manual testing — PR11 rain beds

How to run: `python -m src.main`

The three files in `Sounds/` (Light / Medium / Heavy, 10 minutes each) should all
be loaded. One is at full volume; the other two are silent.

## Happy path

- [ ] New Hunt or Training: the paddock appears **immediately** (no Not Responding hitch). Rain should start with the paddock, not after a freeze.
- [ ] Rain **fades in** over a couple of seconds on New Hunt / Training (not an instant 100% blast)
- [ ] After enough AUT for weather to change, the new bed **crossfades in** over a couple of seconds; the old bed fades out (no hard cut)
- [ ] Light / medium / heavy each have a distinct bed
- [ ] The loop should not click or “restart” obviously; the join is a self-crossfade
- [ ] Esc to menu: rain cuts immediately; menu appears with **no pause**
- [ ] Continue Hunt: rain fades in again at the current weather

## Edges

- [ ] Training Mode also gets rain
- [ ] Missing a file must not crash (rename one to test, then put it back)
- [ ] Dart / F2 / belly still work with rain playing

## Pointer

`openspec/changes/hunt-deferred/tasks.md` (PR11).
