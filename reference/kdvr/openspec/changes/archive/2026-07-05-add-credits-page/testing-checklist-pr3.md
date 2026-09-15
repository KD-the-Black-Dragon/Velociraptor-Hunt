# Manual checklist — PR3 (acceptance)

Run: `python -m src.main`

Automated gate: `pytest tests/test_credits_screen.py tests/test_main_menu.py tests/test_credits_menu_pr2.py tests/test_credits_present_pr2.py tests/test_past_runs_menu_pr4.py tests/test_save_menu_pr4.py -q`

Full suite: `python -m pytest -q`

## Credits (end-to-end)

- [ ] Main menu lists **Credits** above **Exit** in all probe configurations
- [ ] Credit line reads **K.D. — Curator of Voracious Beasts**
- [ ] Links: `patreon.com/KD_Dragon`, `furaffinity.net/user/kd`
- [ ] Credits page matches help/log visual style (dark background, proportional font)
- [ ] Esc returns to menu; Ctrl+Q no-op on credits screen

## Regression (full change)

- [ ] Main menu flow: New Game, Options, Exit
- [ ] Load Game / Past Runs (when present) unchanged
- [ ] In-game F1 help and Ctrl+P log unchanged

## Spec

- [ ] `openspec/specs/main-menu/spec.md` documents Credits requirement and four-to-six option range