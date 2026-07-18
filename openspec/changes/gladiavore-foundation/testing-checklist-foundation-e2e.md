# End-to-end manual testing — foundation pass

## How to run

```bash
python -m src.main
```

Designer: full black-box pass after foundation stubs (PR1–15). Systems are intentionally thin; note bugs, not missing depth.

## New career flow

- [ ] New Game → name → **background pick** → starter allies → downtime
- [ ] Background changes starting gold/renown as labeled
- [ ] Hub shows Diff, optional BG id, patrons list

## Loop

- [ ] Select match (3 cards); green only on green rounds
- [ ] Fight: AP/balance, reactions, abilities a–e, Talk, Second Wind
- [ ] Injuries appear; heal costs gold in hub
- [ ] Grapple: seize, break/counter, no free pile-on while held
- [ ] Green: G surrender after min time; red refuses G
- [ ] Red digest → career ends → menu; save gone
- [ ] Patrons: objective in match + recap met/miss
- [ ] Crowd favor line on recap; HUD shows crowd number

## Difficulty

- [ ] Options difficulty (if available) or settings difficulty_id affects feel (harder foes / pay)
- [ ] Easier can offer more green rounds

## Regression / product identity

- [ ] Title **Gladiavore**; user data under Gladiavore folder
- [ ] New Game is career, not dungeon crawl
- [ ] Log font for text; map tiles for arena

## Note for later modules

Do not expect polished Wrestling, deep patrons, real crowd force, full shop gear, or KDVR asset purge in this pass.
