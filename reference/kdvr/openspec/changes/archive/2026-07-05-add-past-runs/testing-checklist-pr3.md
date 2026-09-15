# Manual checklist — PR3 (Game over modal stats)

Run: `python -m src.main`

## Game over recap

- [ ] Start New Game, play until digested (or use F2 + engulf test setup)
- [ ] After digestion modal, recap shows:
  - [ ] Player name
  - [ ] **Digested by {predator}**
  - [ ] **Monsters defeated:** (count matches your run)
  - [ ] **Runes collected:** (count matches floor runes stepped on)
  - [ ] **Depth:** (matches status corner depth at death)
- [ ] No turn-count or "Score:" line
- [ ] **Enter** returns to main menu

## Sanity with stats

- [ ] Defeat at least one monster via bump combat before dying — monsters count ≥ 1 on recap
- [ ] Step on at least one floor rune before dying — runes count ≥ 1 on recap

## Regression

- [ ] Digestion modal still appears before recap
- [ ] Load Game still omitted after game over
- [ ] Quit-to-menu mid-run still does not write past runs (unchanged from PR2)

Automated: `pytest tests/test_name_entry.py tests/test_digestion.py -k game_over -q`