# Manual testing checklist — PR1 (PlayerEffects infrastructure)

Run: `python -m src.main`

No new potions yet. Effects are only testable via code/debug or save inspection; smoke that normal play is unchanged.

## Regression

- [ ] New game starts; status corner shows Depth as usual
- [ ] No crash on turn-taking, rest, descend
- [ ] Save (autosave) and Load Game mid-run
- [ ] Heal potions still work
- [ ] Status corner still shows rune progress when present

## Optional (debug / future)

- [ ] After PR2+ potions: Fast / Might / Antacid / Tele? rows appear when active

## Automated

- [x] `tests/test_player_effects_pr1.py`
