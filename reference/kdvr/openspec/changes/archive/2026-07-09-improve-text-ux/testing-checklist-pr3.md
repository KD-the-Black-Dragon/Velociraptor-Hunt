# Manual testing checklist — PR3 (shared dialog chrome)

**How to run:** `python -m src.main`  
**Automated:** `python -m pytest tests/test_text_ux_pr3_chrome.py tests/test_text_ux_pr1.py -n 6 -q`

## Automated (agent)

- [x] Chrome + PR1 layout tests — passed

## Happy path

- [ ] **New Game** with save → overwrite prompt in a **panel** (dark box + border), **below title logo**, wraps on narrow window
- [ ] **Ctrl+Q** in play → quit prompt uses same chrome (centered)
- [ ] Options → **Mods...** with save → wipe warning uses same chrome
- [ ] Step on a macguffin → victory Y/n uses same chrome
- [ ] Load Game with mismatched mods → notice in lower band **with panel**

## Input regression

- [ ] Capital **Y** / **n** / Esc still work on each prompt
- [ ] Invalid key still shows error line inside the panel

## Out of scope this PR

- Proportional log font on dialogs (PR4 trial = digestion modal)
