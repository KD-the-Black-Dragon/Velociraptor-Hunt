# Manual testing checklist — PR2 (magazine / spend / reload / save)

**How to run:** `python -m src.main`  
**Automated:** `python -m pytest tests/test_ranged_npc_overhaul_pr2.py -v -n 4`

> Designer note: PR2+PR3 were implemented together; prefer the combined PR3 checklist for playtest.

## Automated (agent)

- [x] PR2 tests — run by agent

## Happy path

- [ ] New Game → encounter fox archer / gnoll / owl mage / dragon: they fire, then pause (reload) instead of infinite shots
- [ ] Nightmare evil shooters feel like they get one extra shot in the magazine (max 3)
- [ ] Save mid-fight with a shooter that has fired; Load → they keep partial magazine (don’t reset to full unless old save lacked the field)

## Regression

- [ ] Melee-only monsters unchanged
- [ ] Ranged vore (if you meet it) still works without “using up” a Path shot
- [ ] Adjacent to a shooter: they stop Path/Smite (centaur-like)

## Out of scope alone

- Full AI priority / hunger / good top-up — see PR3 checklist
