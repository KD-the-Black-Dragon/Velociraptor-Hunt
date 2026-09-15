# Manual testing checklist — PR2 (D2+D3+D4)

**How to run:** `python -m src.main`

## Happy path

- [ ] Floor 1 (often ≤15 NPCs): AI feels fully responsive; no half-speed weirdness near you
- [ ] Near-player corner chase still works (wolf loses LOS around a corner → pursues last-known)
- [ ] Busy / deep floor with many NPCs: turns stay snappy
- [ ] Far-off map activity still happens over time (distant NPCs not frozen — half speed only when busy)

## Distant throttle (when floor is crowded)

- [ ] Approach a distant area you left behind: NPCs are not permanently frozen
- [ ] Fighting in your immediate area still uses full-speed AI

## Save/load

- [ ] Save and load; stagger (`ai_turn_salt`) continues without errors

## Regression

- [ ] Door spite / closed door wolf behavior near you still OK
- [ ] Allies follow / rescue near you still OK
- [ ] PR1 feel preserved (no multi-second freezes)

## Out of scope this PR

- Simplified far explore (D1) — not shipped
- Stand-still beyond R (D5) — not shipped
