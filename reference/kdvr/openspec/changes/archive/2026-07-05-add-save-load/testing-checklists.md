# add-save-load — Consolidated Manual Checklist

Run: `python -m src.main`

Saves live in `{user_data}/saves/` (via `src/user_data.py`). Delete that folder to simulate a fresh install.

---

## Automated gate (save/load)

```bash
python -m pytest tests/test_save_snapshot.py tests/test_save_store.py tests/test_save_coordinator.py tests/test_save_menu_pr4.py tests/test_save_game_over_pr5.py tests/test_save_write_failure.py -q
```

---

## PR1 — Snapshot round-trip (engine only)

- [ ] New game runs normally
- [ ] In-memory snapshot → restore preserves player position, floor depth, inventory

## PR2 — File store

- [ ] After play, `{user_data}/saves/autosave.json` exists
- [ ] Repeated saves create `autosave.bak1.json` … `bak3.json` over time

## PR3 — Background autosave

- [ ] Entering PLAY writes an initial autosave
- [ ] ~15 turns or ~30s idle triggers background save (no UI freeze)
- [ ] Descending stairs triggers save
- [ ] Engulfed player gets per-turn danger saves

## PR4 — Menu + quit + manual save

- [ ] No save: menu shows 4 options (Load Game absent)
- [ ] With save: Load Game restores run into PLAY
- [ ] New Game with existing save → overwrite confirm (capital **Y**)
- [ ] Name entry Escape preserves old save
- [ ] Ctrl+Q (idle) → quit modal + background save; **n** resumes; **Y** → menu with save intact
- [ ] Ctrl+S (idle) → "Game saved." in log
- [ ] Ctrl+S / Ctrl+Q blocked during vore, digestion, inventory modals

## PR5 — Game over wipe

- [ ] Get digested → autosave files deleted when game over opens
- [ ] Recap → menu: Load Game absent until new run saves

## Save failure (graceful)

- [ ] If autosave cannot write (e.g. file locked), game does not crash
- [ ] Ctrl+S failure shows red **"Save failed."** in message log
- [ ] Background failure surfaces **"Save failed."** on next input poll

## Regression

- [ ] Options / vore prefs unchanged for loaded run vs global settings
- [ ] High Scores stub still works
- [ ] Debug keys R / F2 / S still work in gameplay (S = stunned debug, not save)