# Manual testing checklist — PR1 (ally damage + shot knobs)

**How to run:** `python -m src.main`  
**Automated:** `python -m pytest tests/test_ranged_npc_overhaul_pr1.py -v -n 4`

## Automated (agent)

- [x] PR1 tests — run by agent

## Happy path

- [ ] Game launches to main menu (stock `depth_scaling.json` still loads)
- [ ] Options → Difficulty still cycles Easier / Normal / Hard / Nightmare
- [ ] **New Game** on Normal — play until you meet a **ram crossbow** or **sheep cleric** ally (or examine spawn later floors): their Path/Smite hits should feel weaker than before (~half). Exact numbers: ram bolts **4–5**, sheep smite **5–6**
- [ ] No crash / load error mentioning `good_ranged_shots` / `evil_ranged_shots`

## Regression

- [ ] Evil shooters (fox archer, gnoll, owl mage, dragon) still fire every turn as before — **shots resource not wired until PR2**
- [ ] Existing difficulties still apply (Nightmare still feels harder overall)
- [ ] Save/load a short run still works (no new runtime state yet)

## Out of scope this PR

- Magazine / reload / AI hunger (PR2–PR3)
- Live spec archive (PR4)
