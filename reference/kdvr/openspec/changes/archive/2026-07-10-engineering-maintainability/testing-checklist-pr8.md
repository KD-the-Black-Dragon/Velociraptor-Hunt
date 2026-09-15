# Manual testing checklist — PR8 (AI package + explore extract)

**Change:** `engineering-maintainability`  
**PR:** 8 — Convert `systems/ai.py` → package; extract explore intent

## How to run

```text
python -m src.main
```

## Base smoke (required every PR)

- [ ] Game launches (main menu appears; no traceback on start)
- [ ] New Game starts a run (map, log, player visible)
- [ ] Play until game over is reachable (e.g. digestion defeat)
- [ ] No crash during the above

## PR8-specific (AI / explore)

This PR reorganized NPC AI modules. Watch for freezes, crashes, or monsters that never move.

- [ ] Monsters move / chase when you are in view
- [ ] Distant / off-screen monsters still act over time (floor feels alive)
- [ ] Fight at least one evil NPC through a few turns
- [ ] Optional: close a door on a chasing wolf (door spite / repath) if you can set it up
- [ ] Save/load once if easy

## Layout (for context)

```text
src/systems/ai/
  __init__.py   # re-exports stable import surface
  common.py     # shared helpers / door-spite constants
  explore.py    # explore BFS, goals, frustration, oscillation
  pipeline.py   # chase, targeting, visit, run_monster_turns (rest of AI)
```

`from src.systems.ai import …` still works.

## Automated (already run)

- Explore + AI suites green after package split and patch-path updates

## Sign-off

Designer: smoke OK → authorize PR9 (AI chase + targeting extract).
