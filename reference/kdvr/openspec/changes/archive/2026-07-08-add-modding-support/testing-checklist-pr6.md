# Manual testing checklist — PR6 (saves, diagnostics, docs)

**How to run:** `python -m src.main`  
**Automated:** `python -m pytest tests/test_mod_fingerprint.py tests/test_crash_report.py -v -n auto`

## Automated (agent)

- [x] Fingerprint / load gate / crash mods tests — passed

## Save fingerprint + Load Game

- [ ] **No mods:** New Game → play a bit → quit to menu → **Load Game** works
- [ ] With a save present, enable a mod via Options → Mods (capital **Y** wipes save — expected). New Game with mod on → quit → Load Game works while that mod stays enabled
- [ ] **Explorer path:** With a modded save, manually set that mod to `D` in `mod.state` (or delete folder) without using Mods UI → **Load Game** stays on main menu with mismatch message; save files still on disk
- [ ] Re-enable the same mods → Load Game succeeds again
- [ ] **Pre-mod style:** empty mods + save from vanilla → Load with any mod enabled → refuse

## Crash report

- [ ] Enable a named mod → **F6** force crash in PLAY → `logs/crash.log` shows `Loaded mods: YourModName` (not `(none)`)
- [ ] No mods → crash still shows `Loaded mods: (none)`

## Docs

- [ ] README **Modding** section matches behavior
- [ ] `data/SCHEMA.md` has Modding cross-link

## Regression

- [ ] Mods UI, layering, bad-JSON popup still work
- [ ] New Game overwrite confirm still works
