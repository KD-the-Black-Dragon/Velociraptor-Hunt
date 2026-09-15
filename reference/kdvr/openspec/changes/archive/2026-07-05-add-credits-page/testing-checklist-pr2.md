# Manual checklist — PR2 (Credits menu integration)

Run: `python -m src.main`

Automated: `pytest tests/test_credits_screen.py tests/test_main_menu.py tests/test_credits_menu_pr2.py tests/test_credits_present_pr2.py tests/test_past_runs_menu_pr4.py tests/test_save_menu_pr4.py -q`

## Main menu

- [ ] **Credits** appears on the main menu, immediately **above Exit**
- [ ] Credits is visible whether or not Load Game / Past Runs are listed
- [ ] Up/Down highlight moves through Credits; Enter opens the credits page

## Credits screen

- [ ] Full-screen dark background (same feel as F1 help / Ctrl+P log)
- [ ] Title **KD's Vore Roguelike** at top
- [ ] K.D. credit line, Patreon and FurAffinity URLs, font and library attributions visible
- [ ] Proportional Source Sans 3 text when bundled TTF loads (same look as in-game help)
- [ ] Footer shows **Esc: close** centered at bottom

## Navigation

- [ ] **Esc** returns to main menu
- [ ] **Ctrl+Q** on credits screen is a no-op (does not exit app)

## CP437 fallback (optional)

Temporarily rename `data/fonts/SourceSans3-Regular.ttf`, restart the game, open Credits:

- [ ] Credits still readable via CP437 console font
- [ ] Restore font file after testing

## Regression

- [ ] New Game, Load Game (if present), Past Runs (if present), Options, Exit still work
- [ ] F1 / ? help during gameplay unchanged
- [ ] Ctrl+P message log during gameplay unchanged