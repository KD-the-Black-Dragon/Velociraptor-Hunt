# Manual checklist — PR1 (autoexplore)

**Run:** `python -m src.main`

## Happy path

- [ ] On a mostly-cleared floor with known items/runes on **explored** tiles out of current sight, press `` ` `` — player paths to them and picks up / activates runes.
- [ ] With no pickups left, autoexplore reveals unseen map areas (frontier) until dead ends.
- [ ] When nothing left to pick up and no reachable unseen area, log shows *Exploration complete.*
- [ ] Start message *You begin exploring.* appears once per session.

## Start blocked

- [ ] Evil already visible when pressing `` ` `` → *There's an enemy in sight!* (no session).
- [ ] Below 50% HP → *You are too injured to autoexplore.*
- [ ] At exactly 50% HP (e.g. 5/10) → autoexplore **allowed**.
- [ ] Engulfed → *You're already exploring something's digestive tract.*
- [ ] Stunned → tired-to-move message.

## Interrupts (mid-run; rest parity)

- [ ] Evil walks into player FOV during autoexplore → *Danger approaches!*
- [ ] Player is targeted (hit or miss) → *It's hard to rest while under attack!*
- [ ] Good ally in view sees evil → ally alarm line; exploration stops.

## Cancel

- [ ] Any key during autoexplore cancels **silently** (no complete/interrupt line).
- [ ] Inventory modal / examine / vore modal: `` ` `` does not start exploration.

## Regression

- [ ] Long rest (`5`) still works; interrupts unchanged after refactor.
- [ ] Normal movement, pickup-on-step, rune activation unchanged.
- [ ] F1 / `?` help lists `` ` `` autoexplore.

## Performance

- [ ] Autoexplore on a large floor feels responsive (batched turns; map updates when FOV/pickups change).