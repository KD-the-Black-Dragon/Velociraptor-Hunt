# Manual testing checklist — PR10 (AI movement + visit extract)

**Change:** `engineering-maintainability`  
**PR:** 10 — Extract movement + visit orchestration from AI pipeline

## How to run

```text
python -m src.main
```

## Base smoke (required every PR)

- [ ] Game launches (main menu appears; no traceback on start)
- [ ] New Game starts a run (map, log, player visible)
- [ ] Play until game over is reachable (e.g. digestion defeat)
- [ ] No crash during the above

## PR10-specific

Full AI path (chase, explore, abilities, vore) now routes through `movement` + `visit`.

- [ ] Fight evils for several turns (moves, hits, world phase)
- [ ] Monsters still explore when not engaged
- [ ] Optional: engulf / struggle / escape still works
- [ ] Optional: save/load mid-floor
- [ ] No freeze or traceback

## Layout after PR10

```text
src/systems/ai/
  __init__.py     # re-exports
  common.py       # shared helpers
  explore.py      # explore intent
  targeting.py    # target picking
  chase.py        # pursuit / direction resolve
  movement.py     # flee/wander, try_monster_move, door-spite wait  (NEW)
  visit.py        # intent pipeline, run_monster_turns, spawn_test_npc (NEW)
  pipeline.py     # thin re-export shim for older patch paths
```

`from src.systems.ai import run_monster_turns` still works.

## Automated (already run)

- Broad AI suite **147 passed** (`-n 6`)

## Sign-off

Designer: smoke OK → authorize PR11 (AI deeper cleanup).
