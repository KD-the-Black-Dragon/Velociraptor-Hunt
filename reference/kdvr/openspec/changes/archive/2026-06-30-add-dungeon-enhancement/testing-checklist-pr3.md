# Manual checklist — PR 3: Floor depth and descent

Run after `python main.py`. Sign off before PR 4.

## Depth and HUD

- [ ] New game shows **Depth 1** on the HUD status line
- [ ] After descending, depth increments (Depth 2, 3, …)

## Descend key (`Shift+.` / `>`)

- [ ] **`.`** (unshifted) still **waits** / passes a turn
- [ ] **Shift+`.`** while **not** on `>` — message *"There are no stairs here."*, no turn consumed
- [ ] **Shift+`.`** while **engulfed** (any tile) — *"Going deeper won't help you here!"*, no turn consumed
- [ ] Stand on `>`, press **Shift+`.`** — new floor loads, depth increases, player at entrance

## State preservation

- [ ] HP and inventory unchanged after descent
- [ ] Player name and options prefs unchanged

## Good allies

- [ ] Knight in line of sight follows to the new floor (near entrance)
- [ ] Knight out of sight does **not** follow
- [ ] Total knights on new floor still matches expected population (no duplicates)

## Debug

- [ ] **R** still full-regenerates dungeon and resets depth to **1**