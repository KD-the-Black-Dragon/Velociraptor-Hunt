# Manual checklist — PR6 (help overlay F1, ?)

Run: `python -m src.main`

## Open / close

- [ ] During play, **F1** opens the full-screen help overlay.
- [ ] **?** (Shift+/) also opens help.
- [ ] **Esc** closes help and returns to normal play.
- [ ] Pressing **F1** or **?** again while help is open closes it.

## Content

- [ ] Help uses the **same proportional font** as the message log (Source Sans 3).
- [ ] Help lists movement (arrows, numpad, TYUGHJBNM) and **wait 1 turn** under Movement.
- [ ] Single-key actions use `key - description` format (e.g. `i - inspect inventory`).
- [ ] **5 - extended rest** and `> (Shift + .) - descend stairs when standing on '>' glyph`.
- [ ] Help lists meta: **Ctrl+P**, **F1**/**?**, **Ctrl+Q** with hyphen format.
- [ ] **No** debug keys (R, S, F2, F3, F4) in the help text.
- [ ] Footer shows `Esc: close`.

## Meta UI (not blocked)

- [ ] Help works during inventory, examine, rest animation, and vore modal.
- [ ] **Esc** closes help without closing the underlying modal.
- [ ] With help open, **Ctrl+P** closes help and opens the full log (PR5).

## Regression

- [ ] HUD log and **Ctrl+P** full log still work when help is closed.
- [ ] PR0–PR5 behavior intact.