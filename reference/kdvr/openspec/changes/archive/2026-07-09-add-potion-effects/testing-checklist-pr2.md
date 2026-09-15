# Manual testing checklist — PR2 (instant / buff potions)

Run: `python -m src.main`

## New potions

**TEMP:** New games start with discovery / haste / might / antacid in slots **c–f** (remove in final PR).

| Potion | Expect |
|--------|--------|
| **potion of discovery** | Floor layout fully explored (dim map); FOV unchanged |
| **potion of haste** | Status `Fast N`; extra actions before monsters; rest feels faster |
| **potion of might** | Status `Might N`; hits harder for a while |
| **potion of antacid** | Status `Antacid N`; while engulfed, no dig damage / no strikes |

## Happy path

- [ ] Quaff discovery — map memory fills; not fully lit unless in FOV
- [ ] Quaff haste — status row; can act twice before monsters for a while
- [ ] Quaff might — combat feels stronger; expires after turns
- [ ] Quaff antacid then get engulfed — gut does not chip HP or advance digestion strikes until ward ends
- [ ] Heal potions still work

## Regression

- [ ] Save/load mid-buff preserves Fast/Might/Antacid
- [ ] Inventory inspect shows examine (heal still shows HP amount)
- [ ] Floor gen stable with more potion types in pool

## Automated

- [x] `tests/test_potion_effects_pr2.py`
