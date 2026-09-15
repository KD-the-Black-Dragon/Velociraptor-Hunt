# Manual checklist — PR1 Range2

Run: `python -m src.main`

## Range2 wolf

- [ ] New game; find a wolf in LOS
- [ ] Stand **2 tiles** away (not adjacent) — wolf shoots; log shows *"The wolf shoots you for N damage."* (N is 1–4 from ranged stats)
- [ ] Stand **adjacent** — wolf **bumps** you; log does **not** say *"shoots"*
- [ ] Stand **3+ tiles** away — wolf closes distance instead of shooting (Range2 only)
- [ ] Weaken a knight to 0 HP (stunned); stay at distance 2 — wolf **moves in**, does not shoot

## Regression

- [ ] Knights/rabbits without Range2 behave as before
- [ ] Vore still triggers when adjacent at low HP