# Manual checklist — PR10

Run: `python -m src.main`

## Menu screens (layout console 80×42)

- [ ] **Main menu** — title banner and all five options visible (not clipped at bottom)
- [ ] **Name entry** — prompt, input line, and hint visible and centered
- [ ] **Options** — all vore rows + UI layout row + hint visible
- [ ] **Load Game / High Scores** stubs centered on screen
- [ ] Text size matches gameplay (same 2× tile scale)

## Gameplay modals (map viewport only)

- [ ] **Examine** (`x`) — description box centered over map, sidebar/log/corner still visible
- [ ] **Inventory** (`i` etc.) — modal box over map region only
- [ ] **Ground pickup** (multiple items) — modal over map
- [ ] **Vore / digestion** modals — centered on map, not over sidebar
- [ ] **Game over** recap — box over map viewport
- [ ] **Ctrl+Q quit confirm** — prompt centered over map area (not bottom HUD row)

## Regression

- [ ] Camera, sidebar, message log, status corner unchanged from PR5–PR9
- [ ] Evoke target cursor still works on map viewport