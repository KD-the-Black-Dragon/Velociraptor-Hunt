# Manual testing checklist — PR4 (AP / balance / abilities)

## How to run

```bash
python -m src.main
```

## Happy path

- [ ] New Game → downtime → **Select next match** → enter fight
- [ ] Status shows **AP meter** and **Bal meter** under HP/AUT
- [ ] **`.`** wait: balance drifts defensive (more negative over repeated waits)
- [ ] Bump attacks: balance drifts aggressive; log may say **jab** / **attack** / **all-out** depending on foe state
- [ ] **`a`** → ability prompt; **`?`** or **`/`** → full ability list; Esc closes
- [ ] **`a` then `a`**: Haymaker (needs adjacent foe + AP) — costly AP, long AUT, big balance swing
- [ ] **`a` then `b`**: Shield Push — may shove enemy one tile
- [ ] **`a` then `c`**: Hook Shield
- [ ] Low AP: ability refuses with message; AP refills over time (wait / act / fight)
- [ ] Win still returns to downtime with gold

## Edge

- [ ] Ability with no adjacent enemy: refunded / no crash
- [ ] Esc from ability letter mode cancels cleanly
- [ ] Map still tile font; meters readable in status strip

## Not in this PR

- Reaction modal, flanking math polish, full recovery bank, allies, real knockback walls/hazards depth
