# Manual testing checklist — PR1 (spawn-at-depth test helpers)

**Change:** `engineering-maintainability`  
**PR:** 1 — Test helpers only (no intentional production gameplay change)

## How to run

```text
python -m src.main
```

## Base smoke (required every PR)

- [ ] Game launches (main menu appears; no traceback on start)
- [ ] New Game starts a run (map, log, player visible)
- [ ] Play until game over is reachable (e.g. allow digestion defeat)
- [ ] No crash during the above

## PR1-specific

PR1 only adds/extends **test helpers** under `tests/spawn_test_helpers.py` and unit tests. Production spawn paths are unchanged.

- [ ] New game still populates monsters/items as before (sanity: not an empty floor)
- [ ] Optional: Continue/Load if you have an autosave — should still work

## Automated (already run)

- `python -m pytest tests/test_spawn_depth_helpers.py tests/test_spawn_density_pr2.py tests/test_depth_scaling_pr1.py tests/test_dungeon_spawn_config.py -n 6` → **40 passed**

## Sign-off

Designer: smoke OK → authorize PR2 (message catalog).
