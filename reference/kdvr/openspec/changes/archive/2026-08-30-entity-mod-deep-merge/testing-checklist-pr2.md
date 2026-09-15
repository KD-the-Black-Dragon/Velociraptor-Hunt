# Manual testing checklist — PR2 (docs + live modding spec)

**How to run:** `python -m src.main`  
**Automated:** no new code paths this PR — optional smoke:  
`python -m pytest tests/test_mod_json_merge.py tests/test_mod_entities_pipeline.py -v -n 4`

## Doc / spec review

- [ ] `openspec/specs/modding/spec.md` — entities deep-merge requirement + scenarios; other catalogs still full-replace; whole-file unchanged
- [ ] `README.md` **Modding** — rules table distinguishes entities vs other ids; includes `spawn.weight: 0` example
- [ ] `data/SCHEMA.md` **Modding** — merge table + short entity patch note
- [ ] Launch the game once → `%LOCALAPPDATA%\KD's Vore Roguelike\mods\MODDING_README.txt` mentions entity deep-merge / patch tips (stale files are refreshed when contents differ; identical files are left alone)
- [ ] Sample Mod folder (if already present) is **not** wiped or rewritten on launch

## Smoke (patch mod — confirms docs match behavior)

User mods root (Windows): `%LOCALAPPDATA%\KD's Vore Roguelike\mods\`

- [ ] Create `mods/NoWolves/entities.json` exactly as in README (`wolf` + `spawn.weight: 0` only)
- [ ] Options → Mods… → enable → leave Mods (reload; capital **Y** if save wipe)
- [ ] New Game → wolves do not spawn; other content fine

## Regression

- [ ] Incomplete new entity id still shows Mod data error and skips that file
- [ ] PR1 behaviors still hold (rename-only patch, nested OV narrative if you try it)

## Out of scope this PR

- Acceptance archive / full suite (PR3)
