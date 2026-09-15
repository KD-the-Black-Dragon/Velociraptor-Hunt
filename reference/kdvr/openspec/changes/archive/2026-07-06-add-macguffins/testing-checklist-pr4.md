# Manual checklist — PR4 (game over)

Run game: `python -m src.main`

- [ ] Y on victory prompt → game over recap shows `found The {name}!` (article rule)
- [ ] Enter on recap → main menu; autosave wiped
- [ ] Past Runs entry shows macguffin ending (not digested); no predator mention on override
- [ ] Decline victory, then get digested → recap shows macguffin ending, not `Digested by …`
- [ ] Save/load after declining preserves discovery (digest later still overrides)
- [ ] Save/load mid-modal (if reproducible): discovery kept, modal gone, same turn count as step-on

Automated: `pytest tests/test_macguffins_pr4.py tests/test_game_over_ending.py -q`