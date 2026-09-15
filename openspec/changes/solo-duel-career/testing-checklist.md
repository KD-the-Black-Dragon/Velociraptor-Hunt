# Manual testing — Solo Duels career

**Designer sign-off:** 2026-08-10 — all manual checks pass.

Run: `python -m src.main`

## Happy path

- [ ] New Game → downtime hub **without** starter ally picks
- [ ] Hub shows **Campaign: Solo Duels**
- [ ] Hub has **no** Hire / Assign team
- [ ] Select next match → only **1v1** titles (e.g. Dire rat duel, not “3 dire rats”)
- [ ] Match has **exactly one** enemy, no allies
- [ ] Win/lose → recap → downtime
- [ ] Gold/renown/round still advance

## Instant Action

- [ ] Ctrl+B → Red → list shows duel cards only (`d1_wolf`, not `r1_wolves`)
- [ ] Multi-id typed by hand rejected if still multi
- [ ] Bout ends → main menu

## Company on ice

- [ ] Hire/roster code still present (no need to play Company)
- [ ] Load Game of a solo career works

## Regression

- [ ] Battle Sport controls still work in 1v1
- [ ] Green vs red still available among solo cards
