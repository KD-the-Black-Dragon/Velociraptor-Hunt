# Manual testing checklist — PR1 (entity deep merge)

**How to run:** `python -m src.main`  
**Automated:** `python -m pytest tests/test_mod_json_merge.py tests/test_mod_entities_pipeline.py -v -n 4`

## Automated (agent)

- [x] `tests/test_mod_json_merge.py` + `tests/test_mod_entities_pipeline.py` — run by agent

## Happy path

User mods root (Windows): `%LOCALAPPDATA%\KD's Vore Roguelike\mods\`

- [ ] Create `mods/NoWolves/entities.json`:

```json
{
  "schema_version": 1,
  "entities": [
    { "id": "wolf", "spawn": { "weight": 0 } }
  ]
}
```

  Leave `mod.state` to auto-create (Enabled), or set `E 1`.

- [ ] Launch → **Options → Mods...** → confirm `NoWolves` is enabled (capital **Y** if a save wipe warning appears — this deletes the autosave).
- [ ] Leave Mods (reload) → **New Game** → play several floors / check examine or spawn behavior: **wolves should not appear** as new spawns.
- [ ] Confirm other species still spawn and combat/narratives still work (stock wolf text is unchanged for any residual/debug cases; primary check is no wolf spawns).

## Nested / rename patch

- [ ] Create `mods/RenameWolf/entities.json` with only `{ "id": "wolf", "display_name": "Dire Wolf" }` (and `schema_version` / `entities` wrapper). Enable it **after** disabling or removing `NoWolves` (or set spawn weight back if both enabled — last mod wins on overlapping keys).
- [ ] New Game → if a wolf spawns, examine / sidebar name should show **Dire Wolf**; combat stats should still feel like stock wolves (not a stub).

## Bad / incomplete mod (must not be silent)

- [ ] Create `mods/StubDragon/entities.json` with a **new** id that is incomplete, e.g. only `id` + `display_name`.
- [ ] Reload mods / launch → **Mod data error** dialog naming **StubDragon** and **entities.json**.
- [ ] Dismiss → main menu still works; core entities still load.

## Edge / regression

- [ ] Empty / no mods → stock game unchanged
- [ ] Full-copy override mod (complete wolf object with new `max_hp`) still works if you still have one
- [ ] Weapons / other id catalogs still full-replace (unchanged this PR — smoke: game starts, inventory items load)
- [ ] Save/load fingerprint behavior unchanged if you use Mods UI (entering Mods with a save still requires **Y** and deletes save)

## Out of scope this PR

- README / SCHEMA / live modding spec wording (PR2)
- Deep merge for items / names
