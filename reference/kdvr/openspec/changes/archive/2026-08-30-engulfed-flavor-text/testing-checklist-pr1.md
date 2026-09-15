# Manual testing checklist — PR1 (engulfed_flavor data)

**How to run:** `python -m src.main`  
**Automated:** `python -m pytest tests/test_engulfed_flavor_pr1.py tests/test_npc_data_pr3.py tests/test_offscreen_vore_data.py -v -n 4`

## Automated (agent)

- [x] Loader / index tests — run by agent

## Happy path

- [ ] Game starts with stock `entities.json` (no `engulfed_flavor` on species) — no load errors
- [ ] (Optional) Local mod with `engulfed_flavor` on a species loads without error (runtime emit is PR2)

## Regression

- [ ] New Game / entities still load; mods with entities still work

## Out of scope this PR

- Periodic log emit while engulfed (PR2)
