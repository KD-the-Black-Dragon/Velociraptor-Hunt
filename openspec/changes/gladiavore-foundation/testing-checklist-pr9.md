# Manual testing checklist — PR9 (match cards / economy / surrender)

## How to run

```bash
python -m src.main
```

## Match card offers

- [ ] Downtime → **Select next match** shows **up to 3** cards (not a fixed forever list)
- [ ] Round **1** can show a **GREEN** option among reds
- [ ] After winning a round, next offer set can change (new round index)
- [ ] On a non-green round (e.g. round **2**), offers should be **all RED**
- [ ] Cards with different titles/opponents appear (rats, kobolds, wolves, etc.)

## Spawns & payouts

- [ ] Enter a multi-enemy card → correct-ish count of foes in the pit
- [ ] **Win** a red match → gold scales with payout mult; renown +2-ish; round advances
- [ ] **Win** a green match → **less gold** than a similar red win; renown lower
- [ ] **Lose** green → appearance fee; no career end
- [ ] **Lose** red (team incap, not digest) → small gold; return to hub

## Green surrender (`G`)

- [ ] Green match footer shows **G: surrender**
- [ ] Press **G** immediately → denied (“too early”)
- [ ] Fight a few beats (wait/move), then **G** → **Surrender** recap, scaled gold, round advances, back to hub
- [ ] Red match **G** → refused (no surrender)

## Still OK (regression)

- [ ] Grapple scene isolation (PR8) still holds on multi-enemy red
- [ ] Digest still ends career; normal loss does not
- [ ] Starter allies, hire, talk, injuries still work
- [ ] Log font for HUD/log; map tiles for arena

## Optional JSON tune

- [ ] Edit `data/match_cards.json` economy or add a card; relaunch — offers/payouts change
