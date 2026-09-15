# Manual testing checklist — PR3 (AI + combined PR2 playtest)

**How to run:** `python -m src.main`  
**Automated:** `python -m pytest tests/test_ranged_npc_overhaul_pr2.py tests/test_ranged_npc_overhaul_pr3.py -v -n 4`

## Automated (agent)

- [x] PR2 + PR3 tests — run by agent

## Happy path — shots / reload

- [ ] Evil Path/Smite (fox, gnoll, owl, dragon): fire up to magazine size, then take a silent reload turn before firing again
- [ ] At 1 shot while fighting you: they shoot (go to 0) rather than reloading to full
- [ ] When magazine empty and not adjacent: they reload instead of standing forever mute
- [ ] Nightmare: evil shooters get **3** max shots; good allies still **2**

## Happy path — good allies

- [ ] Ram crossbow / sheep cleric: weaker bolts/smite than pre-PR1
- [ ] Ally with 1 shot and **no evil in sight** (following you): prefers reloading back to 2
- [ ] Ally fighting visible evils: will spend shots; won’t idle-top-up mid-fight

## Happy path — evil hunger

- [ ] Weaken yourself (≤50% HP) in sight of a fox/owl/gnoll/dragon at range: sometimes they **walk toward you** instead of shooting (PreferVore always; others by roll)
- [ ] When they commit to hunger, that turn has **no** Path/Smite
- [ ] Fox/owl **NoChase**: still close while they can see you; after breaking LOS they stop pursuing (unchanged)

## Centaur-like melee

- [ ] Close to adjacent: shooters stop Path/Smite; melee feels much safer than their ranged poke

## Save / load

- [ ] Save after a shooter has fired; Load → magazine state preserved
- [ ] Old autosave without magazine field: shooters soft-fill to full (no crash)

## Regression

- [ ] Melee predators / vore modal / digestion unchanged in feel
- [ ] Good Smite still doesn’t smite the player
- [ ] Difficulty Options still cycle; new games use selected difficulty’s shot caps

## Full list pointer

See also `testing-checklist-pr1.md` / `testing-checklist-pr2.md` for earlier slices.
