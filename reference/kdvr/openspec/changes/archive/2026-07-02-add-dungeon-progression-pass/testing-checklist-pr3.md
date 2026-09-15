# Manual checklist — PR3 (rune placement)

Run: `python -m src.main`

- [ ] Each floor has exactly one visible rune glyph (not `#`)
- [ ] Rune is not near the entrance (~30+ steps on a normal floor; far enough that you cannot stumble on it immediately)
- [ ] NPCs do not stand on the rune tile
- [ ] Stepping on rune does **not** activate yet (placement-only PR)
- [ ] Regression: spawning and descent still work