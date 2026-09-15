# PR 1 Manual Testing Checklist — Faction NPC Spawn

Run `python -m src.main` from the project root.

---

## Automated gate

```bash
python -m pytest tests/test_enhancements_3.py -v
python -m pytest tests/ -q
```

All tests should pass.

---

## Map population

- [ ] **6** red **`o`** wolves (evil)
- [ ] **5** cyan **`k`** knights (good)
- [ ] **6** grey **`r`** rabbits (neutral)
- [ ] Total **17** NPCs on a new game (plus potions as before)

## Examine (`x`)

- [ ] Wolf — vicious/ferocious placeholder
- [ ] Knight — *"A noble figure in medieval armor."*
- [ ] Rabbit — *"A small and harmless lagomorph."*

## Regression

- [ ] Wolves still chase and attack the player (evil AI unchanged until PR 3)
- [ ] Player swap with good/neutral still works if you temp-align a wolf (optional)
- [ ] Vore, potions, movement unchanged

**Pass criteria:** All three species visible with correct glyphs; pytest green.