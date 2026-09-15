# Manual testing checklist — PR1 good NPC spawn quota

## Run

```text
python -m src.main
```

## Happy path

- [ ] **New Game** on **Normal**, depth 1: no good allies on floor 1 (stock goods start at 2+)
- [ ] Descend or start so depth ≥ 2: **exactly 2** new goods when you had **0** followers
- [ ] New goods appear roughly **10–15 steps** from stairs/entrance (not adjacent, not map edge far away)
- [ ] Get one good in LOS, descend: new floor has that follower + **1** new good (total 2 goods when possible); new good still in 10–15 band
- [ ] Followed good is stronger (HP/damage) than a newly spawned same-species good on that floor
- [ ] Follow again: same follower keeps getting stronger (stacks)
- [ ] Get two goods in LOS, descend: new floor has followers only — **no** third/fourth new goods
- [ ] Options → difficulty **Easier**, new game at depth with goods: up to **3** goods with 0 followers
- [ ] Hard/Nightmare: still cap **2**

## Edge / regression

- [ ] Floor 1 still has evil population (density works)
- [ ] Water floors still can place sharks (non-good density)
- [ ] Followers still only good + LOS on descent
- [ ] Performance: no hang on floors without goods

## Save / load

- [ ] N/A for spawn formula (no save format change); optional: save on a floor with goods, load, goods still present
