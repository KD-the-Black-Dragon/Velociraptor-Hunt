# Manual testing checklist — PR6 (roster / hire / talk)

## How to run

```bash
python -m src.main
```

## Happy path

- [ ] **New Game** → name → **FREE STARTER ALLIES** market (cannot full hub yet)
- [ ] Pick **2 free** allies (different tiers appear); then “Starter team ready”
- [ ] Downtime shows roster counts (e.g. 2/4, deployed 2/2)
- [ ] **Hire personnel** → paid offers; **R** refreshes market; hire spends gold
- [ ] **Assign team** → Enter toggles **[IN]/[--]**; cannot deploy more than 2
- [ ] **Select match** → fight with cyan-ish ally glyphs near you
- [ ] Allies move/attack on their own AUT
- [ ] **`T`** → pick ally (1/2) or **0 all** → **1 Attack** or **2 Defend**
- [ ] First shout is free (no turn); second soon after costs AP and spends turn
- [ ] Defend: allies stay nearer you; Attack: they chase foes
- [ ] Red match: ally reduced to 0 → digest compensation gold + roster shrinks
- [ ] Green match: ally down message says they survive

## Edge

- [ ] Cannot hire past 4 allies
- [ ] Cannot hire without gold
- [ ] Load Game restores roster after quit

## Not in this PR

- Injuries/recovery bank, full grapple, shop gear, training tree
