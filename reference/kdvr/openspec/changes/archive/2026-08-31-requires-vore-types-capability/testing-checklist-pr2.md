# Manual testing — PR2 (initiation capability filter)

## How to run

`python -m src.main`

## Happy path (stock — should look unchanged)

- [ ] New Game with all three types on — enemies still attempt OV/CV/AV as before (stock `requires_vore_types: []`)
- [ ] New Game with only one type on — enemies only attempt that enabled type (prefs filter still works)
- [ ] Get engulfed / watch NPC vore — no crashes; narrative types still make sense

## Capability filter (optional mod check)

Edit or add a mod entity with full `vore_narratives` for OV/CV/AV but:

```json
"spawn": { "requires_vore_types": ["CV"] }
```

- [ ] With all prefs on — that species only ever attempts **CV** (never OV/AV modal or NPC log type)
- [ ] With only OV enabled — that species does **not** spawn (PR1 OR); if somehow present from an old save, it should not initiate (empty pool; GENERIC is PR3)

## Regression

- [ ] Save/load mid-run still works
- [ ] Shift+D dismiss / recent UX still fine

Full automated coverage: `tests/test_requires_vore_types_initiation_pr2.py`
