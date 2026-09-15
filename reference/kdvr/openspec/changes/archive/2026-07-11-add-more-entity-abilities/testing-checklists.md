# add-more-entity-abilities — Combined manual testing

Run `python -m src.main` from the project root.

## Automated gate (acceptance)

```bash
python -m pytest tests/ -v -n 4
```

Per `AGENTS.md` full-suite workflow.

---

## PR1 — PreferVore

See `testing-checklist-pr1.md`.

## PR2 — Wander

See `testing-checklist-pr2.md`.

## PR2b — NoChase

See `testing-checklist-pr2b.md`.

## PR3 — Hands

See `testing-checklist-pr3.md`.

## PR4 — Stationary mobility

See `testing-checklist-pr4.md`.

## PR5 — RangedVoreN

See `testing-checklist-pr5.md`.

## PR6 — Species content

See `testing-checklist-pr6.md`.

## PR7 — Acceptance regression

- [ ] New game starts without crash (save snapshot encodes all ability types)
- [ ] Stock species behave per assignments (kobold doors, slime wander, owl dual tongue, tunnel slug turret)
- [ ] Wolf `Range6` ground predator — normal spawn rate