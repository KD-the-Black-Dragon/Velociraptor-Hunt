# Manual checklist — Digestion PR 1

Run: `python -m src.main`

## Foundation (this PR)

- [ ] Wolf has digestion damage data (no visible UI yet; behavior in PR 2)
- [ ] Wolf holding prey **does not move** on its turn
- [ ] Wolf holding prey **can bump-attack** an adjacent knight (or player if adjacent)
- [ ] Wolf holding prey **does not** attempt vore on a second adjacent prey
- [ ] Defeat a wolf holding an NPC — freed prey gets mercy; same wolf (or another) **cannot** re-engulf that prey for the rest of the world phase
- [ ] Freed prey is not damaged by bump attacks while mercy is active

## Regression

- [ ] Player vore modal, struggle, escape, and player mercy unchanged
- [ ] NPC rescue log when predator defeated (visible tiles only)
- [ ] Engulfed prey hidden from AI targeting; predator glyph on dark red tile
- [ ] F2 weaken, FOV, faction AI, stunned good/neutral at 0 HP