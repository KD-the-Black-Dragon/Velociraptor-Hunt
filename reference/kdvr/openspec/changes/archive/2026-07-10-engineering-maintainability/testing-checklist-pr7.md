# Manual testing checklist — PR7 (engine deeper cleanup)

**Change:** `engineering-maintainability`  
**PR:** 7 — Engine facade cleanup (names, public API docs, `EngineEventResult` home)

## How to run

```text
python -m src.main
```

## Base smoke (required every PR)

- [ ] Game launches (main menu appears; no traceback on start)
- [ ] New Game starts a run (map, log, player visible)
- [ ] Play until game over is reachable (e.g. digestion defeat)
- [ ] No crash during the above

## PR7-specific (full engine path)

This PR is **cleanup only** but touches the whole engine facade. Exercise a short full loop:

- [ ] Move, fight, wait
- [ ] Inventory / examine / rest if easy
- [ ] Descend one floor if stairs found
- [ ] Save/load or quit-to-menu + load if easy
- [ ] Reach game over (digestion or other)

## What changed (for your mental model)

- `EngineEventResult` now defined in `engine_input.py`, re-exported from `src.engine`
- Input helpers renamed without leading `_` at module level
- `GameEngine` wrappers cleaner; public surface documented on the class docstring
- No intentional gameplay changes

## Automated (already run)

- Engine/input/floor/rest/examine suite → **98 passed** (`-n 6`)

## Sign-off

Designer: smoke OK → authorize PR8 (AI package + explore extract).
