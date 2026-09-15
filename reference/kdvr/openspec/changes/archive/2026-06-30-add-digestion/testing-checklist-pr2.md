# Manual checklist — Digestion PR 2

Run: `python -m src.main`

Tip: F2 weakens all monsters to 1 HP for faster vore/digestion setup.

## NPC digestion (this PR)

- [ ] Wolf engulfs stunned knight (F2 → fight until knight at 0 HP → let wolf vore)
- [ ] While engulfed, knight loses HP each world phase (3 per tick) until 0
- [ ] At 0 HP, knight accumulates strikes over subsequent world phases (no HP loss + strike same tick)
- [ ] After 3 strikes, knight is **removed**; log shows completion line matching vore type (OV burp / CV slime / AV compression)
- [ ] Freed wolf acts normally on the **next** player turn (not an extra full turn the same phase digest completes)
- [ ] Good knight: occasional plea lines (~10%) when you have LOS to wolf or prey tile
- [ ] Neutral rabbit engulfed: **silent** digestion ticks (no plea spam)
- [ ] Engulfed prey with 1+ strikes does **not** natural-regen; potions still heal

## Regression (PR 1 + earlier)

- [ ] Holding wolf attack-only; no move; no second vore
- [ ] NPC mercy on rescue; no re-engulf same phase
- [ ] Player vore/struggle unchanged (no player digestion yet — PR 3)
- [ ] FOV-gated combat/vore/digestion logs