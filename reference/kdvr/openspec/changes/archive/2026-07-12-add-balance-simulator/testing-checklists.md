# add-balance-simulator — Combined manual testing

Designer validates balance tooling after each PR and again at final acceptance.

## Automated gate (acceptance)

```bash
python -m pytest tests/ -v -n 4
```

Per `AGENTS.md` full-suite workflow. Change-scoped sim suite:

```bash
python -m pytest tests/test_sim_aggregator.py tests/test_sim_equip.py tests/test_sim_isolation.py tests/test_sim_navigation.py tests/test_sim_runner.py tests/test_sim_scoring.py tests/test_sim_threat.py -v -n 4
```

---

## PR1 — Runner shell, CSV skeleton

See `testing-checklist-pr1.md` (if present) or verify:

- [ ] `python tools/sim_balance.py --difficulty normal --seconds 5 --trajectory-only` completes
- [ ] Compare sheet has `meta.*` rows and `traj.f01.*` / `iso.f01.*` row keys (iso may be zero)

## PR2 — Navigation, runes, descend

See `testing-checklist-pr2.md`.

## PR3 — Survival (rest, consumables, bail, stunned)

See `testing-checklist-pr3.md`.

## PR4 — Visible loot and equip

See `testing-checklist-pr4.md`.

## PR5 — Trajectory scoring and aggregation

See `testing-checklist-pr5.md`.

## PR6 — Isolation pass and iso columns

See `testing-checklist-pr6.md`.

## PR7 — Final acceptance (designer)

See `testing-checklist-pr7.md`.

### Quick reference — pinned seeds

Documented in `openspec/specs/balance-simulator/spec.md`:

| Pin | Use |
|-----|-----|
| **23** | Normal navigation / descent smoke |
| **25** | Easy deep-run smoke |
| **4242** | Easy bail smoke |
| **7**, **2–13** | Avoid for rune tests (`runes_on_map = 0` common) |

### Quick reference — CLI

```text
python tools/sim_balance.py --difficulty normal --seconds 60
python tools/sim_balance.py --label baseline --output balance_compare.csv
python tools/sim_balance.py --label after_tweak --append --output balance_compare.csv
python tools/sim_balance.py --trajectory-only --seconds 30
python tools/sim_balance.py --curve-output baseline_curve.csv --seconds 60 --label curve_run
```