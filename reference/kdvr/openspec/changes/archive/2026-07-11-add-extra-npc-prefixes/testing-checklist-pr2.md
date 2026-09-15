# Manual testing — PR2 (stock prefix content)

Run: `python -m src.main` — **Normal** or **Hard** difficulty, depth ≥ `prefix_spawn.start_depth` for chosen difficulty.

## Happy path — names visible

Descend until prefix spawns appear (sidebar / examine / combat log names). Confirm each prefix **can** appear on appropriate species:

- [ ] **Elite** `{species}` — tougher than normal same species
- [ ] **Brute** `{species}` — moves on every other player turn (Slow)
- [ ] **Berserk** `{species}` — hits harder, lower max HP than unmarked same species
- [ ] **Veteran** `{species}` — tougher than normal, weaker than Elite on same floor
- [ ] **Bloated** `{species}` — Slow + noticeably higher HP
- [ ] **Starving** `{species}` — any evil species; commits to vore when you are ≤50% HP (PreferVore)
- [ ] **Sniper** `{species}` — only on `RangeN` species (e.g. wolf); **never** on pure melee (e.g. rat, bat without Range)

## Edge cases

- [ ] Melee-only species at depth with prefix rolls: no **Sniper** name ever
- [ ] `SmiteN`-only species (slime): no **Sniper** name

## Regression

- [ ] Easy difficulty: still no prefixes (if stock `prefix_spawn` zeroed)
- [ ] Summons/allies: no prefix names
- [ ] Save mid-floor → reload: prefixed names and behavior persist

## Balance feel (subjective)

- [ ] Prefix variety feels supplemental, not every enemy
- [ ] Starving / Brute / Bloated encourage consumable use without unfair spikes