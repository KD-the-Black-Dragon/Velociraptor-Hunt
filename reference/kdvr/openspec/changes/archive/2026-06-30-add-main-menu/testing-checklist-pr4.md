# Manual checklist — Main Menu PR 4

Run: `python -m src.main`

## Flow integration (this PR)

- [ ] **Ctrl+Q** during gameplay shows `Do you want to quit? (Y/n)`
- [ ] Capital **Y** abandons the run and returns to the **main menu**
- [ ] Lowercase **n** dismisses the prompt and resumes play
- [ ] Any other key shows `Please type capital 'Y' or lowercase 'n' only.`
- [ ] **Ctrl+Q** during vore, digestion, or recap **modal** does **nothing** (Enter only)
- [ ] Post-digestion recap **Enter** returns to **main menu** (does not exit the app)
- [ ] Recap text says **Press Enter to return to menu**
- [ ] **Load Game** shows **Coming soon**; **Escape** or **Enter** returns to menu
- [ ] **High Scores** shows **Coming soon**; **Escape** or **Enter** returns to menu

## Regression

- [ ] Main menu, name entry, options (PR 1–3) unchanged
- [ ] **Exit** and window **X** still quit the process
- [ ] **Ctrl+Q** on menu / name / options / stubs is still no-op
- [ ] Debug keys **R**, **F2**, **S** still work during gameplay
- [ ] Movement, combat, vore, digestion otherwise normal