# Manual testing checklist — PR9 (AI chase + targeting extract)

**Change:** `engineering-maintainability`  
**PR:** 9 — Extract targeting and chase modules from AI pipeline

## How to run

```text
python -m src.main
```

## Base smoke (required every PR)

- [ ] Game launches (main menu appears; no traceback on start)
- [ ] New Game starts a run (map, log, player visible)
- [ ] Play until game over is reachable (e.g. digestion defeat)
- [ ] No crash during the above

## PR9-specific (chase / combat AI)

- [ ] Evil NPCs chase and fight you when in view
- [ ] Monsters pursue around corners briefly (memory chase)
- [ ] Optional: good ally (dog knight) attacks evils / follows if present
- [ ] Come-here (`C` or bound key) still works if you have allies
- [ ] Fight several turns without freeze

## Layout after PR9

```text
src/systems/ai/
  __init__.py    # re-exports
  common.py      # shared helpers
  explore.py     # explore intent
  targeting.py   # pick targets / visible hostiles  (NEW)
  chase.py       # pursuit, momentum, direction     (NEW)
  pipeline.py    # visit orchestration, erratic, run_monster_turns
```

`from src.systems.ai import …` still works.

## Automated (already run)

- Chase / come-here / explore / abilities / vore-engulfed suites green

## Sign-off

Designer: smoke OK → authorize PR10 (movement + visit + orchestration extract).
