# Manual checklist — PR1 (Run statistics + save round-trip)

Run: `python -m src.main`

PR1 has **no visible UI changes**. Stats are tracked internally and persist through save/load only.

## Baseline smoke

- [ ] Game starts normally (New Game → name → play)
- [ ] Bump-combat still defeats evil NPCs and logs "defeated"
- [ ] Stepping on a floor rune still applies bonus and logs activation
- [ ] Struggle while engulfed still works (F2 test predator if needed)
- [ ] Wand evoke still damages/defeats targets

## Save/load (if you have a save from prior sessions)

- [ ] Load Game restores the run normally
- [ ] After load, gameplay (move, combat, runes) behaves as before

## Regression from save/load module

- [ ] Quit-to-menu (Ctrl+Q → Y) still returns to menu with Load Game available
- [ ] Game over still shows recap and returns to menu on Enter

Full automated coverage: `pytest tests/test_run_stats.py tests/test_save_snapshot.py -q`