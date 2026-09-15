# add-npc-data-driven — Combined manual testing

Run `python -m src.main` from the project root.

## Automated gate (acceptance)

```bash
python -m pytest tests/ -v
```

All tests should pass.

---

## PR 1 — Data loaders

- [ ] `data/entities.json` has wolf, knight, rabbit, shark
- [ ] Stub item JSON files exist
- [ ] Main menu → new game plays without crash

## PR 2 — Combat + spawn

- [ ] Bump wolf — ~1/3 misses; variable damage when hit
- [ ] Population: 6 wolves, 5 knights, 6 rabbits on land
- [ ] Miss message: **"You miss …"**
- [ ] F2 debug still weakens monsters

## PR 3 — Vore from data

- [ ] Wolf vore modal text from JSON
- [ ] Shark vore text distinct (on water floors)
- [ ] Knights/rabbits never open vore modals
- [ ] `src/vore_content.py` gone

## PR 4 — Terrain, depth, followers

- [ ] No sharks on dry floors; 2 sharks in water on wet floors
- [ ] Descend with knight follower → 4 fresh knights (not 5)
- [ ] Hidden knight does not follow
- [ ] Shore shark combat still works

## Full regression

- [ ] Main menu, name entry, options, Ctrl+Q quit
- [ ] Examine, descent, depth HUD, potions
- [ ] Player vore modal, struggle, digestion, game over → menu
- [ ] NPC swap, stunned allies, rescue, log visibility gating

**Pass criteria:** Behavior matches `openspec/specs/npc-data/spec.md`; pytest green.