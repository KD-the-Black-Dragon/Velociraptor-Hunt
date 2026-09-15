# Manual checklist — Digestion PR 3

Run: `python -m src.main`

Tip: F2 → fight wolf until stunned at 0 HP → let wolf vore you (modal → engulf).

## Player digestion (this PR)

- [ ] While engulfed at HP > 0, each turn (move/struggle/wait) reduces HP by 3 until 0
- [ ] At 0 HP, strikes accumulate one per consumed turn (no HP loss + strike same tick)
- [ ] Each strike logs **"You are being digested!!"** (not on HP-only damage ticks)
- [ ] Other wolves cannot damage you while engulfed; no "hits you" combat lines
- [ ] No "You are no longer stunned" from regen while engulfed at 0 HP
- [ ] Third strike opens **center digestion modal** (OV/CV/AV line; not in scroll log)
- [ ] Enter on modal → **game over** screen: `Player`, score (turns survived), `Digested by wolf`
- [ ] Enter on game over → game exits

## Same-turn rule

- [ ] Struggle (direction key) then digestion on **one** turn when at 0 HP (strike increments after struggle)

## Regression

- [ ] Escape and mercy still work before third strike
- [ ] NPC digestion (PR 2) unchanged
- [ ] Vore attempt/success modal unchanged
- [ ] Log hyphens render correctly (CP437 safe)