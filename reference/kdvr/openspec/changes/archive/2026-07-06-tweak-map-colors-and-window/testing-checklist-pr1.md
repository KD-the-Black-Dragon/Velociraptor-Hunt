# Manual checklist — PR1 (map tile colors)

Run: `python -m src.main`

## Map palette

- [ ] Start a new game and enter the dungeon
- [ ] **Visible floor** tiles (`.`) appear **dark grey**, not gold/yellow
- [ ] **Visible walls** (`#`) appear **mid grey**
- [ ] **Visible doors** (`+` / `-`) appear **mid grey** (same family as walls)
- [ ] **Stairs** (`>`) still use the **gold/yellow** visible color
- [ ] **Water** (`~`) still uses **blue** visible color
- [ ] Move so previously seen tiles leave FOV — **explored-only** tiles still use **blue-tinted** dim colors (not grey)

## Regression

- [ ] Main menu, Options, and gameplay UI unchanged
- [ ] Window behavior unchanged from pre-PR1 (still fixed design size until PR2)