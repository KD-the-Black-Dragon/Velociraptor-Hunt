# Manual testing checklist — PR4 (engine floor extract)

**Change:** `engineering-maintainability`  
**PR:** 4 — Move floor lifecycle into `src/engine_floor.py` (mechanical; no gameplay intent change)

## How to run

```text
python -m src.main
```

## Base smoke (required every PR)

- [ ] Game launches (main menu appears; no traceback on start)
- [ ] New Game starts a run (map, log, player visible)
- [ ] Play until game over is reachable (e.g. digestion defeat)
- [ ] No crash during the above

## PR4-specific (floor paths)

This PR touched **new game**, **floor init**, **spawn**, **prefetch**, and **descend**.

- [ ] New Game: floor has walls, stairs, monsters/items (not empty/broken)
- [ ] Move around; FOV works
- [ ] Find stairs and **descend** (`>` / Shift+`.`) to a new floor — player arrives, floor continues to work
- [ ] Optional: press `R` to regenerate dungeon (debug) if you use it — should not crash
- [ ] Optional: save/load still works after a short run

## Automated (already run)

- Floor/dungeon/spawn/save snapshot suite → **104 passed** (`-n 6`)

## Sign-off

Designer: smoke OK → authorize PR5 (engine turn extract).
