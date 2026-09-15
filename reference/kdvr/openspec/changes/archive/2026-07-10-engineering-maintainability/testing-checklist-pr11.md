# Manual testing checklist — PR11 (AI deeper cleanup)

**Change:** `engineering-maintainability`  
**PR:** 11 — Public API docs, dead-code/import hygiene, submodule production imports

## How to run

```text
python -m src.main
```

## Base smoke (required every PR)

- [ ] Game launches (main menu appears; no traceback on start)
- [ ] New Game starts a run (map, log, player visible)
- [ ] Play until game over is reachable (e.g. digestion defeat)
- [ ] No crash during the above

## PR11-specific

No intentional AI **decision** changes — cleanup only. Confirm behavior still feels right:

- [ ] Fight evils for several turns (moves, hits, world phase)
- [ ] Monsters explore when not engaged
- [ ] Good ally / come-here if convenient
- [ ] Save/load mid-floor once
- [ ] Optional: bat/erratic still does intentional + random cadence
- [ ] No freeze or traceback

## Layout notes

```text
src/systems/ai/
  __init__.py     # documented public API + test-compat re-exports
  common.py
  explore.py
  targeting.py    # production: rest/ally_introduction import here
  chase.py
  movement.py     # cleaned imports; dead _erratic_pursuit_direction removed
  visit.py
  pipeline.py     # historical shim only
```
