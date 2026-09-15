# Manual testing — PR8 swallow / belly / digest

How to run: `python -m src.main`

## Happy path

- [ ] If the raptor is adjacent after a turn, it takes you (one melee, hunt lost)
- [ ] Swallow text matches **front / side / behind** (try facing it vs looking away)
- [ ] Enter or Esc on swallow goes to the **belly**: `@` boxed by eight red `#`, world gone
- [ ] Wait or move in the belly does nothing useful; after several turns, **digest** text
- [ ] Digest is dismissed only with **Enter or Esc** (not a random letter)
- [ ] Tranq **You win!** results: only Enter/Esc return to the menu (not any key)
- [ ] Time-over screen: same, only Enter/Esc

## Edges

- [ ] F / R / S in the belly do not shoot or change gait
- [ ] Esc in the belly does not dump you to the menu
- [ ] You cannot walk through the raptor before the pounce

## Pointer

`openspec/changes/velociraptor-hunt/tasks.md` (PR8).
