# Manual testing — match-hud-ux PR1–PR3

## How to run

```bash
python -m src.main
```

## Happy path

- [ ] New Game → name → background → starter allies → hub → select a match
- [ ] **Status right of map:** HP, AUT, AP, balance (and card/crowd) appear in the empty space **to the right** of the arena, not only under the map
- [ ] **Bottom is action log:** recent fight messages only under the map (and across the bottom band); meters are not mixed into that log stream
- [ ] Fight an enemy (bump): combat still works; log shows hits/misses
- [ ] Get **swung at** so the reaction UI opens:
  - [ ] **INCOMING** panel appears **low-right** (not buried in the log)
  - [ ] Map remains visible
  - [ ] Status meters remain readable
  - [ ] Action log remains visible (left of / beside the panel)
  - [ ] 1–4 / dodge still resolve the attack
- [ ] Deploy at least one ally; **walk into the ally**:
  - [ ] Message like `{Name} is standing there.`
  - [ ] **No** significant time jump / turn skip from that bump alone
  - [ ] Enemy combat still works after

## Edge cases

- [ ] Green surrender footer still present when relevant
- [ ] Talk (`T`) prompts appear in status area (not as log spam)
- [ ] Abilities (`a` / `?`) still usable
- [ ] Grapple (if triggered) status still readable in status column
- [ ] Recap after win still full-screen readable

## Regression

- [ ] Title / career loop still Gladiavore hub → match
- [ ] Log font still used for non-map text (if enabled)

## Notes for iteration

Reaction panel position/size may need a second pass — note if it clips text, overlaps meters, or feels too far from the map.
