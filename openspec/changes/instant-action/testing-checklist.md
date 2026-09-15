# Manual testing — Instant Action (Ctrl+B)

**Designer sign-off:** 2026-08-10 — all manual checks pass.

Run: `python -m src.main`

## Happy path

- [ ] Main menu: **Ctrl+B** opens Green/Red screen (no crash)
- [ ] **1** → Green card list; **2** → Red card list
- [ ] Typing filters the list (e.g. `wol` shows `r1_wolves`)
- [ ] Enter valid id (e.g. red `r1_wolves`) starts solo sand-pit match
- [ ] No allies in the bout
- [ ] Full combat (move, attack, balance, etc.) works
- [ ] Win/lose recap says **return to the main menu**
- [ ] Enter on recap → **main menu** (not downtime)
- [ ] Career Load Game still has prior save if any (instant did not overwrite)

## Edges

- [ ] Esc on card screen → back to Green/Red
- [ ] Esc on Green/Red → main menu
- [ ] Unknown id shows error
- [ ] Green card rejected after picking Red (if typed by hand)
- [ ] Ctrl+Q mid-match → confirm → main menu
- [ ] Ctrl+S mid-instant match → “not saved” (no file write)

## Regression

- [ ] New Game → career hub still works
- [ ] Normal match from hub still returns to downtime
