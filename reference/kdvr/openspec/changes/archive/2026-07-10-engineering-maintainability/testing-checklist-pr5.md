# Manual testing checklist — PR5 (engine turn extract)

**Change:** `engineering-maintainability`  
**PR:** 5 — Move turn pipeline into `src/engine_turn.py` (mechanical; no gameplay intent change)

## How to run

```text
python -m src.main
```

## Base smoke (required every PR)

- [ ] Game launches (main menu appears; no traceback on start)
- [ ] New Game starts a run (map, log, player visible)
- [ ] Play until game over is reachable (e.g. digestion defeat)
- [ ] No crash during the above

## PR5-specific (turn / rest / combat)

This PR touched **player turn consume**, **monster world phase**, **regen**, **digestion/vore modal advance**, **rest**, and **macguffin victory completion**.

- [ ] Move into a monster and fight — damage log, monsters act on their phase
- [ ] Wait a few turns (`.` or numpad 5) — time passes, regen eventually if damaged
- [ ] Rest (`5` on main keyboard if configured) when safe and injured — rest runs and ends cleanly
- [ ] Optional: get engulfed / digestion path if easy — still works toward game over
- [ ] Optional: inventory action that consumes a turn (quaff/wield) still works

## Automated (already run)

- Turn/rest/digestion/acceptance suite → **178 passed** in batch; one flaky index error re-ran **PASS**

## Sign-off

Designer: smoke OK → authorize PR6 (engine input extract).
