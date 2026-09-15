# Manual checklist — Main Menu PR 3

Run: `python -m src.main`

## Options and persistence (this PR)

- [ ] **Options** from main menu opens the options screen
- [ ] Three rows: **Oral Vore**, **Cock Vore**, **Anal Vore** with **ON** / **OFF**
- [ ] **Up / Down** moves highlight; **Left / Right** or **Enter** toggles the highlighted row
- [ ] Disabling a type works when at least one other stays **ON**
- [ ] Attempting to disable the **last** enabled type does nothing (stays **ON**)
- [ ] **Oral Vore** can be turned **OFF** when Cock or Anal Vore remains on
- [ ] **Escape** returns to main menu
- [ ] Changes persist: toggle a type, exit game, relaunch — setting remains
- [ ] `{user_data}/settings.json` updates when you toggle (optional: inspect file)
- [ ] New game uses saved prefs (e.g. only Anal Vore on → vore narratives skew AV when triggered)

## Regression

- [ ] Main menu, name entry (PR 1–2) unchanged
- [ ] Exit, window close, Ctrl+Q on menu/name/options no-op behavior
- [ ] Gameplay, digestion, message log otherwise normal