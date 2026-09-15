# Vore Mechanics — Manual Testing Checklist

Run `python -m src.main` from the project root.

---

## Eligibility and AI

- [ ] At full HP, adjacent wolves chase/bump only — no vore modal
- [ ] At ≤50% HP, wolves sometimes open vore modal when adjacent (not every turn)
- [ ] Press **S** to stun (0 HP); wolf adjacent → vore modal always opens on wolf turn
- [ ] Wolf not adjacent at 0 HP → wolf chases toward player

## Modal UI

- [ ] Modal is center-screen; only current phase visible
- [ ] **Enter** advances one phase at a time (attempt then success on hit)
- [ ] Movement keys blocked while modal active
- [ ] On miss (after last attempt phase + Enter): log shows *"You evaded the wolf's vore attempt."*
- [ ] Modal text never appears in scrolling log
- [ ] **Escape** still quits the game

## Engulfed state

- [ ] After success phases, player is engulfed — HUD shows `** ENGULFED **`
- [ ] Map is blind: only `@` visible plus dark-red `#` ring on eight adjacent tiles
- [ ] **F2** sets all wolves to 1 HP (debug)
- [ ] Direction key while engulfed (HP > 0): struggle message, predator loses HP, turn passes
- [ ] Direction key while engulfed at 0 HP: *"You're too tired to move."* — no struggle damage
- [ ] **Wait** (`H` / numpad 5 / `.`) passes turn without struggle
- [ ] Inventory keys blocked while engulfed
- [ ] Third wolf bumps predator tile, not engulfed player

## Escape and mercy

- [ ] Successful escape or 1 HP predator defeat → *"You escape from the wolf."*
- [ ] Same monster phase after escape: no immediate re-vore or bump damage (mercy)
- [ ] Next player turn: wolves can target player again
- [ ] Escape at 0 HP leaves stunned until regen/potion

## Regression

- [ ] **R** new game resets state
- [ ] Core movement, FOV, potions, stunned recovery still work
- [ ] `python -m pytest tests/ -v` — all pass

**Pass criteria:** All checked items behave per `openspec/specs/vore/spec.md`.