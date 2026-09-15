# Manual testing checklist — PR2 (Options + data + snapshot)

**How to run:** `python -m src.main`  
**Automated:** `python -m pytest tests/test_alternate_cv_pr2.py tests/test_options_fullscreen.py::test_option_row_count_includes_fullscreen_and_mods -v -n 4`

## Automated (agent)

- [x] PR2 tests — run by agent

## Happy path

- [ ] Options → find **Alternate CV Mechanics: [No] ► Yes** (after 4K row)
- [ ] Toggle to **Yes**, Escape back; reopen Options → still **Yes** (persisted)
- [ ] Toggle back to **No**
- [ ] **New Game** with Yes set — run starts (no gameplay CV rules yet until PR3; flag is snapshotted)
- [ ] Save mid-run (if you can) / quit; confirm no crash. After PR3, Load will restore the Yes/No snapshot independently of current Options

## Regression

- [ ] Vore prefs / Difficulty / 4K / Tutorial / Mods rows still work
- [ ] Row navigation wraps correctly with the extra row
- [ ] Stock difficulties still load (game reaches main menu)

## Out of scope this PR

- Zero struggle damage / auto-daze on CV escape or digest (PR3)
