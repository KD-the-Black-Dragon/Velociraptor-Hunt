# Manual checklist — PR4 (Past Runs menu screen)

Run: `python -m src.main`

## Menu gating

- [ ] Fresh install / no `{user_data}/past_runs.json`: main menu has **no** Past Runs option (New Game, Options, Exit — or Load Game if save exists)
- [ ] After at least one game over: **Past Runs** appears on main menu
- [ ] Quit-to-menu without game over does **not** add Past Runs option

## Past Runs screen

- [ ] Select **Past Runs** → full-screen table with title **PAST RUNS**
- [ ] Column header: Name | Ending | Monsters | Runes | Depth | Date
- [ ] Your completed run(s) appear with correct name, ending, stats, depth, date
- [ ] Rows sorted by depth descending (deepest at top of data)
- [ ] **Escape** returns to main menu
- [ ] With many runs (or narrow window): **Up/Down** scroll one line; **PgUp/PgDn** scroll a page
- [ ] Footer shows scroll hint

## Regression

- [ ] New Game, Load Game (when present), Options, Exit still work
- [ ] Game over recap still shows stats (PR3)
- [ ] `{user_data}/past_runs.json` still updated on game over (PR2)

Automated: `pytest tests/test_past_runs_menu_pr4.py tests/test_main_menu.py tests/test_flow_pr4.py tests/test_save_menu_pr4.py -q`