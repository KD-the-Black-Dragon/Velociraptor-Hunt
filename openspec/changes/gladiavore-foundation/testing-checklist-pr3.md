# Manual testing checklist — PR3 (Match + AUT)

## How to run

```bash
python -m src.main
```

## Happy path

- [ ] New Game → name → **DOWNTIME**
- [ ] **Select next match** → pick a **RED** or **GREEN** card → Enter
- [ ] Enter **MATCH**: ~20×20 sand pit map (tiles), `@` on west, enemies on east
- [ ] Status shows HP, AUT clock, match title / RED|GREEN
- [ ] **Arrow keys** move; bump enemy to attack
- [ ] **`.`** or **numpad 5** waits (brace)
- [ ] Enemies move/attack on their own AUT (not always alternating 1:1 with you)
- [ ] Defeating all enemies → **Victory** recap with gold/renown → Enter → **DOWNTIME**
- [ ] Gold and renown increased; **round** advanced

## Loss / edge

- [ ] (Optional) Let enemies reduce you to 0 HP → **Defeat** recap
  - Green: appearance-fee style note
  - Red: stub “haul out alive” (digest later)
- [ ] Enter from recap returns to downtime; career still loadable
- [ ] **Ctrl+Q** in match → quit confirm → **Y** abandons match back to hub (no forced settlement)

## Still OK from earlier PRs

- [ ] Downtime uses proportional log font
- [ ] Hub selection preserved when backing out of stubs
- [ ] Product title **Gladiavore**

## Not in this PR (do not fail)

- Full grapple/vore, AP/balance meters, smart jab vs haymaker, reaction modal, allies in arena, shop
