# Manual testing checklist — PR5 (whole-file domains)

**How to run:** `python -m src.main`  
**Automated:** `python -m pytest tests/test_mod_whole_file.py -v -n auto`

## Automated (agent)

- [x] Whole-file catalog tests — passed

## Happy path

Mods: `%LOCALAPPDATA%\KD's Vore Roguelike\mods\<ModName>\`

| File | Behavior |
|------|----------|
| `dungeon_spawn.json` | **Replaces** entire core spawn density file |
| `rescue_gratitude.json` | **Replaces** entire gratitude lines file |
| `ui_layout.json` | **Replaces** entire layout document (presets, defaults) |

- [ ] Copy stock `data/dungeon_spawn.json` into a mod, raise `density_pct` a lot → New Game floors feel denser
- [ ] Copy stock `data/rescue_gratitude.json`, change one line → free an ally; see mod text
- [ ] Copy stock `data/ui_layout.json`, set `"default_preset": "wide_sidebar"` → Options UI Layout / new game layout reflects reload after Mods exit
- [ ] Options → Mods → Escape refreshes layout baseline (preset cycling still works)

## Bad mod

- [ ] Broken `dungeon_spawn.json` → **Mod data error** (mod + file); core density still used
- [ ] Empty gratitude `lines: []` → skipped; stock lines remain

## Regression

- [ ] No mods → stock spawn / gratitude / layout unchanged
- [ ] Id catalogs (PR4) and entities (PR2) still work
- [ ] Mods UI (PR3) still works

## Out of scope this PR

- Save fingerprint / Load Game mod mismatch (PR6)
- README docs (PR6)
