# Manual testing checklist — PR5 (space tactics + reaction)

## How to run

```bash
python -m src.main
```

## Happy path

- [ ] Enter a match (preferably multi-enemy: rats/kobolds)
- [ ] When an enemy attacks you, **INCOMING!** appears in log font (not only map tiles)
- [ ] Options: **1 Dodge / 2 Parry / 3 Counter / 4 Ignore**
- [ ] **1** then direction: dodge into open tile works; blocked direction refused
- [ ] Repeated dodges cost more fatigue (HP)
- [ ] **2** Parry: attack more likely to glance (lower damage/hit)
- [ ] **3** Counter: may counter jab if still adjacent
- [ ] **4** Ignore: normal hit resolution
- [ ] Successful hits can **shove** 1–2 tiles; into **wall** deals impact damage
- [ ] With multiple foes on you, log may note **flank** / **crowded angle**
- [ ] Map still tiles; HUD/log still log font

## Not in this PR

- ZoC, spear reach, throwables, full grapple
