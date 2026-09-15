# PR 3 — Manual checklist: Vore narratives from data

Run `python -m src.main` from the project root.

## Automated gate (PR 3 only — not full suite)

```bash
python -m pytest tests/test_npc_data_pr3.py -v
python -m pytest tests/test_vore_constants.py tests/test_vore_modal.py tests/test_vore_ai.py -v
```

## Vore modal text (wolf)

- [ ] Stun yourself near a wolf (or let it reduce you to 0 HP) — vore attempt modal opens
- [ ] Attempt text matches `data/entities.json` wolf `vore_narratives` (not old hardcoded-only lines)
- [ ] On hit, success phases advance with Enter; text stays modal-only (not in log)
- [ ] On miss, log shows evaded message after dismissing modal

## Shark (when floor has water)

- [ ] Find a shark in deep water — vore attempt uses shark-specific text (mentions shark / depths, not wolf copy)

## Non-vore species

- [ ] Knights and rabbits never open vore modals

## Data / code

- [ ] `src/vore_content.py` is gone
- [ ] Evil species get `VoreCapable` + digestion from alignment profile, not `abilities` in JSON

## Regression

- [ ] Combat miss message reads **"You miss the wolf."** (not "misses")
- [ ] Digestion modals still work after engulf + digest
- [ ] Options menu vore type toggles still filter initiation types