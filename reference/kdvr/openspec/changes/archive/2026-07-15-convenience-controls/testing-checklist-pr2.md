# Manual checklist — PR2 (force-attack)

**Run:** `python -m src.main`

## Happy path

- [ ] Stand adjacent to evil; **Ctrl+direction** toward it — attack resolves, player **does not move**.
- [ ] **Ctrl+direction** into empty floor — *You attack the empty air.* and turn passes.
- [ ] Useful against **erratic** wolf: deliberate miss turn without stepping into swap/range danger.

## Edge cases

- [ ] **Ctrl+direction** toward good knight — no swap; empty air (or no ally movement).
- [ ] **Ctrl+direction** toward closed door — door stays closed; empty air.
- [ ] Stunned: **Ctrl+direction** — tired message, turn consumed, no damage.
- [ ] Engulfed: **Ctrl+direction** — struggle behavior (same as normal direction), not empty air.
- [ ] Pending close-door (`c` then direction): Ctrl+direction clears pending and force-attacks.

## Regression

- [ ] Normal bump combat and movement unchanged.
- [ ] F1 / `?` help documents Ctrl+direction force-attack.