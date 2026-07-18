# Manual testing checklist — PR2 (Career shell + downtime hub)

## How to run

```bash
pip install -e ".[dev]"
python -m src.main
```

## Happy path

- [ ] **New Game** → enter a name → land on **DOWNTIME** screen (not a dungeon floor)
- [ ] Header shows name, **Round 1**, **Gold** (starting 100), **Renown** (0)
- [ ] Intro line about downtime before next match
- [ ] Menu lists: Shop, Hire, Manage equipment, Training/healing, Assign team, Select next match, Return to main menu
- [ ] Enter each stub option → notice text → Enter/Esc returns to hub root
- [ ] **Select next match** → three cards; at least one **RED** and one **GREEN** labeled
- [ ] Enter on a card → stub notice that arena combat is not implemented yet
- [ ] Esc or **Return to main menu** → quit confirm (Y/n) → capital **Y** returns to main menu
- [ ] After leaving once, main menu shows **Load Game**
- [ ] **Load Game** returns to DOWNTIME with same name/gold

## Edge / regression

- [ ] First launch still works (onboarding if fresh Gladiavore settings)
- [ ] Credits / Options still reachable from main menu
- [ ] **Ctrl+G** depth-jump (if you use it) still reaches **dungeon** PLAY — legacy tool, expected
- [ ] **Ctrl+B** arena still works if you use it — legacy tool, expected
- [ ] Window title still **Gladiavore** (PR1)

## Not in this PR (do not fail PR2)

- Actual arena fight, AUT, shop purchases, real hiring, equipment stats
