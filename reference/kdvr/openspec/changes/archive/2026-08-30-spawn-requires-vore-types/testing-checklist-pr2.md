# Manual testing — PR2 (stock field + Sample Mod refresh + docs)

How to run: `python -m src.main`

## Stock data

- [ ] New Game — floors still populate normally (empty `requires_vore_types` on stock = no new gate)
- [ ] Toggle only OV / only CV / only AV — density still feels full

## Sample Mod refresh

- [ ] After launch, open `{user_data}/mods/Sample Mod/entities.json` — it includes `spawn.requires_vore_types` and `engulfed_flavor`
- [ ] Edit Sample Mod `entities.json` to junk, relaunch — file restored to shipped template
- [ ] Enable Sample Mod in Options → Mods, relaunch — still **Enabled** (`mod.state` preserved); `entities.json` still matches template if it had drifted
- [ ] Copy Sample Mod to a new folder name, edit that copy — your copy is **not** overwritten on launch

## Docs

- [ ] `mods/MODDING_README.txt` mentions `spawn.requires_vore_types` and Sample Mod game-owned refresh
- [ ] Optional: skim README Modding section / `data/SCHEMA.md` for the new field

## Regression (PR1)

- [ ] Alliance potion / summons / arena still work
- [ ] Save/load mid-run — NPCs remain

## Full checklist

See `openspec/changes/spawn-requires-vore-types/tasks.md` (PR2).
