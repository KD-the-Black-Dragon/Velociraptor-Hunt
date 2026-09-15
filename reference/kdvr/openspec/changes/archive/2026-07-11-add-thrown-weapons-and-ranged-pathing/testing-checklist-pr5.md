# Manual checklist — PR5 Throwables data + starter rocks

Run: `python -m src.main`

## Starter loadout

- [ ] New game: slot `a` — dagger (wielded)
- [ ] Slot `b` — robes (worn)
- [ ] Slot `c` — **5 rocks** (throwable stack)
- [ ] `i` on slot `c` shows rock damage, accuracy bonus, quantity 5

## Floor spawn (depth 1–3)

- [ ] Rocks can appear on the floor alongside other items
- [ ] Picking up a floor rock stacks into slot `c` if you still carry rocks

## Regression

- [ ] Weapons, armor, potions, wands unchanged
- [ ] Save/load with rock stack in `c` preserves count
- [ ] No throw/fire yet (`f` / `F` land in PR6)

Automated: `python -m pytest tests/test_throwables_pr5.py tests/test_inventory_items_pr3.py::test_new_game_starter_loadout -v`