# Manual checklist — PR6

Run: `python -m src.main`

## Sidebar player block

- [ ] Right column (beside map) shows **player display name** on line 1
- [ ] Line 2 shows **HP current/max** and a **filled bar** (`[#---]`)
- [ ] HP bar width looks proportional (~20 chars in standard preset)
- [ ] **No** stunned / engulfed / depth text in sidebar (PR8 status corner)
- [ ] Remainder of sidebar below player block is empty dark background (NPC list in PR7)

## Regression (PR2–PR5)

- [ ] Map viewport 48×34, camera-centered
- [ ] Message log 8 lines, 72 cols wide at bottom-left
- [ ] Status corner gutter still empty at bottom-right
- [ ] Tile scale 2× readable