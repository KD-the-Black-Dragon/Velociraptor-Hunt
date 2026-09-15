# Manual checklist — PR6 Player throw (f / F)

Run: `python -m src.main`

## Starter

- [ ] Slot `c` has 5 light-brown `.` rocks

## Quick throw (`f`)

- [ ] `f` with rocks equipped opens target cursor (no pick modal)
- [ ] Confirm on visible evil with clear path: throw resolves, stack decrements
- [ ] Miss line: *"Your throw misses the …"*
- [ ] Good/neutral on cursor: *"Not the best target."* — no turn
- [ ] Empty floor tile: *"There's no target there."* — no turn
- [ ] Good ally in beam path: *"Something is in the way."* — no turn
- [ ] Cyan `*` projectile animates along the beam (in FOV)

## Manual pick (`Shift+f` / `F`)

- [ ] `Shift+f` lists throwables in slot `c`
- [ ] Pick rock → same target cursor as `f`

## Regression

- [ ] Wand (`v`) still smites through allies (no path block)
- [ ] Engulfed: pack keys blocked with engulfed message
- [ ] Melee, quaff, evoke unchanged

Automated: `python -m pytest tests/test_player_throw_pr6.py tests/test_throwables_pr5.py -v`