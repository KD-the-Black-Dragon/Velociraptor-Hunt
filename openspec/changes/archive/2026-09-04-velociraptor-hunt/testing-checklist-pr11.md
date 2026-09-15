# Manual testing — PR11 autosave, abandon, difficulty boards

How to run: `python -m src.main`

## Happy path

- [ ] Start a hunt, walk around, **Esc** to menu: **Continue Hunt** appears; resume is the same paddock and facing
- [ ] **Ctrl+Q** in a hunt autosaves, asks quit (Y/n); Y returns to menu with Continue Hunt still there (not counted as abandoned)
- [ ] Close the window mid-hunt, relaunch: Continue Hunt restores the run
- [ ] Continue Hunt → New Hunt: prompt **A saved hunt exists and will be abandoned**. Capital **Y** starts a new name; Stats: games played +1 and games abandoned +1 on that hunt’s difficulty. **n** or Esc cancels
- [ ] Finish a hunt (tranq / digest / time-over): no Continue Hunt; the matching outcome line increments; abandoned does not
- [ ] Options difficulty **Hard**, play and finish: Stats on Hard shows it; Normal does not
- [ ] Stats: **Left/Right** cycles Easier / Normal / Hard / Nightmare; title shows the board name
- [ ] Games abandoned is listed on Stats

## Edges

- [ ] F1 help, targeting, rain/clock still work after Continue
- [ ] Abandon uses capital Y / lowercase n (same as other confirm dialogs)

## Pointer

`openspec/changes/velociraptor-hunt/tasks.md` (PR11).
