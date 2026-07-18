# Manual testing checklist — PR7 (injuries / recovery / JSON combat)

## How to run

```bash
python -m src.main
```

## Injuries

- [ ] In a hard fight, take a **big** hit → log shows only e.g. `Injured Arm: Minor` (no gore)
- [ ] Status shows injury labels under meters
- [ ] Injury persists after match into downtime header (“You: …”)
- [ ] Allies can also pick up injuries; shown under Assign team

## Healing hub

- [ ] **Healing (injuries)** lists PC/ally injuries with gold costs
- [ ] Enter pays **one step** (Major→Moderate→Minor→clear)
- [ ] Too little gold refuses

## Recovery / 0 HP

- [ ] Reach 0 HP → **DOWN** + recovery bar (not instant game-over if you can still act)
- [ ] Crawl with move keys (slow); `.` rests
- [ ] When bar full, **`a`** stands to **5 HP**
- [ ] **`s` Second Wind** once: HP surge + “shaken” feel
- [ ] With no allies left and PC downed, bout can still end in defeat recap

## JSON balance (spot-check)

- [ ] Optional: tweak `data/match_combat.json` jab `damage_mult` or ability `ap_cost` and relaunch — values should change

## Still OK

- [ ] Log font for non-map text
- [ ] Starter allies + hire + talk still work
