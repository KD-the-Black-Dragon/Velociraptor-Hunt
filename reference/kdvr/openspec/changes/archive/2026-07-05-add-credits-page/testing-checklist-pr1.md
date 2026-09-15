# Manual checklist — PR1 (credits screen module)

PR1 adds the credits screen module only — **no menu entry yet**. Verify via automated tests and optional isolated render inspection.

Automated: `pytest tests/test_credits_screen.py -q`

## Module content (automated)

- [x] `credits_display_lines()` returns 21 rows
- [x] Title **KD's Vore Roguelike** present
- [x] K.D. credit line (Curator of Voracious Beasts)
- [x] Links: `patreon.com/KD_Dragon`, `furaffinity.net/user/kd`
- [x] Font attribution: Source Sans 3 OFL, CP437 tile font via libtcod
- [x] Library attribution: Python PSF, tcod, tcod-ecs, numpy, Pillow, attrs (transitive)
- [x] Esc → `CreditsAction.BACK`
- [x] `render_credits_screen()` draws title and **Esc: close** footer

## In-game (not applicable this PR)

- [ ] **Credits** menu option — deferred to PR2
- [ ] Opening credits from main menu — deferred to PR2
- [ ] Proportional Source Sans 3 presentation — deferred to PR2

## Regression

- [ ] Main menu unchanged (no Credits option visible yet)
- [ ] Help overlay (F1 / ?) still works during gameplay
- [ ] Message log (Ctrl+P) still works during gameplay