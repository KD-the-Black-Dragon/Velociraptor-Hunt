# Manual checklist — PR0 (debug stdout env gate)

Run: `python -m src.main`

## Default play (no env)

- [ ] Start a new game; play several turns including combat and movement.
- [ ] PowerShell / terminal shows **no** `[prefetch]`, `[map_gen]`, `[floor_init]`, snarl, or swap-attempt lines during normal play.
- [ ] Message log still shows normal in-game messages as before.

## Optional dev mode

- [ ] Set `DEBUG_STDOUT=1` in the shell, then run `python -m src.main`.
- [ ] On new game / floor load, prefetch or map_gen lines **may** appear in the terminal (expected).
- [ ] In-game message log is unchanged; debug text stays in the terminal only.

## Regression

- [ ] Evil frustration and good-follow debug lines do **not** appear in the message log (unchanged).