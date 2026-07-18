# Manual testing checklist — PR10 (thin patrons)

## How to run

```bash
python -m src.main
```

## Hub

- [ ] Downtime header lists **three patrons** (Lady Vex, Patron Halm, Gold-Finger Rusk)
- [ ] Match select mentions a patron will offer an objective at match start
- [ ] After a match, hub shows last patron result line (met or missed)

## In match

- [ ] Match start log includes **Patron: … (+Ng)**
- [ ] HUD shows the active objective line under the match title
- [ ] Objective makes sense for the card (no “win green” on pure red, no ally-only goal with no allies)

## Settlement

- [ ] **Win** while meeting the objective → recap “objective met” + extra gold
- [ ] **Lose / surrender / fail** the condition → recap “objective missed (no bonus)” — gold not reduced for missing
- [ ] Purse total includes patron bonus only on hit

## Still OK (regression)

- [ ] Green surrender (`G`), card offers, grapple isolation still work
- [ ] Career save/load keeps last patron result after returning to hub
- [ ] Digest career end still works; patron line may note miss

## Optional JSON

- [ ] Edit `data/patrons.json` bonus_gold or labels; relaunch — text/amounts change
