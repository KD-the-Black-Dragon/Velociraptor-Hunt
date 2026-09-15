# Manual testing checklist — PR3 (Options → Mods UI)

**How to run:** `python -m src.main`  
**Automated:** `python -m pytest tests/test_mods_menu.py tests/test_options_menu.py tests/test_options_fullscreen.py -v -n auto`

## Automated (agent)

- [x] Mods menu + options regression tests — passed

## Happy path

Mods folder: `%LOCALAPPDATA%\KD's Vore Roguelike\mods\`

- [ ] Create two empty mod folders (or with `entities.json` from PR2) so the list is non-empty
- [ ] Main menu → **Options** → **Mods...** (no save) → enters Mods without Y prompt
- [ ] **Left/Right** or **Enter** toggles Enabled/Disabled; `mod.state` updates on disk
- [ ] **PgUp / PgDn** reorder mods; order numbers rewrite (`1..N`)
- [ ] **Escape** leaves Mods → back to Options; entity data reloads (PR2 pipeline)
- [ ] **Escape** Options → main menu

## Save wipe gate (capital Y)

- [ ] Start **New Game**, play a moment (autosave exists), **Ctrl+Q** → **Y** to menu
- [ ] Options → Mods... → warning about **deleting saved game** appears
- [ ] Lowercase **y** / wrong keys → error hint; save still present; still on Options
- [ ] Lowercase **n** or **Escape** → cancel; save still loadable; still on Options
- [ ] Options → Mods... → capital **Y** → save deleted (**Load Game** gone); Mods opens
- [ ] Escape Mods → Options → main menu; **Load Game** still absent

## Empty list

- [ ] With no mod folders: Mods shows “No mods found…”; Escape still works

## Keyboard reference

| Key | Action |
|-----|--------|
| Up / Down | Select mod |
| Left / Right / Enter | Toggle enable |
| Page Up / Page Down | Reorder (load order) |
| Escape | Back (reload data) |

## Regression

- [ ] Vore toggles, UI Layout, Fullscreen still work on Options
- [ ] New Game overwrite Y/n still works
- [ ] PR2: bad mod still popups on load/reload when present

## Out of scope this PR

- Other JSON domains (weapons, etc.)
- Save fingerprint / load refusal (PR6)
