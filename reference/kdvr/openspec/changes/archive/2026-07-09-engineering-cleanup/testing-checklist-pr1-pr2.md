# Manual testing — engineering-cleanup PR1 + PR2

**Run:** `python -m src.main`

PR2 is test/CI only (no gameplay). Focus playtest on **PR1 save soft-drop** and **spawn weight 0** if you touch data.

## Happy path

- [ ] New game starts and plays normally
- [ ] Save (auto or quit-save) and **Load Game** restores the run
- [ ] Message log / UI still behave as before (no new soft-drop notice on a normal save)

## Soft-drop (if easy to force)

- [ ] Optional: edit a save (or use a crafted fixture) so inventory has an unknown `item_id` → load succeeds; item gone; caution-style notice appears once
- [ ] Optional: unknown floor item / NPC species stripped without crash

## Spawn weight 0

- [ ] No need to playtest unless editing JSON: weight `0` means “defined but never spawns” (automated tests cover load)

## Regression

- [ ] Come here / inventory / vore still feel normal (unrelated systems)
- [ ] No obvious lag or crash on load

## Automated

- Full suite: `python -m pytest tests/ -n 6` → **1253 passed, 2 skipped** (perf p95 skipped by design)
