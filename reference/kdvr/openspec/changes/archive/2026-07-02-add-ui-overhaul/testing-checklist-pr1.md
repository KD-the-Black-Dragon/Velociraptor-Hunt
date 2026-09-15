# Manual checklist — PR1 (layout config loader)

PR1 adds data + loader only; **no visible in-game change**.

## Automated

- [ ] `pytest tests/test_ui_layout.py` passes

## Optional dev sanity (no UI change expected)

Run: `python -m src.main`

- [ ] Game still launches and plays normally (layout not wired yet)
- [ ] No new errors in console

## JSON tuning smoke (optional)

Edit `data/ui_layout.json` → `presets.standard.map_viewport_tiles.w` (e.g. 44), update matching `regions.map_viewport.w`, rerun `pytest tests/test_ui_layout.py` — should pass when regions stay consistent.