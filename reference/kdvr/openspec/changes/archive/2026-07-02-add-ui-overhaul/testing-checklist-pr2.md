# Manual checklist — PR2 (tile scale + root console sizing)

Run: `python -m src.main`

## Readability

- [ ] Menu text is visibly **~2× taller** than before (larger glyphs)
- [ ] In-game map tiles and HUD text are also larger
- [ ] Text remains crisp and readable (not blurry)

## Layout / regression

- [ ] Main menu centers correctly; all options visible
- [ ] New Game → name entry → dungeon: full map + bottom HUD still visible (no clipping)
- [ ] Message log still shows recent lines at bottom
- [ ] Modals (inventory `i`, examine `x`) still readable and centered
- [ ] Options menu still usable

## Settings (no UI toggle yet)

- [ ] Game runs with fresh/default `{user_data}/settings.json` (no `ui_preset` field required)
- [ ] Optional: add `"ui_preset": "wide_sidebar"` to `{user_data}/settings.json`, relaunch — still runs (preset stored; layout not wired until later PRs)

## Automated

- [ ] `pytest tests/test_ui_bootstrap.py tests/test_ui_layout.py tests/test_settings_store.py`