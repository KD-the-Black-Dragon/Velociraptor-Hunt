# Manual checklist — PR4 (rune activation)

Run: `python -m src.main`

- [ ] Three `0` glyphs per floor (colors differ by effect)
- [ ] Step on rune: screen flashes once, log shows bonus (e.g. +5 max HP)
- [ ] Vitality rune: HUD max HP increases; current HP increases by same amount
- [ ] Rune vanishes immediately; cannot re-trigger
- [ ] Accuracy/AC runes: combat feels stronger (check log message for numbers)
- [ ] Descend: rune buffs persist on new floor
- [ ] NPCs cannot activate runes