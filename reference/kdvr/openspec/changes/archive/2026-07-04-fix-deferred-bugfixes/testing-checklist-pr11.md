# Manual checklist — PR11 (good–neutral corridor swap)

Run: `python -m src.main`

## Corridor follow

- [ ] Recruit or spawn a **good knight** ally; find a **neutral rabbit** in a **1-wide corridor** between the knight and the player.
- [ ] Walk the player away down the corridor; the knight should **swap through** the rabbit and continue following — not stall behind it indefinitely.
- [ ] Knight ends up **past** the rabbit (closer to the player than the rabbit's original tile).

## Swap behavior

- [ ] Knight stepping into rabbit still **swaps** (no attack log, no damage).
- [ ] **Two knights** following the player do **not** freeze swapping with each other — rear knight waits for front to advance, then continues.
- [ ] **Neutral rabbit does not** initiate swap into the knight when exploring.
- [ ] **Evil wolf** still **attacks** neutral rabbit on bump (no good–neutral swap rule for evil).

## Regression

- [ ] Good knight still **does not** step onto the player tile (console-only swap attempt unchanged).
- [ ] Player swap with good/neutral NPCs unchanged.
- [ ] PR9 pursuit momentum and PR10 neutral explore intact.
- [ ] PR0–PR10 behavior intact.