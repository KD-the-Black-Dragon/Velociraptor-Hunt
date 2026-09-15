# Manual testing checklist — PR3 (save hardening)

**Change:** `engineering-maintainability`  
**PR:** 3 — Field inventory, `migrate_run` stub, additive-default tests (no format bump)

## How to run

```text
python -m src.main
```

## Base smoke (required every PR)

- [ ] Game launches (main menu appears; no traceback on start)
- [ ] New Game starts a run (map, log, player visible)
- [ ] Play until game over is reachable (e.g. digestion defeat)
- [ ] No crash during the above

## PR3-specific (save path)

- [ ] After a few turns, save works (autosave and/or Ctrl+S → “Game saved.” if you use manual save)
- [ ] Quit to menu (Ctrl+Q flow or equivalent) and **Load Game** resumes the run
- [ ] After load: still on the same floor feel (player alive, map present, can move)
- [ ] Optional: if you had an older autosave, load it — should not crash
- [ ] Game over still wipes the run / leaves Load unavailable as before (if you reach game over)

## Automated (already run)

- Save suite including `test_save_hardening_pr3.py` → **46 passed** (`-n 6`)

## Sign-off

Designer: smoke OK → authorize PR4 (engine floor extract).
