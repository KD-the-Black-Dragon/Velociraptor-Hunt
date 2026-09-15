# Manual checklist — PR4 (camera viewport)

Run: `python -m src.main`

## Map viewport

- [ ] Map shows a **smaller window** (~48×34 tiles), not the full dungeon
- [ ] View stays **centered on the player** while moving
- [ ] Camera stops at map edges (no empty void past borders)
- [ ] Dark **sidebar gutter** on the right (empty placeholder, no content yet)

## HUD

- [ ] Status + message log start **below** the map viewport (more vertical room than PR3)
- [ ] Message log may show more lines than before (bonus from shorter map band)

## Overlays & tools

- [ ] Examine cursor (`x`) tracks correctly on visible tiles
- [ ] Wand evoke targeting cursor appears on correct tile
- [ ] Rune flash still visible when stepping on a rune
- [ ] Engulfed overlay (red `#` walls) still surrounds player while engulfed

## Regression

- [ ] Modals (inventory, vore) still readable
- [ ] No crash moving around large maps

## Automated

- [ ] `pytest tests/test_ui_camera.py tests/test_ui_regions.py tests/test_vore_render.py -q`