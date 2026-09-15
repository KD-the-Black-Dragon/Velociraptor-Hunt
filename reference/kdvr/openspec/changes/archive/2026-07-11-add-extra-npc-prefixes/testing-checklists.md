# add-extra-npc-prefixes — Combined manual testing

Run `python -m src.main` from the project root.

## Automated gate (acceptance)

```bash
python -m pytest tests/ -v -n 4
```

Per `AGENTS.md` full-suite workflow. Change-scoped:

```bash
python -m pytest tests/test_npc_prefixes_extra_pr1.py tests/test_npc_prefixes_pr4.py tests/test_npc_prefixes_content_pr2.py -v -n 4
```

---

## PR1 — Prefix infrastructure

See `testing-checklist-pr1.md`.

## PR2 — Stock prefix content

See `testing-checklist-pr2.md`.

## PR3 — Acceptance regression

- [x] All seven prefix names can appear on appropriate evil species (depth 5+ Normal/Hard)
- [x] Sniper never on melee-only species; never on Smite-only slime
- [x] Brute / Bloated Slow cadence; Starving PreferVore at low HP
- [x] Easy: no prefixes; summons: no prefixes
- [x] Save/load preserves prefixed NPCs