# Manual checklist — PR7 (rune effects status corner)

Run: `python -m src.main`

## HP rune row

- [ ] Start a new game; status corner shows **Depth 1** only (no bonus rows yet).
- [ ] Step on a **vitality** (green) rune; message log shows `+5 max HP`.
- [ ] Status corner gains a **green** row **`HP +5`** below depth.

## Combat rune rows

- [ ] Step on a **striking** (gold) rune; corner shows **yellow** **`Acc +0.15`** on its own row.
- [ ] Step on a **warding** (blue) rune; corner shows **cyan** **`AC +1`** on its own row.
- [ ] On a deep floor, absorb **ruin** (`accuracy_damage`); corner shows **yellow** **`Acc +0.2`** and **red** **`Dam +1`** on separate rows.

## Stacking and persistence

- [ ] With HP + combat bonuses active, descend stairs; bonus rows **persist** on the new floor.
- [ ] Rows appear **after** depth and any ailment rows (STUN, ENGLF).

## Regression

- [ ] Depth, stun, and engulfed indicators still render correctly.
- [ ] PR0–PR6 behavior intact (log colors, wrap, Ctrl+P, F1/? help).