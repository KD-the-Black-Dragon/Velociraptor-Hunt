# Manual testing — PR1: depth-jump start

Run: `python -m src.main`

## Secret entry

- [ ] On main menu, **Ctrl+G** opens name entry (not visible in menu list)
- [ ] Normal **New Game** still works unchanged
- [ ] **Escape** on name or depth returns to main menu

## Depth validation

- [ ] Enter **0** → error **"Please input an integer from 1 to 20"**; can correct
- [ ] Enter **21** → same error
- [ ] Enter **10** → run starts on floor 10

## Depth 1

- [ ] Ctrl+G → name → depth **1** → same as New Game (dagger, robes, rocks; floor 1)

## Loadout (e.g. depth 10)

- [ ] Wielded weapon / worn armor look appropriate for pre-floor-10 loot tables
- [ ] Throwables, potions, and wands present in inventory
- [ ] Status corner shows rune piece bonuses from simulated prior floors

## Past runs

- [ ] Complete a depth-jump run (get digested or win) → **does not** appear in **Past Runs**
- [ ] Complete a normal New Game run → still appears in **Past Runs**

## Regression

- [ ] Load Game, Options, tutorial onboarding (if reset), save/load mid-run