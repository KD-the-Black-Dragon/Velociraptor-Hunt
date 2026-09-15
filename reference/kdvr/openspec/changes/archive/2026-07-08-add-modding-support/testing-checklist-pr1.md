# Manual testing checklist — PR1 (mod discovery / `mod.state`)

**How to run the game:** `python -m src.main`  
**Automated:** `python -m pytest tests/test_mod_discovery.py -v -n auto`

PR1 has **no in-game Mods UI** yet. Manual checks are filesystem + optional REPL.

## Automated (agent already ran)

- [x] `tests/test_mod_discovery.py` — 13 passed

## Happy path (optional manual)

User data mods root (Windows): `%LOCALAPPDATA%\KD's Vore Roguelike\mods\`

- [ ] Create folder `mods/TestModA` (no `mod.state`)
- [ ] In a Python shell from the project:

  ```python
  from pathlib import Path
  from src.mods.discovery import discover_mods
  from src.user_data import MODS_DIR
  print(MODS_DIR)
  print(discover_mods())  # or discover_mods(Path(r"...your mods path..."))
  ```

- [ ] Confirm `TestModA/mod.state` was created with content like `E 1` (or next free order if other mods exist)
- [ ] Create `mods/TestModB` empty; run `discover_mods()` again → `TestModB` gets `E` with higher order
- [ ] Edit two mods to share the same order number; run discover → orders renumbered `1..N` on disk
- [ ] Put a loose file in `mods/not_a_mod.txt` → ignored (not listed as a mod)
- [ ] Game still launches: `python -m src.main` (no behavior change expected)

## Edge cases

- [ ] Malformed `mod.state` (`garbage`) → rewritten to `E <append order>`
- [ ] `D 3` preserved when unique and valid
- [ ] Second `discover_mods()` call does not thrash orders (idempotent)

## Regression

- [ ] Main menu / New Game / Options still work (modding not wired into loaders yet)
- [ ] Saves/settings paths unchanged

## Out of scope this PR

- Content merge, Options → Mods UI, save wipe, bad-JSON popup
