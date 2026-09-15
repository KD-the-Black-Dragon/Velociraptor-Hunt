# Manual testing — PR7 (sentence confirms + game-over body)

**How to run:** `python -m src.main`

Sentence confirms and game-over **body** use the digestion dialog font when available. Game-over **title** stays fixed-width “GAME OVER”.

## Happy path

### Confirms (proportional)
- [ ] Main menu → New Game with an existing save → overwrite **Y/n** prompt uses log font (lower band)
- [ ] Load Game with mod mismatch (if available) → notice uses log font
- [ ] Options → Mods with a save present → wipe warning uses log font
- [ ] In-run **Ctrl+Q** quit → “Do you want to quit? (Y/n)” uses log font
- [ ] Invalid key on a confirm shows error in the same panel (orange/red hint)
- [ ] Macguffin victory prompt (if you can trigger) uses log font

### Game over
- [ ] Finish a run (digested or victory) → **GAME OVER** title is tile/fixed feel
- [ ] Name, fate line, stats, “Press Enter…” use proportional log font
- [ ] Enter returns to menu

## Regressions
- [ ] Digestion / vore / examine still look approved
- [ ] Inventory multi-column still OK
- [ ] Message log still proportional
- [ ] Map tiles still CP437

## Automated (agent)

```bash
python -m pytest tests/test_text_ux_pr7_remaining.py -v
```

After final sign-off: full suite `python -m pytest tests/ -n 6` (re-run failures only).
