# Manual testing — PR2: Headless arena bot

## CLI smoke

- [ ] `python tools/sim_arena.py --difficulty normal --trials 2 --max-turns 100` exits 0 without a game window
- [ ] Stdout prints `seed: <n>` and `wrote arena_compare.csv`
- [ ] `arena_compare.csv` is a compare sheet: column A `metric`, column B+ run data
- [ ] Meta rows: `meta.seed`, `meta.difficulty_id`, `meta.trials_per_entity`, `meta.max_turns`
- [ ] Per entity: six metric rows (`enemy_id` … `enemy_win_hp_remaining`), blank row, next entity
- [ ] For each entity block: `player_wins + enemy_wins ≤ trials` (default 10)
- [ ] Second run (no flags) auto-appends column C without changing metric column
- [ ] `--overwrite` replaces the sheet with a single new column

## Reproducibility

- [ ] Two runs with same `--seed` produce identical CSV data rows

## Mods (if you use mods)

- [ ] Enable a mod that adds/changes an evil entity; re-run sim; new/changed id appears in CSV

## Regression

- [ ] `python tools/sim_balance.py --seconds 5` still runs (unaffected)
- [ ] Interactive Ctrl+B arena (PR1) still works