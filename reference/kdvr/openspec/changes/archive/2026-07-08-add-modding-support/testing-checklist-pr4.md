# Manual testing checklist — PR4 (id catalogs)

**How to run:** `python -m src.main`  
**Automated:** `python -m pytest tests/test_mod_id_catalogs.py tests/test_mod_entities_pipeline.py -v -n auto`

## Automated (agent)

- [x] Id catalog + entity pipeline tests — passed

## Happy path (mods under `%LOCALAPPDATA%\KD's Vore Roguelike\mods\`)

Create one or more mod folders with optional JSON files:

| File | Check |
|------|--------|
| `weapons.json` | New weapon id and/or override of a stock id (e.g. `dagger`) |
| `armor.json` | Same pattern |
| `potions.json` | Same pattern |
| `wands.json` | Same pattern |
| `floor_runes.json` | New/override rune by `id` |
| `macguffins.json` | New/override macguffin by `id` |
| `names.json` | Replace `knight` pool and/or add pool for a mod entity id |

- [ ] Place a valid `weapons.json` override (copy stock entry, change `display_name`) → New Game → find/examine item reflects mod
- [ ] `names.json` with custom knight names → meet a knight with mod name
- [ ] Options → Mods → Escape reloads **all** id catalogs (not just entities)
- [ ] Partial mod (only `weapons.json`) still works; other domains stay core

## Bad mod

- [ ] Broken `weapons.json` in a mod → **Mod data error** popup names mod + file; game continues with core weapons
- [ ] Broken `names.json` → same; knight names stay stock

## Regression

- [ ] No mods → stock items/runes/macguffins/names unchanged
- [ ] Entities modding (PR2) still works
- [ ] Options / Mods UI (PR3) still works

## Out of scope this PR

- `dungeon_spawn.json`, `rescue_gratitude.json`, `ui_layout.json` (PR5 whole-file)
- Save fingerprint (PR6)
