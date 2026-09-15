# Credits Page — Manual Testing Checklists

Consolidated from PR1–PR3. Run the game with `python -m src.main`.

## PR1 — Credits screen module

Automated: `pytest tests/test_credits_screen.py -q`

- [x] Module content verified by automated tests (21 lines, attributions, Esc→BACK, footer)
- [x] Credit line: **K.D. — Curator of Voracious Beasts**
- [x] Links: `patreon.com/KD_Dragon`, `furaffinity.net/user/kd`

## PR2 — Menu integration

Automated: `pytest tests/test_credits_screen.py tests/test_main_menu.py tests/test_credits_menu_pr2.py tests/test_credits_present_pr2.py tests/test_past_runs_menu_pr4.py tests/test_save_menu_pr4.py -q`

- [x] **Credits** on main menu above **Exit** (user playtest PR2)
- [x] Enter opens credits; Esc returns to menu
- [x] Proportional Source Sans 3 when TTF loads
- [x] Ctrl+Q no-op on credits screen
- [x] Main menu regression (user playtest PR2)

## PR3 — Acceptance

- [x] Copy tweaks: Curator of Voracious Beasts; `furaffinity.net/user/kd` (user)
- [ ] End-to-end credits flow re-confirmed at acceptance
- [x] Live spec updated (`main-menu/spec.md`)
- [ ] Full pytest suite recorded in acceptance report