# Testing checklists — balance-pass (final)

Consolidated manual focus for the accepted stock balance baseline.

## How to run

```bash
python -m src.main
```

Options → Difficulty: **Easier ► Normal ► Hard ► Nightmare** (default Normal).

## Happy path (Normal)

- [ ] F1: rats only; cautious melee works
- [ ] F2: bats appear (erratic, weak)
- [ ] F3+: wolves / knights; items start to matter
- [ ] Armor + evade runes change hit rates smoothly (continuous EV)
- [ ] Two evasion runes complete → **+0.5 Ev** (not +1)
- [ ] Far packs on new floors do not all rush at once (spawn freeze)
- [ ] Walking near / damaging a frozen NPC wakes them
- [ ] Deep game still dangerous; dragon is intentional doom if engaged

## Difficulty labels

- [ ] Options shows **Easier**, not Easy
- [ ] Hard feels a step above Normal, not Nightmare-level

## Arena (optional)

```bash
python -m src.main
# Ctrl+B secret arena — peer species at spawn depth
```

## Save / load

- [ ] Mid-run save with armor + partial evade pieces reloads correctly
- [ ] Legacy settings `difficulty_id: "easy"` maps to **easier**

## Pointers

- Per-PR notes: `testing-checklist-pr-evade.md`, `testing-checklist-pr-curve-1.md`
- Design log: `design.md` iteration log + Resolved decisions
