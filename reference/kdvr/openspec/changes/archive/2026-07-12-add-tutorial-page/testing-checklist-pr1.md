# Manual testing — PR1 onboarding

Run: `python -m src.main`

Reset first-run: set `"tutorial_prompt_answered": false` and `"vore_prefs_onboarding_complete": false` in `%LOCALAPPDATA%\KD's Vore Roguelike\settings.json`, or delete the file.

## Tutorial prompt

- [ ] First launch shows welcome prompt, not main menu
- [ ] Enter with nothing selected does nothing
- [ ] Up/Down highlights Yes/No with yellow background and `> `
- [ ] **No** → decline notice → Enter → vore prefs screen
- [ ] **Yes** → tutorial page 1

## Tutorial pages (Yes path)

- [ ] Enter advances page 1 → page 2 → reminder → vore prefs
- [ ] No Esc during first-run chain
- [ ] Proportional font readable; red emphasis on key lines
- [ ] Page 2 mentions TYUGHJBNM, arrows, vore/digestion, runes, isolated rest

## Vore prefs (first launch)

- [ ] Shown after tutorial or after declining tutorial
- [ ] Enter no-op until arrow selects a row
- [ ] Toggle OV/CV/AV; cannot disable last type
- [ ] Confirm row + Enter → "You're all set!" screen → Enter → main menu
- [ ] Relaunch skips prompt and vore screen

## Options → Tutorial

- [ ] Tutorial row between Fullscreen and Mods
- [ ] Pages 1–2 only; Esc returns to Options
- [ ] No vore onboarding from Options

## Regression

- [ ] Main menu, New Game, Options vore rows, save/load unchanged after onboarding complete