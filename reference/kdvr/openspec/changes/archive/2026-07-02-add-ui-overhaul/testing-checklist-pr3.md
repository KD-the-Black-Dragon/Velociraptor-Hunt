# Manual checklist — PR3 (region sub-console infrastructure)

Run: `python -m src.main`

## Visual parity (should match PR2)

- [ ] New Game → dungeon looks the same as PR2 (full map, bottom HUD)
- [ ] Message log and status line still present (same clipping behavior as PR2 is OK)
- [ ] Examine cursor (`x`) appears on correct tile
- [ ] Inventory / vore modals still work
- [ ] No new blank sidebar strip covering the map

## Structural (invisible)

- [ ] No crashes or Python tracebacks on menu → play → quit

## Automated

- [ ] `pytest tests/test_ui_regions.py tests/test_vore_render.py -q`