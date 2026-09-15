# Manual checklist — PR5

Run: `python -m src.main`

## Message log panel

- [ ] Bottom-left panel shows **8 lines** of messages (not clipped to ~3–5)
- [ ] Messages scroll: newest entries appear at the bottom of the 8-line window
- [ ] Message panel width matches map viewport width (72 cols), not full screen
- [ ] Dark gutter at bottom-right (8×8) beside the log — empty placeholder until PR8

## Regression (PR2–PR4)

- [ ] Map viewport still 48×34, centered on player
- [ ] Sidebar column (right of map) still dark placeholder
- [ ] Tile scale 2× — glyphs readable
- [ ] Examine cursor, evoke target, screen flash still camera-relative

## Known gaps until later PRs

- Player name / HP / depth **not** shown in engine HUD (PR6 sidebar + PR8 status corner)
- Engulfed / stunned flags not visible in engine render until PR8