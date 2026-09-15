# Manual testing checklist — PR6 (engine input extract)

**Change:** `engineering-maintainability`  
**PR:** 6 — Move input/modals/gameplay keys into `src/engine_input.py` (mechanical)

## How to run

```text
python -m src.main
```

## Base smoke (required every PR)

- [ ] Game launches (main menu appears; no traceback on start)
- [ ] New Game starts a run (map, log, player visible)
- [ ] Play until game over is reachable (e.g. digestion defeat)
- [ ] No crash during the above

## PR6-specific (input paths)

This PR moved **all keyboard gameplay handling** (movement, inventory, examine, doors, rest key, come-here, debug keys, modal routing).

- [ ] Move with arrows/numpad — walk and bump-fight work
- [ ] Wait / rest keys still work
- [ ] Open inventory (`i` or your inspect key) and cancel with Escape
- [ ] Pickup (`,`) if items on ground
- [ ] Examine (`x`) cursor + Escape
- [ ] Close door flow if you hit a door (`c` then direction) — optional
- [ ] Descend (`>`) still works after finding stairs

## Automated (already run)

- Input-focused suite → **134 passed** after patch path fix; rest/come-here/examine/doors **55 passed** re-check

## Sign-off

Designer: smoke OK → authorize PR7 (engine deeper cleanup).
