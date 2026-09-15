# Manual testing — PR10 Training Mode

How to run: `python -m src.main`

## Entry

- [ ] Main menu has **Training Mode** (no name prompt)
- [ ] New Hunt also skips name; it goes to weapon select
- [ ] Training starts immediately (default rifle) on a **fixed** arena: open west, long grass east
- [ ] Esc from training returns to the menu; **Continue Hunt** does not appear from a training session

## F2 menu (training only)

- [ ] **F2** opens dummy + loadout. Live hunt F2 does nothing
- [ ] Walk back and forth: raptor teleports onto the patrol and walks open ↔ grass
- [ ] Stand still in long grass / open: teleport there and idle
- [ ] Stop moving: freeze in place (no teleport)
- [ ] Cancel stop: resume the previous script (no teleport)
- [ ] Seek and chase ASAP: comes for you
- [ ] Gait sneak / walk / run: overlay; script keeps running
- [ ] Normal behavior: live raptor mind
- [ ] Weapon Rifle / Shotgun / Revolver: swaps on the fly, ammo refills
- [ ] Esc closes F2 without leaving training
- [ ] F1 lists F2

## Rules

- [ ] Adjacent **and** in raptor FOV still swallows; behind it is safe
- [ ] Tranq / clock / belly still work
- [ ] A training win or loss does **not** change Stats

## Pointer

`openspec/changes/hunt-deferred/tasks.md` (PR10).
