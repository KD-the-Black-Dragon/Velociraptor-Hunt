# Manual testing checklist — PR2 (entities layered load)

**How to run:** `python -m src.main`  
**Automated:** `python -m pytest tests/test_mod_entities_pipeline.py tests/test_mod_discovery.py -v -n auto`

## Automated (agent)

- [x] `tests/test_mod_entities_pipeline.py` + discovery tests — passed

## Happy path

User mods root (Windows): `%LOCALAPPDATA%\KD's Vore Roguelike\mods\`

- [ ] Create `mods/CoolDragon/entities.json` with a valid **new** entity id (copy a stock entity from `data/entities.json`, change `id` / `display_name` / glyph). Include `mod.state` or let first load create it (`E` + order).
- [ ] Launch game → New Game → confirm the new species can appear (or is in data; spawn depends on weights/depth).
- [ ] Create `mods/HardWolf/entities.json` that redefines stock id `wolf` with a different `display_name` / `max_hp`.
- [ ] Restart / New Game → examine a wolf (or fight) and confirm override took effect for that session.
- [ ] Disable via `mod.state` → `D 1`, restart → stock wolf returns.

## Bad mod (must not be silent)

- [ ] Create `mods/Cool_Dragon_Mod/entities.json` with broken JSON (`{ not json`).
- [ ] Launch game → **Windows dialog** “Mod data error” naming **Cool_Dragon_Mod** and **entities.json**.
- [ ] Dismiss dialog → game still reaches main menu; core content still works.
- [ ] Check `%LOCALAPPDATA%\KD's Vore Roguelike\logs\startup_error.log` has the same detail.

## Edge / regression

- [ ] No mods folder / empty mods → game behaves as stock (core only)
- [ ] Explicit single-file tools still work (dev load of one JSON path unchanged for tests)
- [ ] Main menu, New Game, combat, Options still work

## Out of scope this PR

- Options → Mods UI, save wipe, other JSON domains (weapons, etc.)
