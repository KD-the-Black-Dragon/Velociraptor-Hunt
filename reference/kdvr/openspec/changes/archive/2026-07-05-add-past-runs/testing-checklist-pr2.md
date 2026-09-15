# Manual checklist — PR2 (Ending model + Past Runs store)

Run: `python -m src.main`

PR2 records completed runs to `{user_data}/past_runs.json` on game over. The menu still shows **High Scores** (stub) — Past Runs UI is PR4.

## Game over recap (unchanged layout for now)

- [ ] Start New Game, get digested by an enemy
- [ ] After digestion modal, recap still shows player name and **Digested by {predator}**
- [ ] **Enter** returns to main menu
- [ ] Load Game is **not** shown after game over (saves wiped)

## Past run recorded (verify via file)

After one game over, check `{user_data}/past_runs.json` exists and contains one entry with:
- [ ] Your character name
- [ ] `ending_kind`: `"digested"`
- [ ] `ending_detail`: predator name (e.g. `"wolf"`)
- [ ] `monsters_defeated`, `runes_collected`, `depth` matching your run
- [ ] `date` in MM/DD/YYYY format

## Quit-to-menu does NOT record

- [ ] Start a run, Ctrl+Q → Y to menu
- [ ] `{user_data}/past_runs.json` is unchanged (no new entry for abandoned run)

## Regression

- [ ] New Game / Load Game / Options / Exit still work
- [ ] Combat, runes, struggle still behave normally

Automated: `pytest tests/test_game_over_ending.py tests/test_past_runs_store.py tests/test_digestion.py tests/test_save_game_over_pr5.py -q`